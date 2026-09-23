"""Endpoints du module Navigation (section 4.2 du cahier des charges)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from config import config
from database import get_db
from services.navigation import calculer_position_du_jour, calculer_distance_et_eta

router = APIRouter(prefix="/api/navigation", tags=["navigation"])


@router.post("/calculer", response_model=schemas.PositionOut)
def calculer_position(db: Session = Depends(get_db)):
    """Déclenche le calcul de la position du jour (NAV-01).

    Se lance aussi automatiquement chaque jour via le scheduler (voir
    services/scheduler.py) — cet endpoint sert surtout à tester sans
    attendre le lendemain.
    """
    return calculer_position_du_jour(db)


@router.get("/positions", response_model=list[schemas.PositionOut])
def lister_positions(db: Session = Depends(get_db)):
    """Historique des positions calculées, la plus récente en premier."""
    return db.query(models.Position).order_by(models.Position.date.desc()).all()


@router.get("/destination", response_model=schemas.DestinationOut)
def obtenir_destination(db: Session = Depends(get_db)):
    """Distance restante et date d'arrivée estimée (NAV-04)."""
    derniere_position = db.query(models.Position).order_by(models.Position.date.desc()).first()
    if derniere_position is None:
        derniere_position = calculer_position_du_jour(db)

    distance_restante, date_arrivee_estimee = calculer_distance_et_eta(derniere_position)

    destination = config["navigation"]["destination"]
    return schemas.DestinationOut(
        nom=destination["nom"],
        x=destination["x"],
        y=destination["y"],
        z=destination["z"],
        distance_restante=distance_restante,
        date_arrivee_estimee=date_arrivee_estimee,
    )
