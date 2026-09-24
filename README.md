# Journal de bord de la navette

Backend du projet "Journal de bord" (workshop Horizon 2080 / ESA — voir
`Cahier des charges Journal de bord de la navette.docx.pdf` pour le détail
complet des besoins).

## 🚀 État actuel

Ce qui fonctionne déjà :

- Connexion à PostgreSQL, les 9 tables (section 8 du cahier des charges)
- Navigation : position du jour, trajet, distance/date d'arrivée
- Statistiques : DHT22 (réel + simulé), simulateurs (oxygène, stocks,
  maintenance), courbes du Bord
- Incidents et maintenance : déclaration, changement de statut, alertes
  automatiques sur seuils dépassés
- Population à bord
- Journal de bord : génération automatique (à heure fixe) et à la demande,
  via Ollama (avec repli sur un texte fixe si Ollama ne répond pas),
  recherche par date exacte ou par plage de dates
- Frontend complet (pages Bord, Navigation, Ciel, Journal, Incidents) dans
  `frontend/`, servi directement par le backend (voir "Démarrer le
  serveur" ci-dessous)

Ce qu'il **reste à faire** : Observation stellaire (capture + analyse
astrometry.net), Assistant (le frontend existe déjà dans
`frontend/assistant.html`, il manque le endpoint `POST /api/assistant/...`
côté backend).

## 📋 Prérequis

