"""Serveur Modbus TCP : permet à un automate (Modicon M340, M221, S7-1200...) de piloter le bras.

L'automate lance des trajectoires enregistrées dans l'interface web (par leur numéro),
commande la pince, arrête le robot et lit son état. Table d'échange : docs/AUTOMATE_M340.md.

Tous les registres sont des mots de 16 bits (« holding registers »), numérotés à partir de 0.
Fonctions Modbus acceptées : 3, 4 (lecture), 6, 16 (écriture), 23 (lecture/écriture).
"""

import asyncio
import json
import re
import struct
import time
from pathlib import Path

from cinematique import position_outil
from robot import ErreurCommande

# --- registres écrits par l'automate ---
R_COMMANDE = 0      # bits : 0 départ trajectoire, 1 arrêt, 2 acquittement défaut, 3 appliquer la pince
R_NUMERO = 1        # numéro de la trajectoire à lancer
R_PINCE = 2         # consigne pince 0..100 %
R_VIE_AUTOMATE = 3  # compteur de vie de l'automate (chien de garde), 0 = désactivé
NB_ECRITURE = 10

# --- registres lus par l'automate ---
R_ETAT = 10         # bits : voir ETAT_* ci-dessous
R_NUM_EN_COURS = 11
R_POINT = 12
R_DEFAUT = 13
R_PINCE_ACTUELLE = 14
R_VIE_ROBOT = 15
R_ANGLES = 20       # 20 à 25 : angles des axes 1 à 6 en dixièmes de degré
R_XYZ = 26          # 26 à 28 : position de la pince X, Y, Z en mm
NB_REGISTRES = 30

ETAT_CONNECTE, ETAT_PRET, ETAT_MOUVEMENT, ETAT_TRAJECTOIRE = 1, 2, 4, 8
ETAT_TERMINE, ETAT_DEFAUT, ETAT_CALIBRE, ETAT_SIMULATEUR = 16, 32, 64, 128

DEFAUTS = {
    1: "trajectoire inconnue",
    2: "robot pas prêt (déconnecté, non calibré ou occupé)",
    3: "erreur pendant la trajectoire",
    4: "liaison avec la carte perdue",
    5: "chien de garde : l'automate ne répond plus",
}
DELAI_CHIEN_DE_GARDE = 2.0  # s


def _int16(v):
    v = int(round(v))
    return max(-32768, min(32767, v)) & 0xFFFF


class PasserelleAutomate:
    """Fait le lien entre la table Modbus et le robot."""

    def __init__(self, robot, dossier_traj, journal):
        self.robot = robot
        self.dossier_traj = Path(dossier_traj)
        self.journal = journal
        self.ecriture = [0] * NB_ECRITURE
        self.defaut = 0
        self.termine = False
        self.num_en_cours = 0
        self.lancee_par_automate = False
        self.vie_robot = 0
        self.vie_automate = None
        self.t_vie_automate = time.monotonic()
        self.clients = 0

    # ----- lecture de la table -----
    def registres(self, debut, nombre):
        r = self.robot
        if self.lancee_par_automate and r.lecture is None:
            self.lancee_par_automate = False
            if r.fin_lecture == "ok":
                self.termine = True
            elif r.fin_lecture == "erreur" and not self.defaut:
                self.defaut = 3
        q = r.q_estime()
        etat = 0
        if r.liaison:
            etat |= ETAT_CONNECTE
        if self._pret():
            etat |= ETAT_PRET
        if r.occupe:
            etat |= ETAT_MOUVEMENT
        if r.lecture:
            etat |= ETAT_TRAJECTOIRE
        if self.termine:
            etat |= ETAT_TERMINE
        if self.defaut:
            etat |= ETAT_DEFAUT
        if r.calibre:
            etat |= ETAT_CALIBRE
        if r.liaison and r.liaison.simulee:
            etat |= ETAT_SIMULATEUR
        table = [0] * NB_REGISTRES
        table[:NB_ECRITURE] = self.ecriture
        table[R_ETAT] = etat
        table[R_NUM_EN_COURS] = self.num_en_cours if r.lecture else 0
        table[R_POINT] = (r.lecture_info["index"] + 1) if r.lecture_info else 0
        table[R_DEFAUT] = self.defaut
        table[R_PINCE_ACTUELLE] = _int16(r.pince)
        table[R_VIE_ROBOT] = self.vie_robot
        for i in range(6):
            table[R_ANGLES + i] = _int16(q[i] * 10)
        for i, v in enumerate(position_outil(q)):
            table[R_XYZ + i] = _int16(v)
        if debut + nombre > NB_REGISTRES:
            raise IndexError
        return table[debut:debut + nombre]

    def _pret(self):
        r = self.robot
        return bool(r.liaison) and r.calibre and not r.occupe and r.lecture is None and not self.defaut

    # ----- écriture par l'automate -----
    def ecrire(self, debut, valeurs):
        if debut + len(valeurs) > NB_ECRITURE:
            raise IndexError
        avant = list(self.ecriture)
        self.ecriture[debut:debut + len(valeurs)] = [v & 0xFFFF for v in valeurs]
        self._traiter(avant)

    def _front(self, avant, bit):
        return not (avant[R_COMMANDE] >> bit) & 1 and (self.ecriture[R_COMMANDE] >> bit) & 1

    def _traiter(self, avant):
        if self.ecriture[R_VIE_AUTOMATE] != avant[R_VIE_AUTOMATE]:
            self.vie_automate = self.ecriture[R_VIE_AUTOMATE]
            self.t_vie_automate = time.monotonic()
        if self._front(avant, 1):
            self.journal("info", "Automate : arrêt demandé.")
            asyncio.ensure_future(self.robot.arreter())
        if self._front(avant, 2):
            self.defaut = 0
            self.termine = False
        if self._front(avant, 3):
            try:
                self.robot.regler_pince(min(100, self.ecriture[R_PINCE]))
            except ErreurCommande as e:
                self._mettre_defaut(2, str(e))
        if self._front(avant, 0):
            self._lancer(self.ecriture[R_NUMERO])
        elif (avant[R_COMMANDE] & 1) and not (self.ecriture[R_COMMANDE] & 1):
            self.termine = False  # l'automate a relâché « départ » : poignée de main terminée

    def _lancer(self, numero):
        self.termine = False
        if not self._pret():
            self._mettre_defaut(2)
            return
        points = self.charger_trajectoire(numero)
        if points is None:
            self._mettre_defaut(1, f"aucune trajectoire n°{numero}")
            return
        try:
            self.robot.lancer_lecture(points)
        except (ErreurCommande, KeyError, TypeError, ValueError) as e:
            self._mettre_defaut(3, str(e))
            return
        self.num_en_cours = numero
        self.lancee_par_automate = True
        self.journal("info", f"Automate : départ de la trajectoire n°{numero}.")

    def charger_trajectoire(self, numero):
        """Trajectoire dont le nom commence par le numéro : « 3 », « 03 - prise pièce »..."""
        for f in sorted(self.dossier_traj.glob("*.json")):
            m = re.match(r"\s*0*(\d+)", f.stem)
            if m and int(m.group(1)) == numero:
                try:
                    return json.loads(f.read_text(encoding="utf-8")).get("points") or None
                except (OSError, ValueError):
                    return None
        return None

    def _mettre_defaut(self, code, detail=""):
        self.defaut = code
        texte = DEFAUTS.get(code, "défaut") + (f" ({detail})" if detail else "")
        self.journal("erreur", f"Automate : {texte}")

    async def surveiller(self):
        """Compteur de vie et chien de garde, toutes les 100 ms."""
        while True:
            await asyncio.sleep(0.1)
            self.vie_robot = (self.vie_robot + 1) & 0x7FFF
            if self.robot.liaison is None and self.lancee_par_automate:
                self.lancee_par_automate = False
                self._mettre_defaut(4)
            garde = self.vie_automate not in (None, 0)
            if garde and self.robot.occupe and time.monotonic() - self.t_vie_automate > DELAI_CHIEN_DE_GARDE:
                self._mettre_defaut(5)
                self.vie_automate = None
                await self.robot.arreter()


