# 🚀 PrimeBank Backend API

Backend Django + Django REST Framework pour le projet PrimeBank. API sécurisée, documentée (Swagger), avec des règles strictes de qualité, sécurité et maintenabilité.

---

## 🧱 Stack technique

- 🐍 **Python 3.11+**
- 🌐 **Django 5.x**
- 🔌 **Django REST Framework**
- 🔐 **JWT** (SimpleJWT)
- 📘 **OpenAPI / Swagger** (drf-spectacular)
- 🧹 **Black / isort / Flake8**
- 🔐 **Bandit** (sécurité)
- 🤖 **GitHub Actions** (CI)
- 🪝 **pre-commit** (qualité locale)

---

## 📁 Structure du projet

```
PrimeBank_Backend/
├── src/
│   └── primeBank/
│       ├── settings.py
│       ├── urls.py
│       ├── views.py
│       └── ...
├── .github/workflows/
│   └── quality.yml
├── .pre-commit-config.yaml
├── pyproject.toml
├── .flake8
├── .bandit
├── requirements.txt
└── README.md
```

---

## ⚙️ Prérequis

- Python 3.11 ou supérieur
- pip
- virtualenv (recommandé)
- Git

---

## 🛠️ Installation & démarrage

### 1️⃣ Cloner le projet

```bash
git clone https://github.com/your-org/primebank-backend.git
cd PrimeBank_Backend
```

---

### 2️⃣ Créer et activer un environnement virtuel

```bash
python -m venv .venv
source .venv/bin/activate  # macOS / Linux
# .venv\Scripts\activate   # Windows
```

---

### 3️⃣ Installer les dépendances

```bash
pip install -r requirements.txt
```

---

### 4️⃣ Variables d'environnement

Créer un fichier `.env` (local uniquement) :

```env
SECRET_KEY=django-insecure-local
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

⚠️ **Ne jamais commit le `.env`**

En CI / production, les variables sont injectées via l'environnement (GitHub Environments, Docker, cloud).

---

### 5️⃣ Lancer le serveur

```bash
cd src
python manage.py migrate
python manage.py runserver
```

---

### 6️⃣ Vérifier que tout fonctionne

- **Health check** : 👉 http://127.0.0.1:8000/
- **Admin Django** : 👉 http://127.0.0.1:8000/admin/
- **Swagger UI** : 👉 http://127.0.0.1:8000/api/docs/

---

## 🔐 Authentification (JWT)

### Obtenir un token

```http
POST /api/token/
{
  "username": "admin",
  "password": "password"
}
```

### Rafraîchir un token

```http
POST /api/token/refresh/
```

---

## 📘 Documentation API

- **OpenAPI (JSON)** : `/api/schema/`
- **Swagger UI** : `/api/docs/`
- **ReDoc** : `/api/redoc/`

Swagger supporte JWT (Bearer Token).

---

## 🧹 Qualité de code (OBLIGATOIRE)

Ce projet applique des règles strictes de qualité.

### 🛠️ Outils utilisés

| Outil      | Rôle                              |
|------------|-----------------------------------|
| Black      | Formatage automatique             |
| isort      | Ordre des imports                 |
| Flake8     | PEP8, nommage, complexité         |
| Bandit     | Sécurité                          |
| pre-commit | Blocage avant commit              |
| GitHub Actions | Blocage avant merge           |

---

### ▶️ Lancer les checks en local

```bash
black src
isort src
flake8 src
bandit -r src
```

Ou tout d'un coup :

```bash
pre-commit run --all-files
```

---

## 🧠 Conventions & règles à respecter

### 📐 Style & formatage

- **Black** est la source de vérité
- longueur de ligne : **88 caractères**
- aucun débat sur le format

### 🏷️ Nommage

- fichiers & variables : `snake_case`
- classes : `PascalCase`
- constantes : `UPPER_CASE`
- URLs : `kebab-case`

### 🧠 Complexité

- complexité maximale par fonction : **10**
- une fonction = une responsabilité

### 🔐 Sécurité

- aucune clé ou secret en dur
- pas de `eval`, `exec`
- **Bandit** doit toujours passer

---

## 🪝 pre-commit (OBLIGATOIRE)

Activer une seule fois :

```bash
pre-commit install
```

👉 À chaque `git commit`, les règles sont automatiquement vérifiées.

👉 Si un hook échoue, le commit est bloqué.

---

## 🤖 CI / GitHub Actions

À chaque `push` ou `pull_request` :

- formatage
- lint
- sécurité

❌ **CI rouge = merge interdit**

---

## 🚫 Règles d'équipe

- ❌ pas de `--no-verify`
- ❌ pas de merge sans CI vert
- ❌ pas de secrets dans le repo
- ✅ code lisible
- ✅ règles automatisées
- ✅ discipline collective

---

## 🧪 Prochaines évolutions possibles

- tests (pytest)
- couverture de code
- typage (mypy + django-stubs)
- Docker
- déploiement CI/CD

---

## 🏁 Conclusion

Ce projet suit des standards professionnels :

- qualité imposée par la machine
- sécurité intégrée
- documentation automatique
- prêt pour le travail en équipe et la production

---

👉 **Si tu veux, je peux aussi te fournir :**

- `CONTRIBUTING.md`
- template de PR
- roadmap technique
- checklist de release

**Dis-moi** 👌