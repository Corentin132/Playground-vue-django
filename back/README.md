# Backend Django API

## Installation

```bash
cd back
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

API disponible sur: `http://127.0.0.1:8000/api`

## Routes API

### Auth

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `GET /api/auth/me/`

### Projects

- `GET /api/projects/` (liste des projets de l'utilisateur connecté)
- `POST /api/projects/` (création de projet)
- `GET /api/projects/<project_id>/`
- `PATCH /api/projects/<project_id>/`
- `DELETE /api/projects/<project_id>/`

### Tasks

- `GET /api/projects/<project_id>/tasks/` (liste des tâches d'un projet)
- `POST /api/projects/<project_id>/tasks/` (création de tâche)
- `PATCH /api/projects/<project_id>/tasks/<task_id>/` (update)
- `DELETE /api/projects/<project_id>/tasks/<task_id>/` (suppression)

## Authentification

Ajouter le header JWT sur les routes protégées:

```http
Authorization: Bearer <access_token>
```
