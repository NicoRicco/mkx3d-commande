# Câblage du bras MKX3D

Plan établi à partir du firmware `FirmwareArduinoV2_010.ino` et des pièces du modèle CAO
(drivers TB6600, Arduino Mega, alimentation, arrêt d'urgence, interrupteur C14 avec fusible).
Les points marqués **à confirmer** doivent être vérifiés sur le matériel réel.

> Toujours câbler **alimentation coupée**. Ne jamais brancher ni débrancher un moteur
> quand son driver est sous tension : ça détruit le driver.

## 1. Vue d'ensemble

```
Secteur 230 V ─ prise C14 (interrupteur + fusible) ─ alimentation 24 V (à confirmer)
                                                          │
                                         arrêt d'urgence (coupe le +24 V des drivers)
                                                          │
                                   ┌──────┬──────┬────────┼──────┬──────┬──────┐
                                 TB6600 TB6600 TB6600  TB6600 TB6600 TB6600
                                  axe 1  axe 2  axe 3   axe 4  axe 5  axe 6
                                   │      │      │       │      │      │
                                 moteur moteur moteur  moteur moteur moteur

PC ── USB ── Arduino Mega ── signaux STEP/DIR ──▶ les 6 drivers
                         └─ broche 22 ──▶ servomoteur de pince (alimenté en 5–6 V séparé)
```

## 2. Arduino Mega → drivers TB6600

| Axe | Rôle | DIR (broche) | STEP / PUL (broche) |
|---|---|---|---|
| 1 | Base | 2 | 3 |
| 2 | Épaule | 4 | 5 |
| 3 | Coude | 6 | 7 |
| 4 | Avant-bras | 8 | 9 |
| 5 | Poignet | 10 | 11 |
| 6 | Rotation pince | 12 | 13 |
| Pince | Servo (signal) | — | 22 |

Câblage conseillé de chaque TB6600 (montage « cathode commune ») :

| Borne TB6600 | Relier à |
|---|---|
| PUL+ | broche STEP de l'axe |
| PUL− | GND Arduino |
| DIR+ | broche DIR de l'axe |
| DIR− | GND Arduino |
| ENA+ / ENA− | **rien** (le firmware n'utilise pas l'activation : driver toujours actif) |

L'autre montage (« anode commune » : PUL+ et DIR+ au 5 V, PUL− et DIR− aux broches) marche aussi,
mais il faut le même sur les 6 drivers.

La broche 13 est aussi la LED de la carte : elle clignote quand l'axe 6 bouge, c'est normal.

## 3. Réglages des drivers (interrupteurs DIP)

**Le micro-pas doit être exactement celui du firmware**, sinon les angles seront faux
(un axe réglé en 1/8 au lieu de 1/4 ne fera que la moitié du mouvement demandé).

| Axe | Micro-pas (firmware) | Pas/tour à régler | Moteur (d'après la CAO) | Courant nominal |
|---|---|---|---|---|
| 1 | 4 | 800 | NEMA 23, 102 mm | à lire sur le moteur |
| 2 | 4 | 800 | 17HS19-1684S-PG5 (réducteur 5:1) | 1,68 A |
| 3 | 1 | 200 | 17HS15-1684S-PG5 (réducteur 5:1) | 1,68 A |
| 4 | 2 | 400 | 14HS13-0804S-PG5 (réducteur 5:1) | 0,8 A |
| 5 | 1 | 200 | 14HS13-0804S | 0,8 A |
| 6 | 4 | 800 | NEMA 17 (à confirmer) | à lire sur le moteur |

- Le tableau des interrupteurs (SW1 à SW6) est imprimé sur le boîtier du TB6600 :
  il varie selon les modèles, c'est lui qui fait foi.
- Certains TB6600 n'ont pas de vrai « pas entier » (1) : si c'est le cas, régler 1/2 et
  passer `MICRO_PAS` à 2 pour cet axe, à la fois dans le firmware et dans `serveur/config.py`.
- Courant : choisir le réglage **égal ou juste en dessous** du courant nominal du moteur
  (ex. 1,5 A pour un moteur à 1,68 A).

## 4. Moteurs → drivers

Chaque moteur a 2 bobines (4 fils) : A+ / A− sur une bobine, B+ / B− sur l'autre.

- Pour trouver les paires : au multimètre, deux fils de la **même bobine** ont une résistance
  de quelques ohms ; entre deux bobines différentes, il n'y a pas de continuité.
- Couleurs fréquentes chez StepperOnline (fabricant des références 17HS / 14HS) :
  noir (A+), vert (A−), rouge (B+), bleu (B−). **À vérifier** sur la fiche du moteur.
- Si un axe tourne dans le mauvais sens, inverser **les deux fils d'une seule bobine**
  (ex. A+ ↔ A−), driver hors tension.

## 5. Alimentations

- Drivers : VCC / GND du TB6600 sur l'alimentation (9 à 42 V selon le modèle, 24 V conseillé).
  Fils de section suffisante (≥ 0,75 mm² pour l'arrivée commune).
- Arduino : alimenté par l'USB du PC (suffisant pour les signaux).
- Servo de pince : **ne pas l'alimenter par le 5 V de l'Arduino** (appels de courant qui
  font redémarrer la carte). Utiliser un régulateur 5–6 V séparé.
- **Masses communes** : le GND de l'Arduino, du servo et (en cathode commune) des entrées
  PUL−/DIR− doivent être reliés.

## 6. Arrêt d'urgence

Le bouton ARRÊT de l'interface est logiciel : il ne remplace pas un arrêt d'urgence physique.
Le bouton coup-de-poing doit **couper l'alimentation des drivers** (contact NF en série sur le +24 V).

Conséquence : après un arrêt d'urgence physique, les moteurs ne sont plus maintenus et l'Arduino
ne sait plus où est le bras. Il faut le recalibrer (onglet Calibration) avant de repartir.

## 7. Ordre de mise en service conseillé

1. Drivers seuls sous tension, sans moteur : vérifier la tension et l'absence d'échauffement.
2. Un seul moteur branché, axe découplé du bras si possible : tester avec l'interface
   (pas de 1°) que le moteur tourne, dans le bon sens.
3. Brancher les axes un par un, en commençant par le poignet (axes 6, 5, 4), puis 3, 2, 1.
4. Contrôler pour chaque axe qu'une consigne de 10° donne bien 10° sur le bras.
