# The Only Tee

A full-stack Python web app for managing limited-edition T-shirt drops, user accounts, archive collections, and future fulfillment integrations.

## Current Status

The project currently includes:

- Flask application factory structure
- Bootstrap-based public layout
- SQLAlchemy database configuration
- Flask-Migrate migrations
- Drop model
- Database-powered homepage and archive page
- Development seed command

## Tech Stack

- Python
- Flask
- Jinja2
- Bootstrap
- Flask-SQLAlchemy
- Flask-Migrate
- SQLite for local development
- MariaDB planned for production
- PyMySQL for future MariaDB connection

## Local Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local `.env` file based on `.env.example`.

Run database migrations:

```bash
flask db upgrade
```

Seed development drop data:

```bash
flask seed-drops
```

Run the app:

```bash
python run.py
```

Open:

```text
http://127.0.0.1:5000
```

## Development Workflow

This project uses a professional GitHub workflow:

```text
Issue → Branch → Code → Commit → Pull Request → Merge → Done
```

## Planned Features

- User registration and login
- Admin dashboard
- Drop lifecycle automation
- Printify API integration
- MariaDB deployment on DirectAdmin
- Stripe Checkout integration
- Tests with pytest
- Code quality tools