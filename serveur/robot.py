"""Pilotage du bras : traduit les demandes de l'interface en commandes série."""

import asyncio
import json
import time
from pathlib import Path

from config import ANGLE_MAX, ANGLE_MIN, MARGE_TIMEOUT, NB_AXES, PAS_PAR_DEGRE
from liaison import LiaisonSerie, Simulateur
from mouvement import plan_avec_duree, plan_synchronise

FICHIER_ETAT = Path(__file__).resolve().parent.parent / "derniere_position.json"


class ErreurCommande(Exception):
    pass


class Robot:
    def __init__(self, notifier):
        self.notifier = notifier  # callback(dict) vers les navigateurs
        self.liaison = None
        self.connexion_en_cours = False
        self.q_cible = [0.0] * NB_AXES
        self.plan = None
        self.t0 = 0.0
        self.q_repos = [0.0] * NB_AXES
        self.pince = 0.0
        self.occupe = False
        self.calibre = False
        self.firmware_q = False  # le firmware sait-il répondre à « Q » ?
        self._ready = asyncio.Event()
        self._pos_recue = None
        self.lecture = None  # tâche de lecture de trajectoire
        self.lecture_info = None
        self.journal = []
        self.derniere_connue = self._charger_derniere_position()

    # ---------- état ----------

    def q_estime(self):
        if self.plan is None:
            return list(self.q_repos)
        t = time.monotonic() - self.t0
        if t >= self.plan.duree:
            return list(self.plan.q_fin)
        return self.plan.position(t)

    def etat(self):
        return {
            "type": "etat",
            "connecte": self.liaison is not None,
            "connexion_en_cours": self.connexion_en_cours,
            "simulateur": bool(self.liaison and self.liaison.simulee),
            "port": self.liaison.port if self.liaison else None,
            "q": [round(a, 3) for a in self.q_estime()],
            "q_cible": [round(a, 3) for a in self.q_cible],
            "pince": self.pince,
            "occupe": self.occupe,
            "calibre": self.calibre,
            "firmware_q": self.firmware_q,
            "lecture": self.lecture_info,
            "derniere_connue": self.derniere_connue,
            "limites": {"min": ANGLE_MIN, "max": ANGLE_MAX},
        }

    def _log(self, sens, texte):
        entree = {"type": "journal", "t": time.strftime("%H:%M:%S"), "sens": sens, "texte": texte}
        self.journal = (self.journal + [entree])[-200:]
        self.notifier(entree)

    def _charger_derniere_position(self):
        try:
            q = json.loads(FICHIER_ETAT.read_text())["q"]
            return [float(a) for a in q][:NB_AXES] if len(q) >= NB_AXES else None
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def _sauver_position(self):
        q = [round(a, 3) for a in self.q_repos]
        self.derniere_connue = q
        try:
            FICHIER_ETAT.write_text(json.dumps({"q": q, "pince": self.pince}))
        except OSError:
            pass

    # ---------- connexion ----------

    async def connecter(self, port):
        if self.liaison or self.connexion_en_cours:
            raise ErreurCommande("Déjà connecté.")
        self.connexion_en_cours = True
        self.notifier(self.etat())
        try:
            liaison = Simulateur(self._recevoir) if port == "simulateur" else LiaisonSerie(port, self._recevoir)
            self._log("info", f"Connexion à {port}…")
            await liaison.ouvrir()
            self.liaison = liaison
            # L'Arduino redémarre à l'ouverture : il croit être en position 0.
            self.q_repos = [0.0] * NB_AXES
            self.q_cible = [0.0] * NB_AXES
            self.plan, self.occupe, self.calibre = None, False, False
            self._ready.clear()
            self._envoyer("R")
            try:
                await asyncio.wait_for(self._ready.wait(), 4.0)
            except asyncio.TimeoutError:
                await self.deconnecter()
                raise ErreurCommande("La carte ne répond pas (READY non reçu). Vérifie le port et le firmware.")
            self.firmware_q = await self._demander_position() is not None
            self._log("info", "Carte prête." + ("" if self.firmware_q else " (firmware sans retour de position)"))
        finally:
            self.connexion_en_cours = False
            self.notifier(self.etat())

    async def deconnecter(self):
        await self.arreter_lecture()
        if self.liaison:
            liaison, self.liaison = self.liaison, None
            await liaison.fermer()
            self._log("info", "Déconnecté.")
        self.plan, self.occupe = None, False
        self.notifier(self.etat())

    def _envoyer(self, ligne):
        if not self.liaison:
            raise ErreurCommande("Pas de carte connectée.")
        self._log("tx", ligne)
        self.liaison.envoyer(ligne)

    def _recevoir(self, ligne):
        if ligne is None:
            self._log("erreur", "Liaison série perdue.")
            asyncio.ensure_future(self.deconnecter())
            return
        self._log("rx", ligne)
        if ligne == "READY":
            if self.plan is not None:
                self.q_repos = list(self.plan.q_fin)
                self.plan = None
                self._sauver_position()
            self.occupe = False
            self._ready.set()
        elif ligne.startswith("POS "):
            try:
                self._pos_recue = [float(v) for v in ligne.split()[1:NB_AXES + 1]]
            except ValueError:
                pass
        elif ligne == "STOPPED":
            self.occupe = False
        self.notifier(self.etat())

    async def _demander_position(self):
        self._pos_recue = None
        self._envoyer("Q")
        for _ in range(15):
            await asyncio.sleep(0.1)
            if self._pos_recue is not None:
                return self._pos_recue
        return None

    # ---------- mouvements ----------

    def _verifier(self, q):
        if len(q) != NB_AXES:
            raise ErreurCommande("Il faut 6 angles.")
        q = [float(a) for a in q]
        for i, a in enumerate(q):
            if not ANGLE_MIN[i] <= a <= ANGLE_MAX[i]:
                raise ErreurCommande(f"Axe {i + 1} : {a:.1f}° hors limites [{ANGLE_MIN[i]} ; {ANGLE_MAX[i]}].")
        return q

    def deplacer(self, q, duree=None):
        """Envoie un mouvement articulaire (en degrés). Ne bloque pas."""
        q = self._verifier(q)
        depart = self.q_estime()
        if duree:
            plan, erreur = plan_avec_duree(depart, q, float(duree))
            if plan is None:
                raise ErreurCommande(erreur)
            ligne = "AT " + " ".join(f"{a:.3f}" for a in q) + f" {float(duree):.3f}"
        else:
            plan = plan_synchronise(depart, q)
            ligne = "A " + " ".join(f"{a:.3f}" for a in q)
        self._ready.clear()
        self._envoyer(ligne)
        self.q_repos = depart
        self.plan, self.t0 = plan, time.monotonic()
        self.q_cible = q
        self.occupe = True
        self.notifier(self.etat())
        return plan.duree

    def regler_pince(self, valeur):
        valeur = max(0.0, min(100.0, float(valeur)))
        self._ready.clear()
        self._envoyer(f"P {valeur:.0f}")
        self.pince = valeur
        self.notifier(self.etat())

    async def arreter(self):
        """Arrêt immédiat (commande S) puis resynchronisation de la position."""
        if self.lecture:
            self.lecture.cancel()
        if not self.liaison:
            return
        self._envoyer("S")
        q = self.q_estime()
        self.plan, self.occupe = None, False
        self.q_repos = q
        if self.firmware_q:
            reel = await self._demander_position()
            if reel:
                self.q_repos = reel
        else:
            self._log("info", "Position estimée après l'arrêt : vérifie-la avant de continuer.")
        self.q_cible = list(self.q_repos)
        self._sauver_position()
        self.notifier(self.etat())

    def definir_position(self, q):
        """Indique à l'Arduino où se trouve le bras (commande F, en pas)."""
        if self.occupe:
            raise ErreurCommande("Attends la fin du mouvement.")
        q = self._verifier(q)
        self._envoyer("F " + " ".join(str(round(q[i] * PAS_PAR_DEGRE[i])) for i in range(NB_AXES)))
        self.q_repos, self.q_cible, self.plan = q, list(q), None
        self.calibre = True
        self._sauver_position()
        self.notifier(self.etat())

    async def attendre_fin(self, duree_estimee):
        try:
            await asyncio.wait_for(self._ready.wait(), duree_estimee + MARGE_TIMEOUT)
        except asyncio.TimeoutError:
            raise ErreurCommande("Pas de READY reçu : mouvement refusé ou carte bloquée.")

    # ---------- trajectoires ----------

    def lancer_lecture(self, points, boucle=False):
        if self.lecture:
            raise ErreurCommande("Une trajectoire est déjà en cours.")
        if not points:
            raise ErreurCommande("Trajectoire vide.")
        for p in points:
            self._verifier(p["q"])
        self.lecture = asyncio.ensure_future(self._lire(points, boucle))

    async def _lire(self, points, boucle):
        try:
            while True:
                for n, p in enumerate(points):
                    self.lecture_info = {"index": n, "total": len(points)}
                    self.notifier(self.etat())
                    if p.get("pince") is not None and float(p["pince"]) != self.pince:
                        self.regler_pince(p["pince"])
                        await self.attendre_fin(1.0)
                    duree = self.deplacer(p["q"], p.get("duree") or None)
                    await self.attendre_fin(duree)
                    if p.get("pause"):
                        await asyncio.sleep(float(p["pause"]))
                if not boucle:
                    break
        except ErreurCommande as e:
            self._log("erreur", f"Trajectoire interrompue : {e}")
        except asyncio.CancelledError:
            self._log("info", "Trajectoire arrêtée.")
        finally:
            self.lecture = None
            self.lecture_info = None
            self.notifier(self.etat())

    async def arreter_lecture(self):
        if self.lecture:
            self.lecture.cancel()
            try:
                await self.lecture
            except asyncio.CancelledError:
                pass
