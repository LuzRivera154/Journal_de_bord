"""Endpoints du module Statistiques et capteurs de survie (section 4.3 du
cahier des charges)."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from services.dht22 import enregistrer_lecture_dht22

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
