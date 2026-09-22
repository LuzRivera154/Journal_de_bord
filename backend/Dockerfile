FROM python:3.11-slim

# Même arborescence qu'en local (backend/ à côté de frontend/, data/, config.yaml)
# pour que les chemins relatifs du code soient identiques dans les deux cas.
WORKDIR /app/backend

# gcc: nécessaire à la compilation de certaines dépendances natives.
# Le binaire astrometry.net (solve-field) n'est PAS installé ici : cette image
# sert le prototype avec le repli OpenCV / résultat simulé (cf. section 13 du
# cahier des charges). Pour le plate-solving réel, ajouter le paquet
# astrometry.net (ou compiler depuis les sources) et copier les fichiers
# d'index dans /app/data/astrometry_index.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
