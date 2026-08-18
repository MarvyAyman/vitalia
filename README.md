# Vitalia / MedQuiz — Django Full-Stack Application

A Django-based academic quiz portal with protected access and a responsive web interface.

## Demo

- **Live demo:** [https://vitalia-three.vercel.app/quiz/login](https://vitalia-three.vercel.app/quiz/login)

- **Repository:** [https://github.com/MarvyAyman/vitalia](https://github.com/MarvyAyman/vitalia)

## Features

- Protected login flow for academic portal access.

- Django application structure with database migration workflow.

- Responsive frontend built with HTML, CSS, and JavaScript.

- Static-file collection and deployment configuration.

- Production-oriented dependencies, including Gunicorn, WhiteNoise, and PostgreSQL integration.

## Technology

- Python

- Django

- Django REST Framework

- HTML

- CSS

- JavaScript

- PostgreSQL integration

- Gunicorn

- WhiteNoise

## My Contribution

I built the application structure, backend workflow, login experience, frontend interface, and deployment configuration.

> Before publishing this README, update this section so it reflects only the parts you personally implemented.

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/MarvyAyman/vitalia.git
cd vitalia
```

### 2. Create and activate a virtual environment

#### macOS / Linux

```bash
python -m venv venv
source venv/bin/activate
```

#### Windows PowerShell

```
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Start the development server

```bash
python manage.py runserver
```

Open the local application at:

[http://127.0.0.1:8000/](http://127.0.0.1:8000/)


## Security Notes

- Do not commit passwords, secret keys, database URLs, or other credentials.

- Do not publish private client data, private question banks, or real student information.

- Use environment variables for production secrets.

- Use a separate demo account and synthetic data for public demonstrations.
