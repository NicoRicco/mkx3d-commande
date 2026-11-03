/*
 * Commande du bras MKX3D à partir de Scilab ou du moniteur série de l'IDE Arduino
 * Ce programme permet de contrôler le bras MKX3D.
 * Les commandes sont envoyées depuis Scilab via le port série de l'Arduino.
 *
 * Le protocole de communication avec Scilab est le suivant :
 * - Les commandes sont envoyées sous forme de chaînes de caractères,
 *   terminées par un caractère de fin de ligne ('\n' ou '\r').
 * - Chaque commande est composée d'un identifiant de commande (une ou deux lettres)
 *   suivi des paramètres, séparés par des espaces.
 * - Les commandes disponibles sont :
 *   - A: Déplacer les axes vers des angles absolus (en degrés).
 *   - AT: Déplacer les axes vers des angles absolus (en degrés) avec un temps spécifié (en secondes).
 *   - D: Pause pendant une durée spécifiée (en millisecondes).
 *   - F: Mettre à jour la position actuelle des moteurs.
 *   - M: Déplacer les axes vers des positions absolues (en pas).
 *   - MT: Déplacer les axes vers des positions absolues (en pas) avec un temps spécifié (en secondes).
 *   - P: Déplacer la pince à une position spécifiée (en pourcentage d'ouverture).
 *   - R: Vérifier la connexion avec la carte Arduino.
 *   - S ou STOP: Arrêter immédiatement tous les moteurs (répond STOPPED).
 *   - Q: Renvoyer la position actuelle des axes en degrés (répond POS a1 a2 a3 a4 a5 a6).
 *   - T: Déplacer les axes vers des positions avec des vitesses et des accélérations spécifiées.
 *
 *  Exemples de commandes:
 *  - A 0 0 0 0 0 10 : Déplacer l'axe 6 à 10 degrés.
 *  - AT 0 0 0 0 0 10 5 : Déplacer l'axe 6 à 10 degrés en 5 secondes.
 *  - P 100: Ouvrir la pince à 100%.
 *  - D 500: Faire une pause de 500 millisecondes.
 *
 *  Auteurs: P. Dalmeida et P. de Poumayrac
 *  Date de création: 20/01/2025
 *
 *  Ce programme est distribué sous licence Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0).
 *  Cette licence a pour but de permettre une amélioration continue de ce projet et d'assurer une grande réciprocité.
 *  Pour plus d'informations sur la licence, veuillez consulter le site web
 *  de Creative Commons : https://creativecommons.org/licenses/by-nc-sa/4.0/
 *
 /*
 * Commande du bras MKX3D à partir de Scilab ou du moniteur série de l'IDE Arduino
 * Ce programme permet de contrôler le bras MKX3D.
 * Les commandes sont envoyées depuis Scilab via le port série de l'Arduino.
 *
 * Structure du code :
 * 1. Appel des librairies
 * 2. Constantes
 *   2.1. Broches des moteurs
 *   2.2. Caractéristiques des moteurs
 *   2.3. Paramètres des bras
 * 3. Variables
 *   3.1. Commandes reçues
 *   3.2. État des moteurs
 *   3.3. Instances des moteurs et servomoteur
 *   3.4. Positions actuelles
 *   3.5. Variables de calcul
 * 4. Fonctions
 *   4.1. Initialisation (setup)
 *   4.2. Boucle principale (loop)
 *   4.3. Réception des commandes (couche de communication)
 *   4.4. Analyse des commandes (Couche de contrôle)
 *   4.5. Contrôle des moteurs (Couche de contrôle)
 *   4.6. Fonctions de mouvement (Couche de mouvement)
 *     4.6.1. Mouvement non synchronisé (moveAxesToAbsolutePositionsUnsynchronized)
 *     4.6.2. Mouvement synchronisé (moveAxesToAbsolutePositionsSynchronized)
 *     4.6.3. Mouvement avec temps spécifié (moveAxesToAbsolutePositionsWithTime)
 */

 /*
 *  V2_011 (interface web mkx3d-commande) :
 *  - Ajout de la commande Q (lecture de la position, réponse "POS ...")
 *  - La commande S arrête les axes sur place, met à jour currentAngles et répond "STOPPED"
 *  Le reste du protocole est inchangé.
 *
 *  Dernière modification du 03/02/2025 :
 * Ajout du texte de présentation et de la licence : fait
 * Ajout de la structure : fait
 * 
 */
// *** 1. Appel des librairies ***
#include <AccelStepper.h> // Importation de la librairie pour la gestion des Steppers
#include <Wire.h>         // Importation de la librairie pour la gestion du port I2C
#include <Servo.h>        // Importation de la librairie pour la gestion du servomoteur


// *** 2 Constantes ***
// 2.1. Broches des moteurs
const int motorDirectionPins[6] = {2, 4, 6, 8, 10, 12};   // broches de direction pour chaque moteur (axe 1 à 6)
const int motorStepPins[6] = {3, 5, 7, 9, 11, 13};        // broches de nombre de pas pour chaque moteur (axe 1 à 6)
const int servoPin = 22;                                  // broche de commande du servomoteur

// 2.2. Caractéristiques des moteurs
const float motorStepsPerRevolution = 200.0;  // 200 pas par révolution
const int motorInterfaceType = 1;             // utilisation d'un driver pour commander les moteurs pas-à-pas

/*// 2.3. Paramètres du bras PROTO
//Rapports de réduction pour chaque axe
const float axisGearRatios[6] = {8.333, 5.5, 21.5, 27.0, 19.41, 1.0};   // Rapports de réduction pour chaque axe
// Micro-stepping utilisé pour chaque axe
const int motorMicrosteps[6] = {32, 4, 4, 1, 1, 4};                     // Micro-pas pour chaque axe
// Vitesses et accélérations maximales
const float axisMaxSpeedsDeg[6] = {30, 30, 80, 60, 60, 60};             // vitesses maxi pour chaque axe en degrés par seconde
const float axisMaxAccelerationsDeg[6] = {30, 30, 60, 60, 300, 60};     // accélérations maxi pour chaque axe en degrés par seconde^2
*/

// 2.3. Paramètres du bras MKX3D-IMT
//Rapports de réduction pour chaque axe
const float axisGearRatios[6] = {8.333, 5.5, 21.5, 5.18, 19.41, 1.0}; // Rapports de réduction pour chaque axe
// Micro-stepping utilisé pour chaque axe
const int motorMicrosteps[6] = {4, 4, 1, 2, 1, 4}; // Micro-pas pour chaque axe
// Vitesses et accélérations maximales
const float axisMaxSpeedsDeg[6] = {25, 28, 35, 35, 10, 90}; // vitesses maxi pour chaque axe en degrés par seconde
const float axisMaxAccelerationsDeg[6] = {70, 7, 7, 15, 10, 50}; // accélérations maxi pour chaque axe en degrés par seconde^2


// Limites angulaires pour chaque axe (en degrés)
const float minAngles[6] = {-90, -90, -100, -180, -90, -180};   // Angles minimum pour chaque axe
const float maxAngles[6] = {90, 90, 90, 180, 90, 180};          // Angles maximum pour chaque axe

// *** 3. Variables ***
// 3.1. Commandes reçues

long targetSteps[6];                  // Positions cibles (en pas) reçues pour chaque moteur
float targetAngles[6];                // Positions cibles (en degrés) reçues pour chaque moteur
long targetGripperPosition;           // Positions cibles (en %) reçues pour la pince
float targetMoveTime;                 // Temps total de mouvement (en secondes) pour les commandes AT et MT
int receivedDelay;                    // Délai reçu (en millisecondes) pour la commande D
bool newCommandReceived = false;      // Indique si de nouvelles données ont été reçues


// 3.2. État des moteurs
volatile bool movementAllowed = false;  // Indicateurs pour les nouvelles données et l'autorisation de mouvement
volatile bool stopRequested = false;    // Indicateur pour demander l'arrêt immédiat

// 3.3. Instances des moteurs et servomoteur
AccelStepper steppers[6] = { 
    AccelStepper(motorInterfaceType, motorStepPins[0], motorDirectionPins[0]),
    AccelStepper(motorInterfaceType, motorStepPins[1], motorDirectionPins[1]),
    AccelStepper(motorInterfaceType, motorStepPins[2], motorDirectionPins[2]),
    AccelStepper(motorInterfaceType, motorStepPins[3], motorDirectionPins[3]),
    AccelStepper(motorInterfaceType, motorStepPins[4], motorDirectionPins[4]),
    AccelStepper(motorInterfaceType, motorStepPins[5], motorDirectionPins[5])
};
Servo pince; // Création de l'objet servo pour contrôler la pince


