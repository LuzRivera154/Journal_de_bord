"""Vérifie si une mesure dépasse les seuils définis dans config.yaml, et crée
un incident automatiquement si besoin.

C'est ce qui permet à un incident d'être créé "automatiquement" (US-4.3,
critère 1) en plus de la création manuelle par l'équipage. Sert aussi de
base à STA-05 (alerte visible dans l'interface), une autre user story.
"""
from config import config
from models import Incident

SEUILS = config["alerts"]


def verifier_seuil(mesure, db):
    """mesure est une ligne Mesure déjà enregistrée en base (avec son id).
    Retourne l'incident créé, ou None si la valeur est dans la plage normale."""
    hors_plage = False
    message = ""

    if mesure.type == "oxygene" and mesure.valeur < SEUILS["oxygene_min"]:
        hors_plage = True
        message = "Oxygène bas : " + str(mesure.valeur) + mesure.unite

    elif mesure.type == "temperature":
        if mesure.valeur < SEUILS["temperature_min"] or mesure.valeur > SEUILS["temperature_max"]:
            hors_plage = True
            message = "Température hors plage : " + str(mesure.valeur) + mesure.unite

    elif mesure.type == "humidite" and mesure.valeur > SEUILS["humidite_max"]:
        hors_plage = True
        message = "Humidité trop élevée : " + str(mesure.valeur) + mesure.unite

    if not hors_plage:
        return None

    incident = Incident(
        id_secteur=mesure.id_secteur,
        gravite="critique",
        description=message,
        statut="ouvert",
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident
