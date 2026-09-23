"""Endpoints du module Navigation (section 4.2 du cahier des charges)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db
from services.navigation import calculer_position_du_jour

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
