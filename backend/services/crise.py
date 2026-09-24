"""Scénario de crise pour la démo (Épic 7) : dépressurisation + perte de la
caméra, déclenché à la main depuis un bouton dans l'entête.

Le seul état qui compte est en base (table crises) : y a-t-il une ligne
sans date de fin ? Ça évite un drapeau en mémoire qui se perdrait à chaque
redémarrage du serveur, et ça permet au module Journal de savoir si une
crise vient de se terminer, pour la résumer une seule fois (US Épic 7,
critère 4)."""
from datetime import datetime

from models import Crise, Incident


def crise_active(db):
    """La crise en cours (ligne sans date de fin), s'il y en a une."""
    return db.query(Crise).filter(Crise.fin.is_(None)).order_by(Crise.debut.desc()).first()


def activer_crise(db):
    """Déclenche le scénario : crée l'incident automatiquement (critère 1)
    et ouvre l'épisode de crise. Si une crise est déjà en cours, ne fait
    rien de plus (pas de doublon)."""
    existante = crise_active(db)
    if existante:
        return existante

    incident = Incident(
        gravite="critique",
        description="Scénario de crise simulé : dépressurisation détectée et caméra d'observation indisponible.",
        statut="ouvert",
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    crise = Crise(debut=datetime.utcnow(), id_incident=incident.id)
    db.add(crise)
    db.commit()
    db.refresh(crise)
    return crise


def desactiver_crise(db):
    """Termine l'épisode en cours (s'il y en a un) et résout l'incident
    associé."""
    crise = crise_active(db)
    if crise is None:
        return None

    crise.fin = datetime.utcnow()

    if crise.id_incident:
        incident = db.query(Incident).filter_by(id=crise.id_incident).first()
        if incident:
            incident.statut = "resolu"

    db.commit()
    db.refresh(crise)
    return crise
