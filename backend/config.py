"""Lecture du fichier config.yaml (à la racine du projet).

Toute la config du projet est dans ce fichier unique pour ne pas avoir
de valeurs en dur dispersées dans le code.
"""
import os
import yaml

# On lance toujours uvicorn depuis le dossier backend/ (en local comme dans
# Docker), donc config.yaml est toujours un dossier au-dessus.
CONFIG_PATH = os.environ.get("CONFIG_PATH", "../config.yaml")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)


def get_database_url():
    # docker-compose surcharge avec DATABASE_URL (hôte "db" au lieu de "localhost")
    return os.environ.get("DATABASE_URL", config["database"]["url"])
