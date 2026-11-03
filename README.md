# MKX3D — Interface web de commande

Interface web pour piloter le bras [MKX3D](https://forge.apps.education.fr/bras-mkx3d) depuis n'importe quel
navigateur du réseau local (PC, tablette, téléphone). Le PC relié en USB à l'Arduino Mega fait tourner un petit
serveur Python, qui envoie les commandes du firmware (`A`, `AT`, `P`, `F`, `S`…) sur le port série.

```
 Navigateur (PC, tablette…) ──WebSocket──▶ serveur Python (PC) ──USB/série 9600 bauds──▶ Arduino Mega ──▶ 6 moteurs + pince
```

## Fonctions

- **Axes** : pilotage axe par axe (curseurs, boutons ±, pas réglable), envoi direct ou groupé, durée imposée (`AT`).
- **Pince** : ouverture 0–100 % (`P`).
- **Cartésien** : déplacement de l'extrémité en X/Y/Z et en orientation, avec le modèle géométrique inverse
  calculé dans le navigateur (modèle DH du jumeau numérique, `rtb/mkx3d.py`).
- **Trajectoires** : enregistrement de points (angles, pince, durée, pause), lecture simple ou en boucle,
  sauvegarde sur le PC (`trajectoires/*.json`), import des CSV du jumeau numérique.
- **Calibration** : sans fins de course, on indique à l'Arduino la position réelle du bras (`F`).
  La dernière position connue est mémorisée dans `derniere_position.json`.
- **Vue 3D** en temps réel (modèle Blender exporté en `web/modele/bras.glb`, ou bras simplifié à défaut).
- **ARRÊT** : bouton rouge ou touche **Échap**, depuis n'importe quel onglet.
- **Simulateur** : choisir « Simulateur » dans la liste des ports pour tout tester sans le bras.
- **Journal** des échanges série.

## Installation (une seule fois)

Python 3.9 ou plus récent :

```bash
pip install -r requirements.txt
```

## Lancement

```bash
python serveur/app.py
```

Puis ouvrir <http://localhost:8080>. Le terminal affiche aussi l'adresse à utiliser depuis un autre appareil du réseau.
Sous Windows, double-cliquer sur `lancer.bat`.

Options utiles :

| Option | Rôle |
|---|---|
| `--serie COM3` (ou `/dev/ttyACM0`, `simulateur`) | se connecter automatiquement au démarrage |
| `--port-web 8080` | port de l'interface web |
| `--hote 127.0.0.1` | n'accepter que le PC lui-même (pas le réseau) |

## Première utilisation avec le bras

1. Brancher l'Arduino, lancer le serveur, choisir le port et cliquer sur **Connecter**.
   L'ouverture du port **redémarre l'Arduino** : il croit alors que tous les axes sont à 0°.
2. Un bandeau demande la calibration : si le bras est en position zéro, cliquer sur **Le bras est en position zéro**.
   Sinon, saisir ses angles dans l'onglet **Calibration**, ou reprendre la dernière position connue.
3. Tester un petit mouvement (pas de 1° ou 5°) sur chaque axe et vérifier **le sens de rotation** par rapport à la vue 3D.

## Câblage

Voir [CABLAGE.md](CABLAGE.md) et le [schéma électrique](docs/schema_electrique.pdf).

## Firmware

L'interface fonctionne avec le firmware d'origine `FirmwareArduinoV2_010.ino`.

Le dossier `firmware/FirmwareArduinoV2_011` contient une version légèrement modifiée (protocole inchangé par ailleurs) :

- nouvelle commande `Q` : l'Arduino renvoie la position de chaque axe (`POS a1 … a6`, en degrés) ;
- la commande `S` arrête les axes sur place, mémorise leur position et répond `STOPPED`.

Avec cette version, après un **ARRÊT** en plein mouvement, l'interface relit la position exacte au lieu de l'estimer.
Le serveur détecte automatiquement quelle version est installée.

## Modèle 3D

`web/modele/bras.glb` (15,8 Mo) est exporté depuis `bras_mkx3d-9.blend` du jumeau numérique : armature,
pièces de chaque segment, socle et table, couleurs d'origine, maillages simplifiés. Ses articulations suivent
le modèle cinématique à 0,2 mm près.

Pour le régénérer après une modification du fichier Blender :

```bash
blender -b chemin/vers/bras_mkx3d-9.blend --python outils/export_glb.py
```

## Organisation

```
serveur/   app.py (web + WebSocket), robot.py (logique), liaison.py (série + simulateur),
           mouvement.py (profils de vitesse du firmware), config.py (paramètres du bras)
web/       interface (HTML/CSS/JS, three.js inclus dans web/vendor)
firmware/  firmware V2_011 optionnel
outils/    export du modèle Blender
```

## Points à vérifier sur le vrai bras

- Les paramètres de `serveur/config.py` doivent rester identiques à ceux du firmware (réductions, micro-pas, vitesses, limites).
- Le modèle géométrique (vue 3D, cartésien) suppose que les angles envoyés à l'Arduino suivent la même convention
  que le jumeau numérique (sens et zéro de chaque axe). À contrôler axe par axe au premier essai.
- Les limites du firmware (axe 1 : ±90°) sont plus étroites que celles du jumeau (±180°) : certains CSV du jumeau
  contiennent des points refusés par l'interface.
- Le serveur n'a pas de mot de passe : toute personne du réseau local qui ouvre la page peut piloter le bras.
  Utiliser `--hote 127.0.0.1` pour limiter l'accès au PC lui-même.

## Licence

Le firmware V2_011 dérive du firmware MKX3D (CC BY-NC-SA 4.0). three.js est sous licence MIT (`web/vendor/three/LICENSE`).
