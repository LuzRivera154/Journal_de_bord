"""Endpoints du module Statistiques et capteurs de survie (section 4.3 du
cahier des charges)."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from services.dht22 import enregistrer_lecture_dht22
from services.simulateur import (
    simuler_oxygene,
    simuler_stocks,
    simuler_maintenance,
    simuler_secteurs,
    simuler_occupation,
    simuler_reserves,
)

router = APIRouter(prefix="/api/stats", tags=["statistiques"])


@router.post("/dht22/lire", response_model=list[schemas.MesureOut])
def lire_dht22_maintenant(db: Session = Depends(get_db)):
    """Déclenche une lecture immédiate du DHT22 (STA-01).

    Se lance aussi automatiquement toutes les 15 min via le scheduler (voir
    services/scheduler.py) — cet endpoint sert surtout à tester sans
    attendre le prochain relevé automatique.
    """
    mesure_temperature, mesure_humidite = enregistrer_lecture_dht22(db)
    return [mesure_temperature, mesure_humidite]


@router.post("/simuler", response_model=list[schemas.MesureOut])
def simuler_maintenant(db: Session = Depends(get_db)):
    """Déclenche une génération immédiate des données simulées (STA-02) :
    oxygène, stocks, et (avec une petite chance) une mise en maintenance.

    Se lance aussi automatiquement toutes les 20 min via le scheduler — cet
    endpoint sert surtout à tester sans attendre.
    """
    mesures = simuler_oxygene(db) + simuler_stocks(db) + simuler_secteurs(db) + simuler_occupation(db)
    simuler_maintenance(db)  # pas toujours un résultat, exclu de la réponse
    simuler_reserves(db)  # pas des Mesure, exclu de la réponse (voir /api/reserves/)
    return mesures


@router.get("/secteurs", response_model=list[schemas.SecteurResumeOut])
def resumer_secteurs(db: Session = Depends(get_db)):
    """Dernière valeur de chaque mesure (O2, CO2, température, humidité,
    pression, occupation) par secteur, + "maintenance" si le secteur a une
    maintenance en cours — pour le panneau "Secteurs" du Bord."""

    def derniere_valeur(id_secteur, type_mesure):
        mesure = (
            db.query(models.Mesure)
            .filter_by(id_secteur=id_secteur, type=type_mesure)
            .order_by(models.Mesure.horodatage.desc())
            .first()
        )
        return mesure.valeur if mesure else None

    resultat = []
    for secteur in db.query(models.Secteur).all():
        maintenance_en_cours = (
            db.query(models.Maintenance)
            .filter_by(id_secteur=secteur.id, statut="en_cours")
            .first()
        )
        occupation = derniere_valeur(secteur.id, "occupation")

        resultat.append(schemas.SecteurResumeOut(
            id=secteur.id,
            nom=secteur.nom,
            oxygene=derniere_valeur(secteur.id, "oxygene"),
            co2=derniere_valeur(secteur.id, "co2"),
            temperature=derniere_valeur(secteur.id, "temperature"),
            humidite=derniere_valeur(secteur.id, "humidite"),
            pression=derniere_valeur(secteur.id, "pression"),
            occupation=int(occupation) if occupation is not None else None,
            statut="maintenance" if maintenance_en_cours else "nominal",
        ))
    return resultat


@router.get("/maintenance", response_model=list[schemas.MaintenanceOut])
def lister_maintenance(db: Session = Depends(get_db)):
    """Secteurs en maintenance (en cours ou passés), le plus récent en premier."""
    return db.query(models.Maintenance).order_by(models.Maintenance.debut.desc()).all()


@router.get("/mesures", response_model=list[schemas.MesureOut])
def lister_mesures(type: str | None = None, heures: int | None = None, secteur: str | None = None, db: Session = Depends(get_db)):
    """Historique des mesures, la plus récente en premier.

    Filtrable par type (ex: ?type=temperature), par période (ex: ?heures=24
    pour les dernières 24 heures, pour la courbe du Bord) et par secteur
    (ex: ?secteur=Pont — utile depuis que temperature/humidite sont aussi
    simulées pour les autres secteurs, pour ne pas les mélanger avec le
    vrai capteur DHT22 du Pont)."""
    requete = db.query(models.Mesure)
    if type:
        requete = requete.filter(models.Mesure.type == type)
    if heures:
        requete = requete.filter(models.Mesure.horodatage >= datetime.utcnow() - timedelta(hours=heures))
    if secteur:
        secteur_trouve = db.query(models.Secteur).filter_by(nom=secteur).first()
        id_secteur = secteur_trouve.id if secteur_trouve else -1
        requete = requete.filter(models.Mesure.id_secteur == id_secteur)
    return requete.order_by(models.Mesure.horodatage.desc()).limit(200).all()
