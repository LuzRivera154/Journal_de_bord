"""Lecture du fichier config.yaml (à la racine du projet).

Toute la config du projet est dans ce fichier unique pour ne pas avoir
de valeurs en dur dispersées dans le code.
"""
import os
import yaml
from dotenv import load_dotenv

# On lance toujours uvicorn depuis le dossier backend/ (en local comme dans
# Docker), donc config.yaml et .env sont toujours un dossier au-dessus.
load_dotenv("../.env")  # en local uniquement : dans Docker, DATABASE_URL est déjà fourni

CONFIG_PATH = os.environ.get("CONFIG_PATH", "../config.yaml")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)


def get_database_url():
    # Dans Docker, docker-compose.yml fournit déjà l'URL complète.
    url = os.environ.get("DATABASE_URL")
    if url:
        return url

    # En local (hors conteneur), on la reconstruit à partir de .env
    # (Postgres est exposé sur localhost:5432 par docker-compose.yml).
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    db_name = os.environ.get("POSTGRES_DB")
    if user and password and db_name:
        return f"postgresql+psycopg2://{user}:{password}@localhost:5432/{db_name}"

    raise RuntimeError(
        "Configuration de la base de données manquante. Copier .env.example "
        "vers .env (à la racine du projet) et le compléter."
    )
