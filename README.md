# Projet ESP32 - Interface Web

Ce projet contient une interface Flask pour communiquer avec un ESP32, afficher des logs, stocker des snapshots et des télémétries.

## Objectifs
- Recevoir des payloads JSON depuis l'ESP32
- Enregistrer des snapshots bruts et des enregistrements structurés dans une base SQLite
- Fournir des pages web pour visualiser commandes, payloads et images

## Prérequis
- Python 3.8+ installé
- (Optionnel mais recommandé) Utiliser un environnement virtuel

## Installation (rapide)
1. Ouvrir un terminal dans le dossier du projet (même dossier que `app.py`).
2. Créer et activer un environnement virtuel (Windows) :

```powershell
python -m venv venv
venv\Scripts\activate
```

3. Installer les dépendances :

```powershell
pip install -r requirements.txt
```

> Remarque : `sqlite3` est inclus avec Python, pas besoin d'installation supplémentaire.

## Lancer l'application

```powershell
python app.py
```

L'application écoute par défaut sur `http://0.0.0.0:5000`.

## Endpoints utiles
- `GET /` — page principale
- `GET /cmd` — page commandes et logs
- `POST /data` — point d'entrée des payloads ESP32 (JSON)
- `GET /logs` — obtenir les derniers logs (JSON)
- `GET /telemetry` — obtenir les derniers éléments de télémétrie (JSON)
- `GET /commands` — obtenir les commandes enregistrées (JSON)

Exemple POST (curl) :

```bash
curl -X POST http://localhost:5000/data -H "Content-Type: application/json" -d '{"status":1, "latitude":48.85, "longitude":2.35}'
```

## Base de données
- Fichier SQLite : `data.db` (à la racine du projet)
- Tables principales créées via SQLAlchemy : `logs`, `commands`, `telemetry`, `images`
- La table `esp32_snapshots` contient les snapshots bruts (JSON) — conservée pour compatibilité

Voir les données :
- Ouvrir `data.db` avec VS Code (extension SQLite) ou avec DB Browser for SQLite.
- Dans VS Code : palette → `SQLite: Open Database` → sélectionner `data.db` → exécuter des requêtes SQL.

Requêtes utiles :

```sql
-- lister les tables
SELECT name FROM sqlite_master WHERE type='table';

-- voir les derniers logs
SELECT * FROM logs ORDER BY timestamp DESC LIMIT 20;

-- voir les dernières données de télémétrie de la clé 'temp'
SELECT * FROM telemetry WHERE key = 'temp' ORDER BY timestamp DESC LIMIT 50;
```

## Structure du projet
- `app.py` — serveur Flask principal
- `models.py` — modèles SQLAlchemy
- `templates/` — pages HTML
- `static/` — fichiers statiques (js, css, images)
- `data.db` — base SQLite
- `requirements.txt` — dépendances Python

## Conseils VS Code
- Sélectionner l'interpréteur Python (Ctrl+Shift+P → `Python: Select Interpreter`) pour utiliser l'environnement virtuel.
- Installer l'extension **SQLite** pour naviguer et exécuter des requêtes directement depuis VS Code.

## Prochaines améliorations possibles
- Ajouter `Flask-Migrate` pour gérer les migrations de schéma
- Interface admin pour filtrer/exporter logs (CSV)
- Authentification pour protéger les pages d'administration

## Licence / Contact
Indiquez ici la licence du projet et une adresse de contact si besoin.
