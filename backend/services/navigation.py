"""Calcul de la position du vaisseau par navigation à l'estime (NAV-01).

Position du jour = position de la veille + vitesse * temps écoulé, dans la
direction de la destination (cf. section 6 du cahier des charges).
"""
import math
from datetime import datetime, timedelta

from config import config
from models import Position

NAV_CONFIG = config["navigation"]
DESTINATION = NAV_CONFIG["destination"]


def calculer_position_du_jour(db):
    """Calcule la position du jour à partir de la dernière position connue
    (la veille), l'enregistre dans la table positions, et la retourne."""
    derniere_position = db.query(Position).order_by(Position.date.desc()).first()

    if derniere_position is None:
        # Premier calcul depuis le début de la mission : position de config.yaml
        depart = NAV_CONFIG["position_initiale"]
        x, y, z = depart["x"], depart["y"], depart["z"]
        incertitude_precedente = 0.0
    else:
        x, y, z = derniere_position.x, derniere_position.y, derniere_position.z
        incertitude_precedente = derniere_position.incertitude

    vitesse = NAV_CONFIG["vitesse_defaut"]

    # Vecteur direction vers la destination
    dx = DESTINATION["x"] - x
    dy = DESTINATION["y"] - y
    dz = DESTINATION["z"] - z
    distance_restante = math.sqrt(dx**2 + dy**2 + dz**2)

    if distance_restante > 0:
        pas = min(vitesse, distance_restante)  # ne dépasse pas la destination
        x += dx / distance_restante * pas
        y += dy / distance_restante * pas
        z += dz / distance_restante * pas

    nouvelle_position = Position(
        date=datetime.utcnow(),
        x=x,
        y=y,
        z=z,
        vitesse=vitesse,
        # L'incertitude augmente un peu à chaque calcul par estime seule
        # (pas de recalage stellaire pour l'instant, cf. NAV-02).
        incertitude=incertitude_precedente + 0.5,
        methode="estime",
    )
    db.add(nouvelle_position)
    db.commit()
    db.refresh(nouvelle_position)
    return nouvelle_position


def calculer_distance_et_eta(position):
    """Distance restante jusqu'à la destination, et date d'arrivée estimée
    si le vaisseau continue à la même vitesse (NAV-04)."""
    dx = DESTINATION["x"] - position.x
    dy = DESTINATION["y"] - position.y
    dz = DESTINATION["z"] - position.z
    distance_restante = math.sqrt(dx**2 + dy**2 + dz**2)

    if position.vitesse > 0:
        jours_restants = distance_restante / position.vitesse
        date_arrivee_estimee = position.date + timedelta(days=jours_restants)
    else:
        date_arrivee_estimee = None  # vitesse inconnue : impossible d'estimer

    return distance_restante, date_arrivee_estimee
