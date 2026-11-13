# Bras MKX3D — Liste d'achats (pièces non imprimables)

Il n'existe pas de nomenclature officielle du bras (le dossier `plan` du dépôt modele-3d contient celle d'un
autre projet). Cette liste est reconstituée à partir du modèle CAO (fichiers SolidWorks et Blender du jumeau),
du firmware et du montage réel. **Les quantités de visserie et de roulements sont estimées** : prévoir les lots.

Prix relevés en novembre 2026 sur des pages de vente (instantanés, à vérifier avant commande ; HT ou TTC
selon le site, frais de port en plus). « ≈ » = estimation.

## 1. Moteurs (commande groupée chez StepperOnline, le moins cher constaté)

| Qté | Pièce | Axe | Prix unitaire | Où |
|---|---|---|---|---|
| 2 | NEMA 23 **23HS41-1804S** (1,8 A, 2,4 N·m) | 2 épaule | 25,18 $ | [StepperOnline](https://www.omc-stepperonline.com/nema-23-bipolar-1-8deg-2-4nm-340oz-in-1-8a-4-95v-57x57x104mm-4-wires-23hs41-1804s) |
| 1 | NEMA 17 + réducteur 5:1 **17HS19-1684S-PG5** | 3 coude | 28,86 $ | [StepperOnline](https://www.omc-stepperonline.com/nema-17-stepper-motor-bipolar-l-48mm-w-gear-ratio-5-1-planetary-gearbox-17hs19-1684s-pg5) |
| 1 | NEMA 17 + réducteur 5:1 **17HS15-1684S-PG5** | 4 avant-bras | 27,69 $ | [StepperOnline](https://www.omc-stepperonline.com/nema-17-stepper-motor-bipolar-l-38mm-w-gear-ratio-5-1-planetary-gearbox-17hs15-1684s-pg5) |
| 1 | NEMA 14 + réducteur 5:1 **14HS13-0804S-PG5** | 5 poignet | 36,77 $ | [Oyostepper](https://oyostepper.com/goods-283-Nema-14-Stepper-Motor-Bipolar-L=33mm-w-Gear-Ratio-5-1-Planetary-Gearbox.html) (chercher aussi sur StepperOnline) |
| 1 | NEMA 14 **14HS13-0804S** | 6 rotation pince | 8,48 $ | [StepperOnline](https://www.omc-stepperonline.com/nema-14-bipolar-1-8deg-18ncm-25-5oz-in-0-8a-5-4v-35x35x34mm-4-wires-14hs13-0804s) |
| 1 | NEMA 17 (≈ 42 × 48 mm, à confirmer) | 1 base (plus tard) | ≈ 12 $ | StepperOnline |
| 1 | Servomoteur **MG996R** (format standard) | pince | 6 à 13 € | [Tinytronics](https://www.tinytronics.nl/shop/en/mechanics-and-actuators/motors/servomotors/mg996r-servo), [Otronic](https://otronic.nl/en/go/product/140568980) |

Sous-total moteurs : ≈ 160 $ hors port et TVA (≈ 190 € livrés).

## 2. Électronique

| Qté | Pièce | Prix | Où |
|---|---|---|---|
| 7 | Driver **TB6600** 9–42 V, 4 A (dont 2 pour l'épaule) | 22 € pièce, ou lot de 5 à 109 € | [Fruugo pièce](https://www.fruugo.fr/tb6600-stepper-motor-controller-4a-40v-dc-for-425786-motors-with-32-micro-steps-for-cnc-robotics-applications/p-388531483-833423781), [Fruugo lot de 5](https://www.fruugo.fr/tb6600-stepper-motor-driver-5pcs-for-nema17-nema23-4257-motors-4a-dc9-42v-compatible-with-3d-printers-and-engraving-machines/p-364834242-790830042) — souvent moins cher sur AliExpress (non vérifié) |
| 1 | **Arduino Mega 2560** compatible (CH340) + câble USB | 16 à 25 € | [LaskaKit](https://www.laskakit.cz/arduino-mega2560-klon), [Bot'n Roll](https://www.botnroll.com/en/arduino-boards/3835-arduino-mega-2560-r3-with-ch340-driver-usb-cable.html) |
| 1 | Shield **bornier à vis** pour Mega | ≈ 14 € | [eBay](https://www.ebay.de/itm/205137414904) |
| 1 | Alimentation **Mean Well LRS-350-12** (12 V 29 A) | 31 à 50 € | [e-Sonic](https://www.e-sonic.com/fr/mean-well/lrs35012-47466831.html), [Audiophonics](https://www.audiophonics.fr/fr/alimentations-smps/mean-well-lrs-350-12-module-d-alimentation-a-decoupage-smps-12v-29a-348w-p-17203.html) — déjà en ta possession |
| 1 | Embase **C14** interrupteur + porte-fusible + fusible 5×20 temporisé 3,15 A | ≈ 2 € + 1 € | [Audiophonics](https://www.audiophonics.fr/fr/embases-iec/embase-iec-porte-fusible-interrupteur-porte-fusible-10a-p-6842.html) |
| 1 | Cordon secteur C13 | ≈ 3 € | — |
| 1 | **Arrêt d'urgence** coup-de-poing 22 mm, contact NF, + boîtier | 20 € (lot de 2) à 60 € (Omron) | [ManoMano lot de 2](https://www.manomano.fr/p/2pieces-12v24v48v220v-10a-bouton-poussoir-darret-durgence-champignon-rouge-22mm-no-nc-interrupteurs-a-bouton-poussoir-91963627), [RS Omron A22E](https://fr.rs-online.com/web/p/products/8411809) — déjà en ta possession |
| 1 | Convertisseur **LM2596** avec afficheur (réglé à 6 V pour le servo) | ≈ 7 € | [AZ-Delivery](https://www.az-delivery.de/en/products/lm2596s-buck-converter-mit-3-digits-voltmeter-display) |

## 3. Transmission (courroies et poulies)

Profil mesuré dans la CAO : **T5 (pas 5 mm), largeur 16 mm**, poulies 14 dents. Courroies fermées en
polyuréthane à câbles acier, **simple face** (éviter les références « DT5 » = double face).

**Longueurs estimées depuis le modèle 3D (± 10 mm) : à vérifier avec une ficelle sur les pièces imprimées
avant de commander.** Les tendeurs du bras rattrapent un petit écart.

| Qté | Pièce | Axe | Prix | Où |
|---|---|---|---|---|
| 2 | Courroie T5 **≈ 455–460 mm** / 16 mm | 2 épaule | ≈ 23 € | [Klium Conti T5-460-16](https://www.klium.be/en/conti-t5-460-16-f-3-8-conti-synchroflex-timing-belt-t546016-142002) |
| 1 | Courroie T5 **≈ 420 mm** / 16 mm | 3 coude | ≈ 22 € | [RS Optibelt 420 mm](https://fr.rs-online.com/web/p/courroies-synchrones/2170495) |
| 1 | Courroie T5 **≈ 280–290 mm** / 16 mm | 5 poignet | ≈ 20 € | [RS Optibelt 280 mm](https://fr.rs-online.com/web/p/courroies-synchrones/2170478) |
| 1 | Courroie T5 **≈ 600–610 mm** / 15-16 mm | 1 base (plus tard) | ≈ 25 € | RS / Klium |
| 4 | Poulie **T5 14 dents, alésage 8 mm, 16 mm**, alu | 2 (×2), 3, 5 | 5,81 € TTC | [RS Optibelt 236-5399](https://fr.rs-online.com/web/p/poulies/2365399) |
| 1 | Poulie T5 14 dents, alésage 5 mm | 1 base (plus tard) | ≈ 6 € | RS |

## 4. Roulements

| Qté | Pièce | Usage | Prix | Où |
|---|---|---|---|---|
| ≈ 8 (lot de 10) | **608ZZ** 8 × 22 × 7 | axes sur douilles Ø 8 | ≈ 6 € les 10 | [3DJake](https://www.3djake.ch/fr-CH/3djake/roulements-a-billes?sai=33688), [ManoMano lot de 30](https://www.manomano.fr/p/lot-de-20-roulements-a-billes-608-zz-double-blindage-213594912) |
| ≈ 8 (lot de 10) | **623ZZ** 3 × 10 × 4 | galets des tendeurs | ≈ 0,50–0,70 € pièce | [Olimex](https://www.olimex.com/Products/Robot-CNC-Parts/Bearings/623ZZ/) |
| 4 | Butée à aiguilles **AXK2542** + 8 rondelles **AS2542** | rotations axes 4 et 6 | ≈ 5 € les 2 butées + 4 rondelles | [eBay](https://www.ebay.de/itm/297295087498), [123bearing](https://www.123bearing.com/bearing-housing/needle-roller-bearing/axial-needle/axk2542) |

## 5. Visserie et quincaillerie

| Qté | Pièce | Prix |
|---|---|---|
| 1 coffret | Vis **M3** tête cylindrique six pans creux (DIN 912) 6, 10, 16, 20 mm + écrous M3 + écrous **nylstop** M3 + rondelles M3 | 10 à 20 € ([3DJake coffret M2–M5](https://www.3djake.ch/fr-CH/3djake/jeu-de-vis-a-tete-cylindrique-m2-m5-iso4762-din912-1152)) |
| 4 | Vis M4 × 20 tête cylindrique (fixation alimentation) | ≈ 1 € |
| 1 m | **Tige filetée M6** (axes L1, L2, L4) | ≈ 3 € (magasin de bricolage) |
| 10 | Écrous **nylstop M6** + 10 rondelles M6 | ≈ 3 € |
| 1 m | **Tube Ø 8 × 6 mm** alu ou laiton (douilles M6-8-20 et entretoises 6-8, à recouper) | ≈ 5 € |
| — | Vis sans tête M3 (poulies) : fournies avec les poulies | — |

## 6. Câblage

| Qté | Pièce | Prix |
|---|---|---|
| 10 m | Câble 4 conducteurs 4 × 0,5 mm² (rallonges moteurs) | ≈ 10 € |
| 5 m + 5 m | Fil 1,5 mm² rouge et noir (puissance 12 V, ARU) | ≈ 8 € |
| 1 bobine | Fil souple 0,5 mm² (signaux STEP/DIR) | ≈ 5 € |
| 1 lot | Embouts de câblage + pince à sertir | ≈ 15 € |
| 5 | Bornes Wago 221 (répartition +12 V / 0 V après l'ARU) | ≈ 5 € |
| 1 | Câble USB A–B (souvent fourni avec l'Arduino) | ≈ 3 € |
| 1 sachet | Colliers de serrage | ≈ 3 € |

## Budget indicatif

| Poste | Total |
|---|---|
| Moteurs + servo | ≈ 200 € |
| Électronique (hors alimentation et ARU déjà achetés) | ≈ 80 à 200 € selon l'origine des drivers |
| Courroies + poulies (bras sans la base) | ≈ 110 € |
| Roulements | ≈ 20 € |
| Visserie | ≈ 30 € |
| Câblage | ≈ 50 € |
| **Total** | **≈ 500 à 600 €** |

Pistes pour payer moins : drivers TB6600, Arduino, LM2596, servo, roulements et visserie sont en général
2 à 3 fois moins chers sur AliExpress (délai 2 à 4 semaines, prix non vérifiés ici). Les courroies T5 fermées
existent aussi sur AliExpress à quelques euros, mais vérifier qu'elles sont **à câbles acier** et au bon profil.

## Recherches Joybuy (liens prêts à ouvrir)

Joybuy n'a pas pu être consulté automatiquement (site protégé contre les robots) : ces liens ouvrent
directement la recherche sur joybuy.fr. Comparer avec les prix de référence ci-dessus et vérifier la référence exacte.

| Pièce | Recherche Joybuy |
|---|---|
| Drivers TB6600 (×7) | [TB6600](https://www.joybuy.fr/s?keyword=TB6600) |
| Moteur NEMA 23 2,4 Nm 1,8 A (×2, épaule) | [23HS41-1804S](https://www.joybuy.fr/s?keyword=23HS41-1804S) |
| NEMA 17 réducteur planétaire 5:1 (coude, avant-bras) | [nema 17 planetary gearbox 5:1](https://www.joybuy.fr/s?keyword=nema%2017%20planetary%20gearbox%205%3A1) |
| NEMA 14 réducteur 5:1 (poignet) | [nema 14 planetary gearbox](https://www.joybuy.fr/s?keyword=nema%2014%20planetary%20gearbox) |
| NEMA 14 0,8 A (rotation pince) | [14HS13-0804S](https://www.joybuy.fr/s?keyword=14HS13-0804S) |
| Arduino Mega 2560 | [Arduino Mega 2560](https://www.joybuy.fr/s?keyword=Arduino%20Mega%202560) |
| Shield bornier Mega | [Mega 2560 screw terminal shield](https://www.joybuy.fr/s?keyword=Mega%202560%20screw%20terminal%20shield) |
| Servo MG996R | [MG996R](https://www.joybuy.fr/s?keyword=MG996R) |
| Convertisseur LM2596 avec afficheur | [LM2596](https://www.joybuy.fr/s?keyword=LM2596) |
| Embase C14 interrupteur fusible | [C14 interrupteur fusible](https://www.joybuy.fr/s?keyword=C14%20interrupteur%20fusible) |
| Arrêt d'urgence 22 mm | [bouton arrêt d'urgence 22mm](https://www.joybuy.fr/s?keyword=bouton%20arr%C3%AAt%20d%27urgence%2022mm) |
| Courroie T5 16 mm fermée | [courroie T5 16mm](https://www.joybuy.fr/s?keyword=courroie%20T5%2016mm) |
| Poulie T5 14 dents alésage 8 | [poulie T5 14 dents](https://www.joybuy.fr/s?keyword=poulie%20T5%2014%20dents) |
| Roulements 608ZZ | [608ZZ](https://www.joybuy.fr/s?keyword=608ZZ) |
| Roulements 623ZZ | [623ZZ](https://www.joybuy.fr/s?keyword=623ZZ) |
| Butée à aiguilles AXK2542 | [AXK2542](https://www.joybuy.fr/s?keyword=AXK2542) |
| Coffret vis M3 BTR | [assortiment vis M3](https://www.joybuy.fr/s?keyword=assortiment%20vis%20M3) |
| Tige filetée M6 | [tige filetée M6](https://www.joybuy.fr/s?keyword=tige%20filet%C3%A9e%20M6) |
| Embouts de câblage + pince | [embouts de câblage pince à sertir](https://www.joybuy.fr/s?keyword=embouts%20de%20c%C3%A2blage%20pince%20%C3%A0%20sertir) |
| Câble 4 × 0,5 mm² | [câble 4x0.5mm2](https://www.joybuy.fr/s?keyword=c%C3%A2ble%204x0.5mm2) |
