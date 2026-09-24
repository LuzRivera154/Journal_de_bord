"""Connaît l'effectif actuel à bord (section 4.3 du cahier des charges).

Deux sources possibles, choisies dans config.yaml (section "population") :
- "simulee" : un nombre généré ici, au hasard dans une plage raisonnable.
- "reelle" : envoyée par un autre projet de l'équipe (la caméra à
  reconnaissance faciale), qui appelle POST /api/population.
"""
import random

from config import config
from models import Population

POPULATION_CONFIG = config["population"]


def simuler_population(db):
    """Génère un effectif simulé, seulement si c'est la source configurée."""
    if POPULATION_CONFIG["source"] != "simulee":
        return None

    population = Population(
        nombre_personnes=random.randint(POPULATION_CONFIG["simulee_min"], POPULATION_CONFIG["simulee_max"]),
        source="simulee",
    )
    db.add(population)
    db.commit()
    db.refresh(population)
    return population


def enregistrer_population_reelle(db, nombre_personnes):
    """Enregistre un effectif envoyé par un système externe (ex: la caméra)."""
    population = Population(
        nombre_personnes=nombre_personnes,
        source="reelle",
    )
    db.add(population)
    db.commit()
    db.refresh(population)
    return population