// 3.4. Positions actuelles
float currentAngles[6];       // Positions actuelles en degrés

// 3.5. Variables de calcul
float stepsPerDegree[6];      // Pas par degré pour chaque axe


// *** 4. Fonctions ***
// 4.1. Initialisation
void setup()
// Rôle: Initialise le programme. Configure le port série, attache le servomoteur et initialise les moteurs.
{
    Serial.begin(9600);
    pince.attach(servoPin); // Attache le servomoteur sur la broche servoPin

    // Calcul du nombre de pas par degré pour chaque axe
    for (int i = 0; i < 6; i++)
    {
        stepsPerDegree[i] = (motorStepsPerRevolution * motorMicrosteps[i] * axisGearRatios[i]) / 360.0;
        // Nombre de pas par degré pour l'axe i calculé en fonction du nombre de pas par révolution du moteur,
        // du micro-pas utilisé, du rapport de réduction.

        // Définition des vitesses et accélérations maximales en pas par seconde
        steppers[i].setMaxSpeed(axisMaxSpeedsDeg[i] * stepsPerDegree[i]);
        steppers[i].setAcceleration(axisMaxAccelerationsDeg[i] * stepsPerDegree[i]);
        steppers[i].setCurrentPosition(0); // Initialise la position actuelle à 0
        currentAngles[i] = 0;              // Initialise l'angle actuel à 0
        steppers[i].disableOutputs();      // Désactive les sorties
    }

    //Serial.println("Robot prêt");
}

// 4.2. Boucle principale
void loop() 
// Rôle: Boucle principale du programme. Appelle les fonctions pour recevoir les commandes et contrôler les moteurs.
{
    receiveCommands(); // Fonction pour recevoir les commandes
    runMotors(); // Fonction pour contrôler les moteurs
}

// 4.3. Réception des commandes (Couche de communication)
void receiveCommands() 
// Rôle: Vérifie si des données sont disponibles sur le port série et les stocke dans un tampon.
{
    static char inputBuffer[100]; // Tampon pour stocker les caractères reçus depuis le port série
    static int inputIndex = 0; // Indice du prochain caractère à écrire dans le tampon

    while (Serial.available() > 0)
    {
        char receivedChar = Serial.read();

        if (receivedChar == '\n' || receivedChar == '\r')
        {
            // Fin de la commande
            inputBuffer[inputIndex] = '\0'; // Termine la chaîne de caractères
            inputIndex = 0;
            newCommandReceived = true;
            processCommand(inputBuffer);
            break;
        }
        else
        {
            if (inputIndex < 99) // Évite le dépassement de tampon
            {
                inputBuffer[inputIndex++] = receivedChar;
            }
        }
    }
}

