"""Paramètres du bras MKX3D.

Les valeurs reprennent celles du firmware Arduino (FirmwareArduinoV2_010.ino,
section « Paramètres du bras MKX3D-IMT »). Si tu modifies le firmware,
mets ce fichier à jour pour que le serveur reste cohérent.
"""

NB_AXES = 6

# Moteurs pas-à-pas
PAS_PAR_TOUR = 200.0
REDUCTIONS = [8.333, 5.5, 21.5, 5.18, 19.41, 1.0]
MICRO_PAS = [4, 4, 1, 2, 1, 4]

# Vitesses (°/s) et accélérations (°/s²) maximales par axe
VITESSES_MAX = [25, 28, 35, 35, 10, 90]
ACCELERATIONS_MAX = [70, 7, 7, 15, 10, 50]

# Limites angulaires (°) appliquées par le firmware
ANGLE_MIN = [-90, -90, -100, -180, -90, -180]
ANGLE_MAX = [90, 90, 90, 180, 90, 180]

# Pas par degré, calculé comme dans le firmware
PAS_PAR_DEGRE = [PAS_PAR_TOUR * MICRO_PAS[i] * REDUCTIONS[i] / 360.0 for i in range(NB_AXES)]

# Liaison série : le firmware utilise Serial.begin(9600)
VITESSE_SERIE = 9600

# Identifiants USB reconnus pour la détection automatique (vid, pid)
CARTES_USB = {
    (0x2341, 0x0042): "Arduino Mega 2560",
    (0x2341, 0x0010): "Arduino Mega",
    (0x2A03, 0x0042): "Arduino Mega 2560 (clone)",
    (0x1A86, 0x7523): "Clone CH340",
    (0x0403, 0x6001): "Clone FTDI",
}

# Délai max d'attente de « READY » après un mouvement (s), en plus de la durée estimée
MARGE_TIMEOUT = 10.0
