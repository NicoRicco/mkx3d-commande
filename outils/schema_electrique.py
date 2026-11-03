"""Génère docs/schema_electrique.svg : schéma électrique complet du bras MKX3D.

Lancement :  python outils/schema_electrique.py
Les données (broches, réglages des drivers, moteurs) sont en tête de fichier :
les modifier ici puis relancer le script pour mettre le schéma à jour.
"""

import math
from pathlib import Path

SORTIE = Path(__file__).resolve().parent.parent / "docs" / "schema_electrique.svg"

DRIVERS = [
    # (axe, nom, moteur, micro-pas SW1-3, courant SW4-6, à faire plus tard)
    (1, "Base", "à identifier", "ON OFF OFF · 1/4", "selon étiquette", True),
    (2, "Épaule A", "23HS41-1804S · 1,8 A", "ON OFF OFF · 1/4", "ON ON OFF · 1,5 A", False),
    (2, "Épaule B", "23HS41-1804S · 1,8 A", "ON OFF OFF · 1/4", "ON ON OFF · 1,5 A", False),
    (3, "Coude", "17HS19-1684S-PG5", "ON ON OFF · 1", "ON ON OFF · 1,5 A", False),
    (4, "Avant-bras", "17HS15-1684S-PG5", "ON OFF ON · 1/2", "ON ON OFF · 1,5 A", False),
    (5, "Poignet", "14HS13-0804S-PG5", "ON ON OFF · 1", "ON ON ON · 0,5 A", False),
    (6, "Rotation pince", "14HS13-0804S", "ON OFF OFF · 1/4", "ON ON ON · 0,5 A", False),
]

L, H = 1700, 1480
ROUGE, NOIR, BLEU_SIG = "#d62828", "#1b1b1b", "#1f5fbf"
PHASE, NEUTRE, TERRE = "#8b4513", "#1f6fd6", "#3a9a3a"
FIL_MOTEUR = {"A+": "#1b1b1b", "A−": "#2a9d3a", "B+": "#d62828", "B−": "#1f6fd6"}

el = []


def ligne(points, couleur=NOIR, larg=2.0, pointille=False):
    d = " ".join(f"{x},{y}" for x, y in points)
    dash = ' stroke-dasharray="7 5"' if pointille else ""
    el.append(f'<polyline points="{d}" fill="none" stroke="{couleur}" stroke-width="{larg}" '
              f'stroke-linejoin="round" stroke-linecap="round"{dash}/>')


def texte(x, y, t, taille=13, ancre="start", gras=False, couleur="#1b2230", italique=False):
    poids = ' font-weight="700"' if gras else ""
    style = ' font-style="italic"' if italique else ""
    t = t.replace("&", "&amp;").replace("<", "&lt;")
    el.append(f'<text x="{x}" y="{y}" font-size="{taille}" text-anchor="{ancre}" fill="{couleur}"{poids}{style}>{t}</text>')


def boite(x, y, l, h, titre=None, sous_titre=None, fond="#f6f8fb", pointille=False):
    dash = ' stroke-dasharray="7 5"' if pointille else ""
    el.append(f'<rect x="{x}" y="{y}" width="{l}" height="{h}" rx="6" fill="{fond}" stroke="#1b2230" stroke-width="1.6"{dash}/>')
    if titre:
        texte(x + l / 2, y + 20, titre, 14, "middle", True)
    if sous_titre:
        texte(x + l / 2, y + 37, sous_titre, 12, "middle", couleur="#4a5568")


def point(x, y, couleur=NOIR):
    el.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{couleur}"/>')


def borne(x, y, nom, cote="gauche", couleur="#1b2230"):
    el.append(f'<circle cx="{x}" cy="{y}" r="3.2" fill="#fff" stroke="#1b2230" stroke-width="1.4"/>')
    if cote == "gauche":
        texte(x + 8, y + 4, nom, 11.5, couleur=couleur)
    elif cote == "droite":
        texte(x - 8, y + 4, nom, 11.5, "end", couleur=couleur)
    elif cote == "bas":
        texte(x, y - 8, nom, 11.5, "middle", couleur=couleur)