// 4.4. Analyse des commandes (Couche de contrôle)
void processCommand(char *commandLine) 
// Rôle: Analyse la commande reçue et appelle la fonction appropriée.
    // Paramètres: commandLine (pointeur vers la chaîne de caractères contenant la commande)
{
    // Extraction de la commande et des paramètres
    char *token = strtok(commandLine, " "); 

    if (token == NULL)
    {
        //Serial.println("Commande vide");
        return;
    }

    char cmd[3];
    strncpy(cmd, token, 2);
    cmd[2] = '\0'; // Assure que la chaîne est terminée

    // Détermine si la commande est d'un ou deux caractères
    if (strcmp(cmd, "AT") == 0 || strcmp(cmd, "MT") == 0)
    {
        // Commande à deux caractères
    }
    else
    {
        cmd[1] = '\0'; // Commande à un seul caractère
    }

    // Traitement de la commande
    if (strcmp(cmd, "A") == 0) // Traite la commande 'A'  -  Ex : A 0 0 0 0 0 10 (l'axe 6 se déplace vers la position 10 degrés)
    {

        for (int i = 0; i < 6; i++)
        {
            token = strtok(NULL, " ");
            if (token == NULL)
            {
                //Serial.println("Nombre insuffisant de paramètres pour la commande A");
                return;
            }
            targetAngles[i] = atof(token);

            // Vérification des limites angulaires
            if (targetAngles[i] < minAngles[i] || targetAngles[i] > maxAngles[i])
            {
                //Serial.print("ERROR - Limite atteinte sur l'axe N°");
                //Serial.println(i + 1);
                targetAngles[i] = currentAngles[i]; // Ne pas déplacer cet axe
            }

            // Conversion des angles en pas
            targetSteps[i] = targetAngles[i] * stepsPerDegree[i];
        }
        // Lancement de la fonction mouvement
        moveAxesToAbsolutePositionsSynchronized();
    }
    else if (strcmp(cmd, "AT") == 0) // Traite la commande 'AT' -  Ex : AT 0 0 0 0 0 10 5 (l'axe 6 se déplace vers la position 10 degrés en 5 secondes)    
    {
        
        for (int i = 0; i < 6; i++)
        {
            token = strtok(NULL, " ");
            if (token == NULL)
            {
                //Serial.println("Nombre insuffisant de paramètres pour la commande AT");
                return;
            }
            targetAngles[i] = atof(token);

            // Vérification des limites angulaires
            if (targetAngles[i] < minAngles[i] || targetAngles[i] > maxAngles[i])
            {
                //Serial.print("ERROR - Limite atteinte sur l'axe N°");
                //Serial.println(i + 1);
                targetAngles[i] = currentAngles[i]; // Ne pas déplacer cet axe
            }

            // Conversion des angles en pas
            targetSteps[i] = targetAngles[i] * stepsPerDegree[i];
        }

        // Récupération du temps total de déplacement
        token = strtok(NULL, " ");
        if (token == NULL)
        {
            //Serial.println("Temps non spécifié pour la commande AT");
            return;
        }
        targetMoveTime = atof(token);

        // Lancement de la fonction mouvement
        moveAxesToAbsolutePositionsWithTime(targetMoveTime);
    }

    else if (strcmp(cmd, "D") == 0) // Traite la commande 'D'  : "D 500" provoque un délai de 500 ms
    {
        token = strtok(NULL, " ");
        if (token == NULL)
        {
            //Serial.println("Paramètre manquant pour la commande D");
            return;
        }
        receivedDelay = atof(token);
        delay(receivedDelay);
        Serial.println("READY");

    }

    else if (strcmp(cmd, "F") == 0) // Traite la commande 'F' Mise à jour de la position actuelle
    {
        for (int i = 0; i < 6; i++)
        {
            token = strtok(NULL, " ");
            if (token == NULL)
            {
                //Serial.println("Nombre insuffisant de paramètres pour la commande F");
                return;
            }
            targetSteps[i] = atof(token);
            steppers[i].setCurrentPosition(targetSteps[i]);
            currentAngles[i] = targetSteps[i] / stepsPerDegree[i];
            steppers[i].disableOutputs();
        }
        movementAllowed = false;
        //Serial.println("Positions mises à jour");
    }


    else if (strcmp(cmd, "M") == 0)  // Traite la commande 'M' -  Ex : M 0 0 0 0 0 200 (l'axe 6 se déplace vers la position 200 pas)

    {
        for (int i = 0; i < 6; i++)
        {
            token = strtok(NULL, " ");
            if (token == NULL)
            {
                //Serial.println("Nombre insuffisant de paramètres pour la commande M");
                return;
            }
            targetSteps[i] = atof(token);

            // Calcul de l'angle cible
            float targetAngle = targetSteps[i] / stepsPerDegree[i];


            // Vérification des limites angulaires
            if (targetAngle < minAngles[i] || targetAngle > maxAngles[i])
            {
                //Serial.print("ERROR - Limite atteinte sur l'axe N°");
                //Serial.println(i + 1);
                targetSteps[i] = steppers[i].currentPosition(); // Ne pas déplacer cet axe
            }
        }
        // Lancement de la fonction mouvement
        moveAxesToAbsolutePositionsSynchronized();
    }
    
    
    else if (strcmp(cmd, "MT") == 0) //Traite la commande 'MT' -  Ex : M 0 0 0 0 0 200 5 (l'axe 6 se déplace vers la position 200 pas en 5 secondes)
    {
        for (int i = 0; i < 6; i++)
        {
            token = strtok(NULL, " ");
            if (token == NULL)
            {
                //Serial.println("Nombre insuffisant de paramètres pour la commande MT");
                return;
            }
            targetSteps[i] = atof(token);

            // Calcul de l'angle cible
            float targetAngle = targetSteps[i] / stepsPerDegree[i];

            // Vérification des limites angulaires
            if (targetAngle < minAngles[i] || targetAngle > maxAngles[i])
            {
                //Serial.print("ERROR - Limite atteinte sur l'axe N°");
                //Serial.println(i + 1);
                targetSteps[i] = steppers[i].currentPosition(); // Ne pas déplacer cet axe
            }
        }

        // Récupération du temps total de déplacement
        token = strtok(NULL, " ");
        if (token == NULL)
        {
            //Serial.println("Temps non spécifié pour la commande MT");
            return;
        }
        targetMoveTime = atof(token);

        // Lancement de la fonction mouvement
        moveAxesToAbsolutePositionsWithTime(targetMoveTime);
    }
    else if (strcmp(cmd, "P") == 0) //Traite la commande 'P' Pince seule - Ex : P 100 (la pince souvre à 100 %)
    {
        token = strtok(NULL, " ");
        if (token == NULL)
        {
            //Serial.println("Paramètre manquant pour la commande P");
            return;
        }
        targetGripperPosition = atof(token);
        targetGripperPosition = map(targetGripperPosition, 0, 100, 95, 40); // Mise à l'échelle pour le servo
        pince.write(targetGripperPosition); // Positionne le servo
        //delay(1000); // Attente pour que le servo atteigne la position
        Serial.println("READY");

    }
    else if (strcmp(cmd, "R") == 0) //Traite la commande 'R' - vérifie la connection avec la carte Arduino
    {
      delay(1000);
      Serial.println("READY");
    }

    else if (strcmp(cmd, "S") == 0 || strcmp(cmd, "STOP") == 0) //Traite la commande 'S' - Arrête les moteurs immédiatement
    {
        // Arrêt sur place : la cible devient la position actuelle
        for (int i = 0; i < 6; i++)
        {
            steppers[i].setCurrentPosition(steppers[i].currentPosition());
            currentAngles[i] = steppers[i].currentPosition() / stepsPerDegree[i];
        }
        movementAllowed = false;
        stopRequested = false;
        Serial.println("STOPPED");
    }

    else if (strcmp(cmd, "Q") == 0) // Traite la commande 'Q' - renvoie la position actuelle en degrés
    {
        Serial.print("POS");
        for (int i = 0; i < 6; i++)
        {
            Serial.print(" ");
            Serial.print(steppers[i].currentPosition() / stepsPerDegree[i], 3);
        }
        Serial.println();
    }

       
    else if (strcmp(cmd, "T") == 0) //Traite la commande 'T' -  lit une trame de 6x "position vitesse accélération" + valeur pince
      // Exemple -  T 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 200 500 10000 100
      //(l'axe 6 se déplace vers la position 200 pas à une vitesse de 500 pas/s avec une accélération de 10000 pas/s² et la pince s'ouvre à 100%)
    {
      for (int i = 0; i < 6; i++)
     {
        // Lecture des positions cibles en pas
        token = strtok(NULL, " ");
        targetSteps[i] = atol(token); // Pas de vérification des limites
        // Lecture des vitesses maximales en pas/s
        token = strtok(NULL, " ");
        float maxSpeed = atof(token);
        steppers[i].setMaxSpeed(maxSpeed); // Pas de vérification
        // Lecture des accélérations en pas/s²
        token = strtok(NULL, " ");
        float acceleration = atof(token);
        steppers[i].setAcceleration(acceleration); // Pas de vérification
      }

      // Lecture de la position pince
        token = strtok(NULL, " ");
        targetGripperPosition = atof(token);
        targetGripperPosition = map(targetGripperPosition, 0, 100, 95, 40); // Mise à l'échelle pour le servo
        pince.write(targetGripperPosition); // Positionne le servo
        //delay(200); // Attente pour que le servo atteigne la position
        //Serial.println("Robot en position"); //inutile car déja dans la fonction runMotors

        // Lancement de la fonction mouvement
        moveAxesToAbsolutePositionsUnsynchronized(); // Effectue le mouvement avec les paramètres mis à jour
    }
    else
    {
        //Serial.println("Commande inconnue");
    }
}

// 4.5. Contrôle des moteurs (Couche de contrôle)
void runMotors() 
// Rôle: Contrôle les moteurs en fonction des commandes reçues.
{
    if (movementAllowed == true)
    {
        bool allSteppersStopped = true;
        for (int i = 0; i < 6; i++)
        {
            steppers[i].enableOutputs();

            // Vérifie si une commande d'arrêt a été reçue
            if (stopRequested)
            {
                steppers[i].stop();
                steppers[i].disableOutputs();
                movementAllowed = false;
                allSteppersStopped = true;
            }
            else
            {
                if (steppers[i].distanceToGo() != 0)
                {
                    steppers[i].run();
                    allSteppersStopped = false;
                }
            }
        }

        // Vérifie les nouvelles commandes pendant le mouvement
        receiveCommands();

        if (allSteppersStopped)
        {
            movementAllowed = false;
            // Mise à jour des positions actuelles
            for (int i = 0; i < 6; i++)
            {
                currentAngles[i] = steppers[i].currentPosition() / stepsPerDegree[i];
                steppers[i].disableOutputs();
            }
            // Afficher les positions actuelles
            //Serial.println("Déplacement terminé. Positions actuelles :");
            //for (int i = 0; i < 6; i++)
            //{
                //Serial.print("Axe ");
                //Serial.print(i + 1);
                //Serial.print(": ");
                //Serial.print(currentAngles[i]);
                //Serial.print("° (");
                //Serial.print(steppers[i].currentPosition());
                //Serial.println(" pas)");
            //}
            Serial.println("READY");
        }
    }
    else
    {
        // Les moteurs sont à l'arrêt
        return;
    }
}

