# Hangarin Task & To-Do Manager

This repository contains a Django implementation of the Hangarin assignment from the provided PDF. It models tasks, priorities, categories, notes, and subtasks, and includes admin configuration plus a seed command for fake data generation.

## Implemented requirements

- `BaseModel` abstract model with `created_at` and `updated_at`
- `__str__` methods for every model
- Status enums for `Task` and `SubTask`
- Admin filters/search/list displays as specified
- Corrected admin plurals for `Category` and `Priority`
- Fake data generator for `Task`, `Note`, and `SubTask`
- Default records for `Priority` and `Category`
- **Progressive Web App (PWA)** support with custom installation prompt
- Local virtual environment prepared in `.venv_ssp`
- Git repository initialized in the project root

## Project structure

- `config/` Django project settings and URLs
- `hangarin/` app with models, admin, tests, and management command
- `staticfiles/` gathered static assets including PWA icons

## Progressive Web App (PWA)

Hangarin is a fully featured PWA, allowing you to install it as a standalone app on your desktop or mobile device. Key features include:

- **Offline Support**: Proactive caching of core CSS and branding assets ensuring the dashboard remains accessible without an internet connection.
- **Install App Button**: A custom installation trigger is integrated directly into the dashboard sidebar.
- **App Fidelity**: Standalone display mode with custom icons (192px/512px) and professional theme colors.

## Local setup

Activate the prepared virtual environment:

```powershell
.\.venv_ssp\Scripts\Activate.ps1
```

Install requirements:

```powershell
pip install -r requirements.txt
```

Apply migrations:

```powershell
python manage.py migrate
```

Create an admin user:

```powershell
python manage.py createsuperuser
```

Seed the database (Optional):

```powershell
python manage.py seed_hangarin --tasks 15 --notes-per-task 2 --subtasks-per-task 3
```

Run the development server:

```powershell
python manage.py runserver 9000
```

Open `http://127.0.0.1:9000/` for the Bootstrap dashboard. Use `http://127.0.0.1:9000/admin/` for Django admin.

## PythonAnywhere deployment notes

1. Create a Python 3.12 web app in PythonAnywhere.
2. Upload this project and create a virtual environment on PythonAnywhere.
3. Install the dependencies from `requirements.txt`.
4. Set the WSGI file to point to this project directory and `config.settings`.
5. Run:

```powershell
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py seed_hangarin
```

`ALLOWED_HOSTS` already accepts `.pythonanywhere.com` by default.

## Social sign-in setup

Google and GitHub OAuth support are available. Update your environment variables or a `.env` file to enable them.

To enable it on a deployed server, set:

```text
DJANGO_ENABLE_SOCIAL_LOGIN=True
```

Callback URIs should follow this format:
- Google: `https://your-domain/accounts/google/login/callback/`
- GitHub: `https://your-domain/accounts/github/login/callback/`