def masse(x, y, etiquette=True):
    """Symbole de masse (0 V commun) sous le point (x, y)."""
    ligne([(x, y), (x, y + 10)], NOIR, 1.6)
    for i, demi in enumerate((9, 6, 3)):
        yy = y + 10 + i * 4
        ligne([(x - demi, yy), (x + demi, yy)], NOIR, 1.6)
    if etiquette:
        texte(x + 12, y + 22, "0 V", 10.5, couleur="#4a5568")


def non_connecte(x, y):
    ligne([(x - 5, y - 5), (x + 5, y + 5)], "#888", 1.6)
    ligne([(x - 5, y + 5), (x + 5, y - 5)], "#888", 1.6)


# ------------------------------------------------------------------ titre
texte(40, 42, "Bras MKX3D — Schéma électrique", 24, gras=True)
texte(40, 66, "Arduino Mega 2560 · 7 drivers TB6600 (épaule ×2) · alimentation 12 V · firmware V2_010 / V2_011", 13.5,
      couleur="#4a5568")

# ------------------------------------------------------------------ secteur et C14
y_l, y_n, y_pe = 140, 165, 190
texte(40, 245, "Secteur 230 V~", 12.5, gras=True)
for y, nom, c in ((y_l, "L", PHASE), (y_n, "N", NEUTRE), (y_pe, "PE", TERRE)):
    texte(40, y + 4, nom, 12, gras=True, couleur=c)
boite(80, 105, 150, 115)
texte(155, 98, "Embase C14", 13, "middle", True)
texte(155, 213, "interrupteur + fusible", 10.5, "middle", couleur="#4a5568")
# L : fusible + interrupteur ; N : interrupteur ; PE direct
ligne([(60, y_l), (100, y_l)], PHASE, 2.4)
el.append(f'<rect x="100" y="{y_l - 6}" width="30" height="12" fill="#fff" stroke="{PHASE}" stroke-width="2"/>')
texte(115, y_l - 10, "F", 10, "middle", couleur=PHASE)
ligne([(130, y_l), (160, y_l)], PHASE, 2.4)
ligne([(160, y_l), (186, y_l - 10)], PHASE, 2.4)
ligne([(190, y_l), (250, y_l)], PHASE, 2.4)
ligne([(60, y_n), (160, y_n)], NEUTRE, 2.4)
ligne([(160, y_n), (186, y_n - 10)], NEUTRE, 2.4)
ligne([(190, y_n), (250, y_n)], NEUTRE, 2.4)
ligne([(173, y_l - 4), (173, y_n - 4)], "#888", 1.2, True)  # interrupteur bipolaire
ligne([(60, y_pe), (250, y_pe)], TERRE, 2.4)
ligne([(60, y_pe), (250, y_pe)], "#e0c020", 2.4, True)

# ------------------------------------------------------------------ alimentation
ax, ay = 250, 100
boite(ax, ay, 190, 130, "Mean Well LRS-350-12", "12 V ⎓ · 29 A")
for y, nom in ((y_l, "L"), (y_n, "N"), (y_pe, "⏚")):
    borne(ax, y, nom, "gauche")
y_pv, y_mv = 150, 200
borne(ax + 190, y_pv, "+V", "droite")
borne(ax + 190, y_mv, "−V", "droite")

