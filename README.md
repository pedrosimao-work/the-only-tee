# The Only Drop

A full-stack Python web app for managing monthly limited product drops, user accounts, archive collections, payment flow planning, fulfillment integration, and launch automation.

## Current Product Model

The Only Drop currently focuses on T-shirts.

The production domain is planned as:

```text
the-only-drop.com
```

The current business rules are:

- One active T-shirt design per month
- One selected shirt color per design
- Multiple sizes per design
- No user-selected color changes
- Availability depends on Printify stock
- At the first second of each new month, the current design becomes archived
- The next scheduled design becomes the active monthly drop
- Previous drops remain visible in the permanent Archive Collection

## Current Status

The project currently includes:

- Flask application factory structure
- Bootstrap-based public layout
- SQLAlchemy database configuration
- Flask-Migrate migrations
- Drop model
- User model
- User registration and login
- Password hashing
- Flask-Login session handling
- Admin-only dashboard
- Admin drop creation form
- Database-powered homepage and archive page
- Development seed command

## Tech Stack

- Python
- Flask
- Jinja2
- Bootstrap
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-Login
- Flask-WTF
- SQLite for local development
- MariaDB planned for production
- PyMySQL for future MariaDB connection

## Planned Integrations

- Printify product and fulfillment integration
- Stripe Checkout hosted payment flow
- Instagram Reel launch automation
- DirectAdmin deployment with MariaDB
- Cron-based monthly drop rotation

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

- Monthly drop lifecycle automation
- MariaDB configuration
- Printify product and fulfillment integration
- Stripe Checkout integration
- Privacy Policy and Terms pages
- Instagram Reel automation on monthly launch
- Launch logging and error handling
- DirectAdmin deployment
- Tests with pytest
- Code quality tools