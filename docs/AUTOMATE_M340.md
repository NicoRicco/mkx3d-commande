# Piloter le bras depuis un automate Modicon M340

Le serveur du robot (`serveur/app.py`) contient un **serveur Modbus TCP**. L'automate s'y connecte
par Ethernet. Il ne pilote pas les moteurs lui-même : il gère le cycle (« lance la trajectoire n°2 »,
« ouvre la pince », « arrête ») et lit l'état du robot, comme avec un robot industriel.

```
M340 (client Modbus TCP) ──Ethernet──▶ PC : serveur MKX3D (port 502) ──USB──▶ Arduino ──▶ drivers ──▶ moteurs
```

Les trajectoires sont créées dans l'interface web (onglet Trajectoire), puis appelées par leur numéro.

## 1. Mise en place

1. **Réseau** : relier le M340 et le PC sur le même switch, avec des adresses fixes du même réseau.
   Exemple : M340 `192.168.1.10`, PC `192.168.1.20`, masque `255.255.255.0`.
2. **Port Ethernet du M340** : port intégré du CPU (BMX P34 2020 / 2030) ou module BMX NOE 0100 / NOC 0401.
3. **Serveur du robot** : lancer `lancer.bat` comme d'habitude. Le serveur Modbus démarre tout seul
   sur le port **502** (message « Serveur Modbus TCP pour automate : port 502 »).
   Au premier lancement, **autoriser Python dans le pare-feu Windows** (réseau privé).
   Option : `python serveur/app.py --modbus 0` le désactive.
4. **Nommer les trajectoires** en commençant par leur numéro : `1 - prise pièce`, `2 - dépose`, `03 - rangement`…
5. Avant de lancer un cycle, le robot doit être **connecté et calibré** dans l'interface (bit « prêt »).

## 2. Table d'échange

Tous les registres sont des mots de 16 bits (registres Modbus, vus comme des `%MW` à distance),
numérotés à partir de 0. Les valeurs négatives sont en complément à 2 (type `INT`).

### Écrits par l'automate (registres 0 à 3)

| Registre | Contenu |
|---|---|
| 0 | **Mot de commande** : bit 0 = départ trajectoire, bit 1 = arrêt, bit 2 = acquittement défaut, bit 3 = appliquer la consigne pince |
| 1 | Numéro de la trajectoire à lancer |
| 2 | Consigne de pince, 0 (fermée) à 100 % (ouverte) |
| 3 | Compteur de vie de l'automate (chien de garde) : à incrémenter régulièrement, 0 = chien de garde désactivé |

Les bits 0 à 3 agissent sur **front montant** : les remettre à 0 avant de redemander.

### Lus par l'automate (registres 10 à 28)

| Registre | Contenu |
|---|---|
| 10 | **Mot d'état** : bit 0 carte connectée, bit 1 **prêt**, bit 2 en mouvement, bit 3 trajectoire en cours, bit 4 **trajectoire terminée**, bit 5 **défaut**, bit 6 calibré, bit 7 simulateur |
| 11 | Numéro de la trajectoire en cours |
| 12 | Point en cours dans la trajectoire (1, 2, 3…) |
| 13 | Code défaut : 1 trajectoire inconnue, 2 robot pas prêt, 3 erreur pendant la trajectoire, 4 liaison carte perdue, 5 chien de garde |
| 14 | Ouverture actuelle de la pince (%) |
| 15 | Compteur de vie du robot (+1 toutes les 100 ms) |
| 20 à 25 | Angles des axes 1 à 6, en **dixièmes de degré** (ex. 125 = 12,5°) |
| 26 à 28 | Position de la pince X, Y, Z en mm |

- **Poignée de main pour lancer une trajectoire** : l'automate met « départ » (bit 0) à 1 et le garde ;
  le robot exécute puis met « terminé » (bit 4) à 1 ; l'automate remet « départ » à 0 ; le robot remet
  alors « terminé » à 0. L'automate attend que « terminé » soit retombé avant le départ suivant.
- Un défaut bloque les départs jusqu'à l'acquittement (bit 2 du mot de commande).
- **Chien de garde** : si le registre 3 a déjà été utilisé et ne change plus pendant 2 s alors que le robot
  bouge, le robot s'arrête et passe en défaut 5 (automate en STOP, câble débranché…).

## 3. Programme M340 (Control Expert / Unity Pro, langage ST)

### Variables à déclarer