# ------------------------------------------------------------------ bus de puissance
X_0V, X_12 = 960, 992
noeud_pv = (480, y_pv)
noeud_mv = (510, y_mv)
# +V -> ARU -> bus +12 V
ligne([(ax + 190, y_pv), (560, y_pv)], ROUGE, 2.6)
point(*noeud_pv, ROUGE)
# symbole de l'ARU (contact NF à accrochage)
cx1, cx2 = 560, 640
el.append(f'<circle cx="{cx1}" cy="{y_pv}" r="3.5" fill="#fff" stroke="{ROUGE}" stroke-width="2"/>')
el.append(f'<circle cx="{cx2}" cy="{y_pv}" r="3.5" fill="#fff" stroke="{ROUGE}" stroke-width="2"/>')
ligne([(cx1 + 4, y_pv), (cx2 - 6, y_pv + 7)], ROUGE, 2.4)
ligne([(cx2 - 4, y_pv - 2), (cx2 - 4, y_pv + 10)], ROUGE, 2.4)
ligne([(600, y_pv + 3), (600, y_pv - 34)], "#555", 1.4, True)
el.append(f'<path d="M 580 {y_pv - 34} A 20 14 0 0 1 620 {y_pv - 34} Z" fill="{ROUGE}" stroke="#7a1010" stroke-width="1.4"/>')
texte(600, y_pv - 54, "ARU", 13, "middle", True, ROUGE)
texte(600, y_pv + 32, "contact NF · ≥ 10 A", 10.5, "middle", couleur="#4a5568")
ligne([(cx2 + 4, y_pv), (X_12, y_pv), (X_12, 205 + 6 * 165 + 18)], ROUGE, 3)
texte(X_12 + 6, y_pv - 8, "+12 V moteurs", 12, gras=True, couleur=ROUGE)
texte(X_12 + 6, y_pv + 8, "(coupé par l'ARU)", 10.5, couleur=ROUGE)
# −V -> bus 0 V
ligne([(ax + 190, y_mv), (X_0V, y_mv), (X_0V, 205 + 6 * 165 + 36)], NOIR, 3)
point(*noeud_mv)
texte(X_0V - 6, y_mv - 8, "0 V", 12, "end", True)

# ------------------------------------------------------------------ convertisseur (Arduino)
bx, by = 290, 300
boite(bx - 30, by, 190, 100, "Convertisseur LM2596", "réglé à 6 V")
borne(bx + 160, 345, "IN+", "droite")
borne(bx + 160, 378, "IN−", "droite")
borne(bx - 30, 345, "OUT+", "gauche")
borne(bx - 30, 378, "OUT−", "gauche")
ligne([noeud_pv, (480, 345), (bx + 160, 345)], ROUGE, 2.2)
ligne([noeud_mv, (510, 378), (bx + 160, 378)], NOIR, 2.2)
texte(520, 300, "alimente le servo de pince ;", 10.5, couleur="#4a5568")
texte(520, 314, "non coupé par l'ARU", 10.5, couleur="#4a5568")

# ------------------------------------------------------------------ Arduino
gx, gy, gl, gh = 420, 470, 220, 470
boite(gx, gy, gl, gh, "Arduino Mega 2560", "+ shield bornier à vis", "#eef6ee")
broches = []
for k in range(12):
    y = 510 + 22 * k
    borne(gx + gl, y, f"D{k + 2}", "droite")
    broches.append(y)
y_gnd_ard = 790
borne(gx + gl, y_gnd_ard, "GND", "droite")
ligne([(gx + gl, y_gnd_ard), (gx + gl + 20, y_gnd_ard)], NOIR, 2)
masse(gx + gl + 20, y_gnd_ard)
# alimentation jack + USB
y_usb = 820
borne(gx, y_usb, "USB", "gauche")
texte(gx + 10, 600, "Jack : non branché", 11, couleur="#4a5568", italique=True)
texte(gx + 10, 615, "(alimenté par l'USB)", 11, couleur="#4a5568", italique=True)
# sortie 6 V du convertisseur -> servo de pince
ligne([(bx - 30, 345), (232, 345), (232, 440), (380, 440), (380, 1052), (450, 1052)], ROUGE, 2.2)
ligne([(bx - 30, 378), (214, 378), (214, 455), (395, 455), (395, 1072), (450, 1072)], NOIR, 2.2)
texte(240, 434, "6 V servo", 11, gras=True, couleur=ROUGE)
boite(40, 790, 190, 60, "PC", "serveur mkx3d-commande")
ligne([(230, y_usb), (gx, y_usb)], "#555", 2.4)
texte(325, y_usb - 6, "USB : alim. + données", 10.5, "middle", couleur="#4a5568")
# broche 22 -> servo (à venir)
x22 = 530
borne(x22, gy + gh, "D22", "bas")
ligne([(x22, gy + gh), (x22, 1000)], "#7a4fbf", 2, True)
boite(450, 1000, 160, 88, "Servo de pince", "à venir", "#f7f2fd", True)
borne(450, 1052, "+6 V", "gauche")
borne(450, 1072, "GND", "gauche")
texte(x22 + 8, 975, "signal", 10.5, couleur="#7a4fbf")

