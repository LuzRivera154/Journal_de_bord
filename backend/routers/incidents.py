"""Endpoints du module Incidents (section 4.3 du cahier des charges)."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.post("/", response_model=schemas.IncidentOut)
def declarer_incident(donnee: schemas.IncidentIn, db: Session = Depends(get_db)):
    """Un membre de l'équipage déclare un incident à la main (US-4.3, critère 1)."""
    id_secteur = None
    if donnee.secteur:
        secteur = db.query(models.Secteur).filter_by(nom=donnee.secteur).first()
        if secteur:
            id_secteur = secteur.id

    incident = models.Incident(
        id_secteur=id_secteur,
        gravite=donnee.gravite,
        description=donnee.description,
        statut=donnee.statut,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


@router.get("/", response_model=list[schemas.IncidentOut])
def lister_incidents(
    secteur: str | None = None,
    date: str | None = None,
    statut: str | None = None,
    db: Session = Depends(get_db),
):
    """Historique des incidents, le plus récent en premier.

    Filtrable par secteur (ex: ?secteur=Pont), par jour exact
    (ex: ?date=2026-09-24) — US-4.3, critère 3 — et par statut
    (ex: ?statut=ouvert, pour les alertes en cours — US-4.5, critère 2)."""
    requete = db.query(models.Incident)

    if secteur:
        secteur_trouve = db.query(models.Secteur).filter_by(nom=secteur).first()
        id_secteur = secteur_trouve.id if secteur_trouve else -1  # -1 : aucun résultat
        requete = requete.filter(models.Incident.id_secteur == id_secteur)

    if date:
        debut_jour = datetime.strptime(date, "%Y-%m-%d")
        fin_jour = debut_jour + timedelta(days=1)
        requete = requete.filter(models.Incident.horodatage >= debut_jour, models.Incident.horodatage < fin_jour)

    if statut:
        requete = requete.filter(models.Incident.statut == statut)

    return requete.order_by(models.Incident.horodatage.desc()).all()