// 4.6. Fonctions de mouvement (Couche de mouvement)

void moveAxesToAbsolutePositionsUnsynchronized() 
// Rôle: Déplace les moteurs vers des positions absolues (en pas), sans synchronisation.
{
    // définir les positions cibles en step
    for (int i = 0; i < 6; i++)
    {
        steppers[i].moveTo(targetSteps[i]);
        /*Serial.print("Moteur ");
        Serial.print(i + 1);
        Serial.print(" cible : ");
        Serial.println(targetSteps[i]);*/
    }
    // autoriser les mouvements
    stopRequested = false; // Réinitialise la demande d'arrêt
    movementAllowed = true;     // Autorise le mouvement
}

void moveAxesToAbsolutePositionsSynchronized() 
// Rôle: Déplace les moteurs vers des positions absolues (en pas), de manière synchronisée.
{
    // Calculer les distances à parcourir et les temps correspondants
    long distances[6];  // Distances à parcourir (en pas) pour chaque moteur
    float times[6];     // Temps de mouvement pour chaque moteur
    float maxTime = 0;  // Temps maximal de mouvement pour tous les moteurs

    //Serial.println("Début du déplacement vers les positions cibles :");
    for (int i = 0; i < 6; i++)
    {
        long currentPosition = steppers[i].currentPosition();
        distances[i] = abs(targetSteps[i] - currentPosition); // Distance en pas

        // Calcul du temps pour ce moteur
        float distanceDeg = distances[i] / stepsPerDegree[i]; // Distance en degrés
        float maxSpeed = axisMaxSpeedsDeg[i];                     // Vitesse maximale en degrés/s
        float acceleration = axisMaxAccelerationsDeg[i];          // Accélération en degrés/s^2

        // Calcul du temps en tenant compte de l'accélération (profil trapézoïdal)
        float tAccel = maxSpeed / acceleration; // Temps pour atteindre la vitesse maximale
        float dAccel = 0.5 * acceleration * tAccel * tAccel; // Distance parcourue pendant l'accélération

        float totalTime;

        if (distanceDeg < 2 * dAccel) // Mouvement triangulaire (n'atteint pas la vitesse maximale)
        {
            // Temps total = 2 * sqrt(distance / acceleration)
            totalTime = 2 * sqrt(distanceDeg / acceleration);
        }
        else // Mouvement trapézoïdal
        {
            float dConst = distanceDeg - 2 * dAccel; // Distance à vitesse constante
            float tConst = dConst / maxSpeed;        // Temps à vitesse constante
            totalTime = 2 * tAccel + tConst;
        }

        times[i] = totalTime; // Temps en secondes

        if (times[i] > maxTime)
            maxTime = times[i]; // Trouver le temps maximal

        float targetAngle = targetSteps[i] / stepsPerDegree[i];
        //Serial.print("Axe ");
        //Serial.print(i + 1);
        //Serial.print(" : ");
        //Serial.print(targetAngle);
        //Serial.print("° (");
        //Serial.print(targetSteps[i]);
        //Serial.println(" pas)");
    }

    // Ajuster les vitesses pour synchroniser les mouvements
    for (int i = 0; i < 6; i++)
    {
        float distanceDeg = abs(distances[i]) / stepsPerDegree[i]; // Distance en degrés

        if (distanceDeg == 0)
        {
            steppers[i].setSpeed(0);
            continue;
        }

        float adjustedSpeed = distanceDeg / maxTime;

        if (adjustedSpeed > axisMaxSpeedsDeg[i])
            adjustedSpeed = axisMaxSpeedsDeg[i];

        steppers[i].setMaxSpeed(adjustedSpeed * stepsPerDegree[i]);
        steppers[i].setAcceleration(axisMaxAccelerationsDeg[i] * stepsPerDegree[i]);

        // Maintenant, on peut définir la position cible
        steppers[i].moveTo(targetSteps[i]);
    }

    stopRequested = false; // Réinitialise la demande d'arrêt
    movementAllowed = true;     // Autorise le mouvement
}

