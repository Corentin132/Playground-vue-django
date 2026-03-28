# Frontend Vue

## Installation

```bash
cd front
npm install
npm run dev
```

Application disponible sur: `http://localhost:5173`

## Configuration API

Par défaut, le front utilise `http://127.0.0.1:8000/api`.

Tu peux surcharger via:

```bash
VITE_API_URL=http://127.0.0.1:8000/api
```

## Routes Front

- `/login`
- `/register`
- `/projects` (liste + création de projet)
- `/projects/:projectId` (liste des tasks + create/update/delete)
