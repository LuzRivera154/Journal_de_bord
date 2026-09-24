"""Endpoints du module Statistiques et capteurs de survie (section 4.3 du
cahier des charges)."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from services.dht22 import enregistrer_lecture_dht22
from services.simulateur import simuler_oxygene, simuler_stocks, simuler_maintenance

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
    mesures = simuler_oxygene(db) + simuler_stocks(db)
    simuler_maintenance(db)  # pas toujours un résultat, exclu de la réponse
    return mesures


@router.get("/maintenance", response_model=list[schemas.MaintenanceOut])
def lister_maintenance(db: Session = Depends(get_db)):
    """Secteurs en maintenance (en cours ou passés), le plus récent en premier."""
    return db.query(models.Maintenance).order_by(models.Maintenance.debut.desc()).all()


@router.get("/mesures", response_model=list[schemas.MesureOut])
def lister_mesures(type: str | None = None, heures: int | None = None, db: Session = Depends(get_db)):
    """Historique des mesures, la plus récente en premier.

    Filtrable par type (ex: ?type=temperature) et par période
    (ex: ?heures=24 pour les dernières 24 heures, pour la courbe du Bord)."""
    requete = db.query(models.Mesure)
    if type:
        requete = requete.filter(models.Mesure.type == type)
    if heures:
        requete = requete.filter(models.Mesure.horodatage >= datetime.utcnow() - timedelta(hours=heures))
    return requete.order_by(models.Mesure.horodatage.desc()).limit(200).all()
