"""Liaison avec la carte : port série réel ou simulateur."""

import asyncio
import threading
import time

import serial
from serial.tools.list_ports import comports

from config import ANGLE_MAX, ANGLE_MIN, CARTES_USB, NB_AXES, PAS_PAR_DEGRE, VITESSE_SERIE
from mouvement import plan_avec_duree, plan_synchronise


def lister_ports():
    ports = []
    for p in comports():
        nom = CARTES_USB.get((p.vid, p.pid)) if p.vid is not None else None
        ports.append({"port": p.device, "description": nom or p.description or p.device, "arduino": nom is not None})
    ports.sort(key=lambda p: not p["arduino"])
    return ports


class LiaisonSerie:
    """Port série vers l'Arduino Mega. Les lignes reçues sont passées à `recevoir`."""

    simulee = False

    def __init__(self, port, recevoir):
        self.port = port
        self.recevoir = recevoir
        self.serie = None
        self._fil = None
        self._actif = False

    async def ouvrir(self):
        boucle = asyncio.get_running_loop()
        self.serie = await boucle.run_in_executor(
            None, lambda: serial.Serial(self.port, VITESSE_SERIE, timeout=0.1)
        )
        # L'ouverture du port redémarre l'Arduino Mega : on attend son démarrage.
        await asyncio.sleep(2.5)
        self.serie.reset_input_buffer()
        self._actif = True
        self._fil = threading.Thread(target=self._lire, args=(boucle,), daemon=True)
        self._fil.start()

    def _lire(self, boucle):
        tampon = b""
        while self._actif:
            try:
                donnees = self.serie.read(64)
            except (serial.SerialException, OSError, TypeError):
                boucle.call_soon_threadsafe(self.recevoir, None)  # câble débranché
                return
            if not donnees:
                continue
            tampon += donnees
            while b"\n" in tampon:
                ligne, tampon = tampon.split(b"\n", 1)
                texte = ligne.decode("ascii", errors="replace").strip()
                if texte:
                    boucle.call_soon_threadsafe(self.recevoir, texte)

    def envoyer(self, ligne):
        self.serie.write((ligne + "\n").encode("ascii"))

    async def fermer(self):
        self._actif = False
        if self.serie:
            self.serie.close()


class Simulateur:
    """Imite le firmware V2_010 (+ commande Q) pour tester sans le bras."""

    simulee = True

    def __init__(self, recevoir):
        self.recevoir = recevoir
        self.port = "simulateur"
        self.q = [0.0] * NB_AXES
        self.plan = None
        self.t0 = 0.0
        self._tache = None

    async def ouvrir(self):
        await asyncio.sleep(0.3)

    def _position(self):
        if self.plan is None:
            return self.q
        return self.plan.position(time.monotonic() - self.t0)

    def _repondre(self, texte, delai=0.0):
        asyncio.get_running_loop().call_later(delai, self.recevoir, texte)

    def _lancer(self, plan):
        self.q = self._position()
        if self._tache:
            self._tache.cancel()
        self.plan, self.t0 = plan, time.monotonic()
        self._tache = asyncio.ensure_future(self._fin(plan))

    async def _fin(self, plan):
        await asyncio.sleep(plan.duree)
        self.q, self.plan = list(plan.q_fin), None
        self.recevoir("READY")

    def envoyer(self, ligne):
        morceaux = ligne.split()
        if not morceaux:
            return
        cmd, args = morceaux[0][:2], morceaux[1:]
        if cmd not in ("AT", "MT"):
            cmd = cmd[0]
        try:
            valeurs = [float(a) for a in args]
        except ValueError:
            return
        if cmd in ("A", "AT", "M", "MT"):
            if len(valeurs) < NB_AXES + (1 if cmd in ("AT", "MT") else 0):
                return
            cible = valeurs[:NB_AXES]
            if cmd in ("M", "MT"):
                cible = [cible[i] / PAS_PAR_DEGRE[i] for i in range(NB_AXES)]
            depart = self._position()
            cible = [c if ANGLE_MIN[i] <= c <= ANGLE_MAX[i] else depart[i] for i, c in enumerate(cible)]
            if cmd in ("A", "M"):
                plan = plan_synchronise(depart, cible)
            else:
                plan, _ = plan_avec_duree(depart, cible, valeurs[NB_AXES])
                if plan is None:
                    return  # le firmware annule sans répondre
            self._lancer(plan)
        elif cmd == "P":
            self._repondre("READY", 0.05)
        elif cmd == "R":
            self._repondre("READY", 1.0)
        elif cmd == "D":
            self._repondre("READY", (valeurs[0] if valeurs else 0) / 1000)
        elif cmd == "F" and len(valeurs) >= NB_AXES:
            if self._tache:
                self._tache.cancel()
            self.plan = None
            self.q = [valeurs[i] / PAS_PAR_DEGRE[i] for i in range(NB_AXES)]
        elif cmd == "S":
            self.q = self._position()
            self.plan = None
            if self._tache:
                self._tache.cancel()
            self._repondre("STOPPED", 0.01)
        elif cmd == "Q":
            self._repondre("POS " + " ".join(f"{a:.3f}" for a in self._position()), 0.01)

    async def fermer(self):
        if self._tache:
            self._tache.cancel()
