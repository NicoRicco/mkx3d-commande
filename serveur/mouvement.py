"""Modèle de mouvement : reproduit le calcul du firmware (AccelStepper).

Sans encodeur, le PC ne reçoit pas la position réelle du bras pendant un
mouvement. On l'estime donc en rejouant les mêmes profils de vitesse
trapézoïdaux que le firmware.
"""

import math

from config import ACCELERATIONS_MAX, NB_AXES, VITESSES_MAX


def duree_trapeze(distance, vitesse, accel):
    """Durée d'un mouvement trapézoïdal (ou triangulaire si trop court)."""
    if distance <= 0 or vitesse <= 0 or accel <= 0:
        return 0.0
    if distance < vitesse * vitesse / accel:
        return 2.0 * math.sqrt(distance / accel)
    return distance / vitesse + vitesse / accel


def position_trapeze(distance, vitesse, accel, t):
    """Distance parcourue au temps t sur un profil trapézoïdal."""
    if distance <= 0 or vitesse <= 0 or accel <= 0:
        return distance
    if distance < vitesse * vitesse / accel:
        ta = math.sqrt(distance / accel)
        vitesse = accel * ta
        tc = 0.0
    else:
        ta = vitesse / accel
        tc = distance / vitesse - ta
    total = 2 * ta + tc
    if t <= 0:
        return 0.0
    if t >= total:
        return distance
    if t < ta:
        return 0.5 * accel * t * t
    d_acc = 0.5 * accel * ta * ta
    if t < ta + tc:
        return d_acc + vitesse * (t - ta)
    tr = total - t
    return distance - 0.5 * accel * tr * tr


class Plan:
    """Mouvement planifié de q_debut vers q_fin, avec un profil par axe."""

    def __init__(self, q_debut, q_fin, profils):
        self.q_debut = list(q_debut)
        self.q_fin = list(q_fin)
        self.profils = profils  # liste de (vitesse, accel) par axe
        self.duree = max(
            duree_trapeze(abs(q_fin[i] - q_debut[i]), v, a)
            for i, (v, a) in enumerate(profils)
        ) if profils else 0.0

    def position(self, t):
        q = []
        for i in range(NB_AXES):
            d = self.q_fin[i] - self.q_debut[i]
            v, a = self.profils[i]
            s = position_trapeze(abs(d), v, a, t)
            q.append(self.q_debut[i] + math.copysign(s, d))
        return q


def plan_synchronise(q_debut, q_fin):
    """Commande A : tous les axes arrivent à peu près ensemble (firmware)."""
    temps = [
        duree_trapeze(abs(q_fin[i] - q_debut[i]), VITESSES_MAX[i], ACCELERATIONS_MAX[i])
        for i in range(NB_AXES)
    ]
    t_max = max(temps)
    profils = []
    for i in range(NB_AXES):
        d = abs(q_fin[i] - q_debut[i])
        v = min(d / t_max, VITESSES_MAX[i]) if t_max > 0 and d > 0 else VITESSES_MAX[i]
        profils.append((v, ACCELERATIONS_MAX[i]))
    return Plan(q_debut, q_fin, profils)


def plan_avec_duree(q_debut, q_fin, duree):
    """Commande AT : renvoie (plan, None) ou (None, message d'erreur).

    Le firmware annule silencieusement le mouvement si un axe dépasse sa
    vitesse max ; on fait la même vérification avant d'envoyer.
    """
    if duree <= 0:
        return None, "La durée doit être positive."
    profils = []
    for i in range(NB_AXES):
        d = abs(q_fin[i] - q_debut[i])
        v = 2 * d / duree
        if v > VITESSES_MAX[i]:
            t_min = 2 * d / VITESSES_MAX[i]
            return None, (f"Axe {i + 1} : mouvement impossible en {duree:.1f} s sans dépasser "
                          f"sa vitesse max (minimum {t_min:.1f} s).")
        profils.append((v if d > 0 else VITESSES_MAX[i], ACCELERATIONS_MAX[i]))
    return Plan(q_debut, q_fin, profils), None