Le projet tourne pareil sous Windows et sous Linux : la base de données et
Ollama sont dans des conteneurs Docker (identiques quel que soit l'OS), et
Python/FastAPI sont multiplateformes. Seules les commandes d'installation
changent.

- **Python 3.12** :
  - Windows : [téléchargement direct (64 bits)](https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe). Pendant l'installation, cocher "Add python.exe to PATH".
  - Linux : `sudo apt install python3 python3-venv python3-pip` (Debian/Ubuntu), ou l'équivalent de votre distribution.
- **Docker** :
  - Windows : [Docker Desktop](https://www.docker.com/products/docker-desktop/) (avec WSL2).
  - Linux : [Docker Engine](https://docs.docker.com/engine/install/) (paquet natif de votre distribution, pas besoin de "Desktop").
- Git

Vérifier que tout est bien installé :

```bash
python3 --version   # ou "python --version" sous Windows — doit afficher Python 3.12.x
docker --version
docker compose version
```

## ⚙️ Installation

```bash
# 1. Cloner le dépôt (si ce n'est pas déjà fait)
git clone <url-du-depot>
cd Journal_de_bord

# 2. Créer le fichier .env (jamais commité, voir .env.example)
cp .env.example .env

# 3. Démarrer la base de données (sous Windows : Docker Desktop doit être ouvert)
docker compose up -d db

# 4. Créer l'environnement virtuel et installer les dépendances
# IMPORTANT : bien être dans backend/ à ce stade (donc juste après le "cd backend"
# ci-dessus), sinon le venv se crée au mauvais endroit et rien ne fonctionne ensuite.
cd backend
python3 -m venv venv          # sous Windows : python -m venv venv

source venv/bin/activate      # sous Windows : venv\Scripts\activate

pip install -r requirements.txt
```

## ▶️ Démarrer le serveur

```bash
# Depuis backend/, avec l'environnement virtuel activé
uvicorn main:app --reload
```

Si tout s'est bien passé, le dernier message ressemble à
`Uvicorn running on http://127.0.0.1:8000`.

### 🐳 Alternative : tout lancer via Docker (sans venv)

Au lieu des étapes ci-dessus, on peut aussi construire et lancer le backend
comme un conteneur (pratique pour tester "à froid", ou si le venv pose
problème) :

```bash
docker compose up -d --build backend
```

**Important** : `backend/` est copié dans l'image au moment du build (pas
un volume monté en direct) — donc après **chaque** changement de code
Python, il faut relancer cette commande pour que le conteneur prenne le
changement en compte. `frontend/`, lui, est monté en direct : pas besoin de
rebuild pour un changement HTML/CSS/JS.

### 🤖 Ollama (génération du journal par IA)

Le premier démarrage d'Ollama n'a pas encore de modèle téléchargé — sans
cette étape, la génération de journal utilise toujours le texte de repli
(NFR "Résilience", donc ça ne plante pas, mais il vaut mieux tester avec la
vraie IA) :

```bash
docker exec journal-ollama ollama pull qwen2.5:3b
```

## 🧪 Comment tester

Ouvrir **http://localhost:8000/** dans le navigateur pour voir le
frontend (page Bord, avec le menu à gauche vers les autres pages).

Pour tester l'API directement, ouvrir **http://localhost:8000/docs** —
c'est l'interface générée automatiquement par FastAPI : chaque endpoint
peut être testé en un clic, sans avoir besoin de Postman.

Tester dans l'ordre :

1. **GET `/api/health`** → doit renvoyer `{"status": "ok"}`. Si ça marche,
   le serveur a bien démarré.
2. **GET `/api/secteurs`** → doit renvoyer une liste de 5 secteurs (Pont,
   Serre, Dortoirs, Machinerie, Laboratoire). Si ça marche, la connexion à
   PostgreSQL et la création des tables fonctionnent.

Si l'étape 2 échoue mais que l'étape 1 a marché, le problème vient de la
connexion à la base — voir Dépannage ci-dessous.

## 🗄️ Voir les tables de la base de données

Il y a **Adminer** (équivalent de phpMyAdmin, mais pour PostgreSQL) inclus
dans le `docker-compose.yml`. Pratique pour voir les tables et les données
sans taper de SQL à la main.

```bash
docker compose up -d adminer
```

Puis ouvrir **http://localhost:8080** et se connecter avec :

| Champ | Valeur |
|---|---|
| Système | PostgreSQL |
| Serveur | `db` (pas `localhost` — c'est le nom du service Docker) |
| Utilisateur | valeur de `POSTGRES_USER` dans votre `.env` |
| Mot de passe | valeur de `POSTGRES_PASSWORD` dans votre `.env` |
| Base de données | valeur de `POSTGRES_DB` dans votre `.env` |

## 🛑 Tout arrêter

```bash
docker compose down
```

(Les données de Postgres restent dans un volume Docker, elles ne sont pas
perdues avec `down`. Pour tout effacer : `docker compose down -v`.)

## 📁 Structure du projet

```
Journal_de_bord/
├── config.yaml              # toute la configuration ajustable (rien en dur)
├── docker-compose.yml       # services : db (Postgres), backend, ollama, adminer
├── data/                    # images capturées, index astrometry.net (non versionné)
├── frontend/                # pages HTML/CSS/JS, servies par le backend (pas de build)
│   ├── css/style.css
│   └── js/                  # un fichier par page + sidebar.js (menu commun)
└── backend/
    ├── main.py              # démarrage de l'app + endpoints de test
    ├── config.py            # lecture de config.yaml
    ├── database.py          # connexion à Postgres
    ├── models.py            # les 9 tables (section 8 du cahier des charges)
    ├── schemas.py           # format d'entrée/sortie de l'API
    ├── routers/              # ICI va chaque module (un fichier par module)
    └── services/             # ICI va la logique de chaque module
```

## 🔧 Dépannage

| Problème | Cause probable |
|---|---|
| `docker compose up -d db` ne fait rien / erreur de connexion | Sous Windows : Docker Desktop n'est pas ouvert. Sous Linux : le service Docker n'est pas démarré (`sudo systemctl start docker`) |
| `python --version` ouvre le Microsoft Store (Windows) | Python n'est pas vraiment installé, réinstaller depuis le lien ci-dessus |
| `pip install` échoue | Vérifier que l'environnement virtuel est activé (le prompt doit commencer par `(venv)`) |
| `/api/secteurs` renvoie une erreur de connexion à la base | Lancer `docker ps` et vérifier que le conteneur `journal-db` est `healthy` (peut prendre ~10s à démarrer) |
| `RuntimeError: DATABASE_URL manquant` au lancement de `uvicorn` | Le fichier `.env` n'existe pas encore : `cp .env.example .env` à la racine du projet |
| `uvicorn : le terme n'est pas reconnu` alors que `(venv)` est affiché | Le venv a été créé au mauvais endroit (à la racine au lieu de `backend/`). Supprimer ce venv vide, puis refaire `cd backend` avant `python -m venv venv` |
| Une commande marche puis, après un `pip install` ou une install (Python, Docker...), la même commande "n'est pas reconnue" | Le PATH est resté en mémoire depuis avant l'installation. Fermer complètement le terminal (voire VS Code) et en rouvrir un nouveau |
| Le journal généré dit "modèle de langage indisponible" (texte de repli) alors qu'Ollama tourne | Le modèle n'a pas encore été téléchargé : `docker exec journal-ollama ollama pull qwen2.5:3b` (une seule fois, ~2 Go, peut prendre plusieurs minutes) |
| Un changement dans `backend/` (routers, services, models...) ne se voit pas dans le navigateur | Si le backend tourne dans Docker, il faut le reconstruire après chaque changement Python : `docker compose up -d --build backend`. Un changement dans `frontend/` n'a pas besoin de ça (juste rafraîchir la page) |
