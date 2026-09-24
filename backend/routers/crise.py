"""Endpoints du scénario de crise pour la démo (Épic 7)."""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import schemas
from database import get_db
from services.crise import activer_crise, desactiver_crise, crise_active

router = APIRouter(prefix="/api/crise", tags=["crise"])


@router.get("/", response_model=Optional[schemas.CriseOut])
def obtenir_etat(db: Session = Depends(get_db)):
    """État actuel : la crise en cours, ou null si tout va bien."""
    return crise_active(db)


@router.post("/activer", response_model=schemas.CriseOut)
def activer(db: Session = Depends(get_db)):
    """Bouton "Simuler une crise" de l'entête."""
    return activer_crise(db)


@router.post("/desactiver", response_model=Optional[schemas.CriseOut])
def desactiver(db: Session = Depends(get_db)):
    """Bouton "Arrêter la simulation" de l'entête. Renvoie null s'il n'y
    avait déjà aucune crise à terminer (bouton cliqué deux fois, deux
    onglets ouverts...) plutôt que planter."""
    return desactiver_crise(db)