class ServeurModbus:
    """Serveur Modbus TCP minimal (aucune bibliothèque nécessaire)."""

    def __init__(self, passerelle):
        self.p = passerelle
        self.serveur = None

    async def demarrer(self, hote, port):
        self.serveur = await asyncio.start_server(self._client, hote, port)

    async def arreter(self):
        if self.serveur:
            self.serveur.close()
            await self.serveur.wait_closed()

    async def _client(self, lecteur, ecrivain):
        adresse = ecrivain.get_extra_info("peername")
        self.p.clients += 1
        self.p.journal("info", f"Automate connecté en Modbus TCP ({adresse[0] if adresse else '?'}).")
        try:
            while True:
                entete = await lecteur.readexactly(7)
                tid, pid, longueur, unite = struct.unpack(">HHHB", entete)
                pdu = await lecteur.readexactly(longueur - 1)
                reponse = self._traiter(pdu)
                ecrivain.write(struct.pack(">HHHB", tid, pid, len(reponse) + 1, unite) + reponse)
                await ecrivain.drain()
        except (asyncio.IncompleteReadError, ConnectionError):
            pass
        finally:
            self.p.clients -= 1
            ecrivain.close()

    def _traiter(self, pdu):
        fc = pdu[0]
        try:
            if fc in (3, 4):
                debut, nombre = struct.unpack(">HH", pdu[1:5])
                return self._lecture(fc, debut, nombre)
            if fc == 6:
                adr, valeur = struct.unpack(">HH", pdu[1:5])
                self.p.ecrire(adr, [valeur])
                return pdu[:5]
            if fc == 16:
                debut, nombre = struct.unpack(">HH", pdu[1:5])
                valeurs = list(struct.unpack(f">{nombre}H", pdu[6:6 + 2 * nombre]))
                self.p.ecrire(debut, valeurs)
                return struct.pack(">BHH", fc, debut, nombre)
            if fc == 23:
                lect_debut, lect_nb, ecr_debut, ecr_nb = struct.unpack(">HHHH", pdu[1:9])
                valeurs = list(struct.unpack(f">{ecr_nb}H", pdu[10:10 + 2 * ecr_nb]))
                if ecr_nb:
                    self.p.ecrire(ecr_debut, valeurs)
                return self._lecture(fc, lect_debut, lect_nb)
            return bytes([fc | 0x80, 1])  # fonction non prise en charge
        except (IndexError, struct.error):
            return bytes([fc | 0x80, 2])  # adresse hors table

    def _lecture(self, fc, debut, nombre):
        if not 1 <= nombre <= 125:
            raise IndexError
        valeurs = self.p.registres(debut, nombre)
        return struct.pack(f">BB{nombre}H", fc, 2 * nombre, *valeurs)