void moveAxesToAbsolutePositionsWithTime(float totalTime) 
// Rôle: Déplace les moteurs vers des positions absolues (en pas), de manière synchronisée, avec un temps spécifié.
    // Paramètres: totalTime (temps total de mouvement en secondes)
{
    // Calculer les distances à parcourir
    long distances[6];
    float requiredSpeeds[6];
    bool movePossible = true;

    //Serial.println("Début du déplacement vers les positions cibles avec temps spécifié :");

    for (int i = 0; i < 6; i++)
    {
        long currentPosition = steppers[i].currentPosition();
        distances[i] = targetSteps[i] - currentPosition; // Distance en pas
        float distanceDeg = abs(distances[i]) / stepsPerDegree[i]; // Distance en degrés

        if (distanceDeg == 0)
        {
            requiredSpeeds[i] = 0;
            continue;
        }

        float A_max = axisMaxAccelerationsDeg[i];
        float V_max = axisMaxSpeedsDeg[i];

        // Calcul de la vitesse requise en utilisant l'accélération maximale
        // Pour un profil triangulaire symétrique
        float V_required = (2 * distanceDeg) / totalTime;

        // Vérifier si la vitesse requise dépasse la vitesse maximale autorisée
        if (V_required > V_max)
        {
            movePossible = false;
            //Serial.print("ERROR - Impossible d'atteindre la position de l'axe N°");
            //Serial.print(i + 1);
            //Serial.println(" dans le temps spécifié sans dépasser la vitesse maximale.");
            break;
        }

        requiredSpeeds[i] = V_required;

        float targetAngle = targetSteps[i] / stepsPerDegree[i];
        //Serial.print("Axe ");
        //Serial.print(i + 1);
        //Serial.print(" : ");
        //Serial.print(targetAngle);
        //Serial.print("° (");
        //Serial.print(targetSteps[i]);
        //Serial.println(" pas)");
    }

    if (!movePossible)
    {
        // Annuler le mouvement
        //Serial.println("Le mouvement est annulé.");
        return;
    }

    // Ajuster les vitesses et garder les accélérations maximales avant de définir les positions cibles
    for (int i = 0; i < 6; i++)
    {
        steppers[i].setMaxSpeed(requiredSpeeds[i] * stepsPerDegree[i]);
        steppers[i].setAcceleration(axisMaxAccelerationsDeg[i] * stepsPerDegree[i]);

        // Définir la position cible
        steppers[i].moveTo(targetSteps[i]);
    }

    stopRequested = false; // Réinitialise la demande d'arrêt
    movementAllowed = true;     // Autorise le mouvement
}