# ------------------------------------------------------------------ drivers et moteurs
dx, dl, dh, pas = 1040, 260, 150, 165
y0 = 205
OFFS = {"VCC": 18, "GND": 36, "DIR+": 60, "PUL+": 78, "DIR−": 96, "PUL−": 114, "ENA+": 130, "ENA−": 144}
cibles = {}  # axe -> liste de (y DIR+, y PUL+)
for i, (axe, nom, moteur, micro, courant, plus_tard) in enumerate(DRIVERS):
    y = y0 + i * pas
    boite(dx, y, dl, dh, fond="#f3f3f3" if plus_tard else "#f6f8fb", pointille=plus_tard)
    texte(dx + 140, y + 22, f"Axe {axe} — {nom}", 14, "middle", True)
    texte(dx + 140, y + 40, "TB6600" + (" · plus tard" if plus_tard else ""), 12, "middle", couleur="#4a5568")
    texte(dx + 140, y + 70, "SW1-3 (micro-pas)", 10, "middle", couleur="#4a5568")
    texte(dx + 140, y + 84, micro, 11.5, "middle", True)
    texte(dx + 140, y + 106, "SW4-6 (courant)", 10, "middle", couleur="#4a5568")
    texte(dx + 140, y + 120, courant, 11.5, "middle", True)
    for b, o in OFFS.items():
        borne(dx, y + o, b, "gauche")
    # puissance
    ligne([(X_12, y + OFFS["VCC"]), (dx, y + OFFS["VCC"])], ROUGE, 2.2)
    point(X_12, y + OFFS["VCC"], ROUGE)
    ligne([(X_0V, y + OFFS["GND"]), (dx, y + OFFS["GND"])], NOIR, 2.2)
    point(X_0V, y + OFFS["GND"])
    # DIR− et PUL− pontés vers le 0 V commun (montage cathode commune)
    xm = dx - 22
    ligne([(dx, y + OFFS["DIR−"]), (xm, y + OFFS["DIR−"]), (xm, y + OFFS["PUL−"]), (dx, y + OFFS["PUL−"])], NOIR, 1.8)
    point(xm, y + OFFS["PUL−"])
    masse(xm, y + OFFS["PUL−"], etiquette=False)
    non_connecte(dx, y + OFFS["ENA+"])
    non_connecte(dx, y + OFFS["ENA−"])
    cibles.setdefault(axe, []).append((y + OFFS["DIR+"], y + OFFS["PUL+"]))
    # moteur
    mx, my, r = 1495, y + 75, 36
    for j, (b, o) in enumerate((("A+", 42), ("A−", 62), ("B+", 92), ("B−", 112))):
        yb = y + o
        borne(dx + dl, yb, b, "droite")
        ey = my - 27 + j * 18
        ex = mx - math.sqrt(r * r - (ey - my) ** 2)
        ligne([(dx + dl, yb), (1385, yb), (1415, ey), (ex, ey)], FIL_MOTEUR[b], 2.4, plus_tard)
    dash = ' stroke-dasharray="7 5"' if plus_tard else ""
    el.append(f'<circle cx="{mx}" cy="{my}" r="{r}" fill="#fff" stroke="#1b2230" stroke-width="2"{dash}/>')
    texte(mx, my + 6, "M", 17, "middle", True)
    texte(mx + r + 12, my - 4, f"Axe {axe}" + (" (A)" if nom.endswith(" A") else " (B)" if nom.endswith(" B") else ""), 12.5, gras=True)
    texte(mx + r + 12, my + 12, moteur, 10.5, couleur="#4a5568")