| Nom | Type | Rôle |
|---|---|---|
| `Emiss` | `ARRAY[0..3] OF INT` | registres 0 à 3 envoyés au robot |
| `Recept` | `ARRAY[0..18] OF INT` | registres 10 à 28 reçus du robot |
| `Gest_Ecr`, `Gest_Lect` | `ARRAY[0..3] OF INT` | tables de gestion des échanges |
| `Commande`, `Numero`, `Pince`, `Vie`, `Etape` | `INT` | |
| `Presence_piece`, `Acquit` | `EBOOL` | entrées de la cellule (exemple) |

Dans **Outils → Options du projet → Variables**, cocher « Autoriser l'extraction de bits des INT et WORD »
pour pouvoir écrire `Recept[0].1`.

### Échanges avec le robot (section exécutée à chaque cycle)

Adresse `ADDM('0.0.3{192.168.1.20}')` : rack 0, emplacement 0 (CPU), voie 3 (port Ethernet du CPU),
suivi de l'adresse IP du PC. Avec un module NOE dans l'emplacement 2 : `ADDM('0.2.0{192.168.1.20}')`.

```
(* Écriture des registres 0 à 3 quand l'échange précédent est terminé *)
IF NOT Gest_Ecr[0].0 THEN
    Vie := Vie + 1;
    IF Vie > 30000 THEN Vie := 1; END_IF;
    Emiss[0] := Commande;
    Emiss[1] := Numero;
    Emiss[2] := Pince;
    Emiss[3] := Vie;
    Gest_Ecr[2] := 10;  (* délai maxi 1 s, en centaines de ms *)
    WRITE_VAR(ADDM('0.0.3{192.168.1.20}'), '%MW', 0, 4, Emiss, Gest_Ecr);
END_IF;

(* Lecture des registres 10 à 28 *)
IF NOT Gest_Lect[0].0 THEN
    Gest_Lect[2] := 10;
    READ_VAR(ADDM('0.0.3{192.168.1.20}'), '%MW', 10, 19, Gest_Lect, Recept);
END_IF;
```

Après l'échange, `Recept[0]` est le mot d'état (registre 10), `Recept[3]` le code défaut (registre 13),
`Recept[10]` à `Recept[15]` les angles, `Recept[16]` à `Recept[18]` la position X, Y, Z.

### Exemple de cycle : prise puis dépose d'une pièce

```
CASE Etape OF
0:  (* attente : robot prêt, pièce présente, poignée de main précédente terminée *)
    Commande := 0;
    IF Recept[0].1 AND NOT Recept[0].4 AND Presence_piece THEN
        Numero := 1;            (* trajectoire « 1 - prise pièce » *)
        Commande := 1;          (* bit 0 : départ, maintenu jusqu'à « terminé » *)
        Etape := 1;
    END_IF;
1:  (* attente de la fin de la prise *)
    IF Recept[0].4 THEN Commande := 0; Etape := 2;
    ELSIF Recept[0].5 THEN Etape := 10; END_IF;
2:  (* « terminé » retombe : on peut lancer la dépose *)
    IF NOT Recept[0].4 AND Recept[0].1 THEN
        Numero := 2;            (* trajectoire « 2 - dépose » *)
        Commande := 1;
        Etape := 3;
    END_IF;
3:  IF Recept[0].4 THEN Commande := 0; Etape := 0;
    ELSIF Recept[0].5 THEN Etape := 10; END_IF;
10: (* défaut : code dans Recept[3] *)
    Commande := 0;
    IF Acquit THEN Commande := 4; Etape := 11; END_IF;   (* bit 2 : acquittement *)
11: IF NOT Recept[0].5 THEN Commande := 0; Etape := 0; END_IF;
END_CASE;
```

Pour arrêter le robot depuis la cellule (porte ouverte, barrière immatérielle…), mettre le bit 1 de
`Commande` à 1 : `Commande := Commande OR 2;`.

**Sécurité** : ces échanges ne remplacent pas l'arrêt d'urgence câblé, qui doit toujours couper
l'alimentation des moteurs (voir `CABLAGE.md`).

## 4. Variante : scrutation d'E/S (I/O Scanning)

Si le module Ethernet le permet, on peut remplacer READ_VAR / WRITE_VAR par une ligne de scrutation
dans la configuration Ethernet de Control Expert : adresse IP du PC, **lecture** à partir du registre 10
sur 19 mots, **écriture** à partir du registre 0 sur 4 mots, période 100 ms. Le serveur du robot
accepte la fonction Modbus 23 utilisée par la scrutation.

## 5. Tester sans automate

Lancer le serveur, connecter le **Simulateur** dans l'interface, puis utiliser un logiciel client Modbus
(par exemple Modbus Poll ou QModMaster) sur l'adresse du PC, port 502 : lire les registres 10 à 28,
écrire 1 dans le registre 1 puis 1 dans le registre 0 pour lancer la trajectoire n°1.
