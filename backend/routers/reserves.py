"""Endpoints du panneau "Réserves et besoins" du Bord.

Les quantités descendent au fil du temps (voir services/simulateur.py,
simuler_reserves) — aucun capteur réel derrière, c'est inventé pour la
démo (voir config.yaml, section "reserves")."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from config import config
from database import get_db

router = APIRouter(prefix="/api/reserves", tags=["reserves"])

RESERVES_CONFIG = config["reserves"]


@router.get("/", response_model=list[schemas.ReserveOut])
def lister_reserves(db: Session = Depends(get_db)):
    """État actuel de chaque réserve, avec le nombre de jours restants au
    rythme de consommation actuel."""
    resultat = []
    for reserve in db.query(models.Reserve).all():
        infos = RESERVES_CONFIG[reserve.type]
        consommation_par_jour = infos["consommation_par_jour"]
        jours_restants = reserve.quantite_actuelle / consommation_par_jour if consommation_par_jour > 0 else 0

        resultat.append(schemas.ReserveOut(
            type=reserve.type,
            libelle=infos["libelle"],
            quantite_actuelle=round(reserve.quantite_actuelle, 1),
            quantite_initiale=infos["quantite_initiale"],
            unite=infos["unite"],
            consommation_par_jour=consommation_par_jour,
            jours_restants=round(jours_restants, 1),
        ))
    return resultat