# fils de commande Arduino -> drivers ; l'épaule (axe 2) commande 2 drivers en parallèle
for k, yp in enumerate(broches):
    axe = k // 2 + 1
    ys = [c[k % 2] for c in cibles[axe]]
    if max(ys) < yp:
        xl = 690 + 20 * k           # fils qui montent
    elif min(ys) > yp:
        xl = 920 - 20 * (k - 4)     # fils qui descendent
    else:
        xl = 730 + 20 * (k - 2)     # épaule : un driver au-dessus, un en dessous
    haut, bas = min(ys + [yp]), max(ys + [yp])
    ligne([(gx + gl, yp), (xl, yp)], BLEU_SIG, 1.8)
    ligne([(xl, haut), (xl, bas)], BLEU_SIG, 1.8)
    for yt in ys:
        ligne([(xl, yt), (dx, yt)], BLEU_SIG, 1.8)
        if haut < yt < bas:
            point(xl, yt, BLEU_SIG)
    if haut < yp < bas:
        point(xl, yp, BLEU_SIG)

# ------------------------------------------------------------------ légende et notes
lx, ly = 40, 1300
el.append(f'<rect x="{lx}" y="{ly}" width="900" height="155" rx="6" fill="#fff" stroke="#c9d0da"/>')
texte(lx + 14, ly + 22, "Légende et règles", 13, gras=True)
items = [
    (ROUGE, "+12 V moteurs (après ARU)"), (NOIR, "0 V commun"), (BLEU_SIG, "signaux STEP / DIR"),
    (PHASE, "phase 230 V"), (NEUTRE, "neutre"), ("#7a4fbf", "à venir"),
]
for n, (c, t) in enumerate(items):
    x = lx + 14 + (n % 3) * 210
    y = ly + 44 + (n // 3) * 20
    ligne([(x, y - 4), (x + 28, y - 4)], c, 3, c == "#7a4fbf")
    texte(x + 36, y, t, 11.5)
notes = [
    "• Arduino alimenté uniquement par l'USB du PC (jack débranché). Masses communes ; aucun fil vers le +5 V de l'Arduino.",
    "• ENA+ / ENA− non connectés : drivers toujours actifs. DIR−/PUL− pontés au 0 V (montage cathode commune).",
    "• Micro-pas identique au firmware (axes 1 à 6 : 4, 4, 1, 2, 1, 4). Interrupteurs réglés hors tension.",
    "• Épaule : 2 drivers en parallèle sur D4/D5, réglés à l'identique ; inverser A+/A− d'un des 2 moteurs s'ils tirent en sens contraire.",
    "• Après un arrêt d'urgence, recalibrer la position dans l'interface (onglet Calibration).",
]
for n, t in enumerate(notes):
    texte(lx + 14, ly + 88 + n * 15, t, 11)

texte(L - 40, H - 22, "Projet mkx3d-commande · généré par outils/schema_electrique.py", 10.5, "end",
      couleur="#8a94a6", italique=True)

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L} {H}" width="{L}" height="{H}" '
       f'font-family="DejaVu Sans, Segoe UI, Arial, sans-serif">\n'
       f'<rect width="{L}" height="{H}" fill="#ffffff"/>\n' + "\n".join(el) + "\n</svg>\n")
SORTIE.parent.mkdir(exist_ok=True)
SORTIE.write_text(svg, encoding="utf-8")
print(f"Schéma écrit : {SORTIE}")
