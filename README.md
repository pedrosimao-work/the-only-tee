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

Run monthly drop lifecycle automation manually:

```bash
flask rotate-drops
```

This command archives expired active drops and activates the next scheduled draft drop when its start date has arrived.

In production, this command is intended to run through a DirectAdmin cron job at the first second of the first day of each month.

Run the app:

```bash
python run.py
```

Open:

```text
http://127.0.0.1:5000
```

## Database Configuration

The app uses environment-based database configuration.

For local development, the default fallback is SQLite:

```text
sqlite:///the_only_drop.db
```

For production, the app is prepared for MariaDB using PyMySQL:

```text
mysql+pymysql://database_user:database_password@localhost/database_name
```

Real database credentials must be stored in environment variables and must never be committed to Git.

You can safely inspect the active database configuration with:

```bash
flask db-info
```

This command shows the database driver, host, and database name while hiding the password.

### DirectAdmin MariaDB Notes

When preparing the production deployment, create a MariaDB database and database user inside DirectAdmin.

Then set the production `DATABASE_URL` using this format:

```text
mysql+pymysql://database_user:database_password@localhost/database_name
```

If the password contains special characters, URL-encode the password before placing it inside `DATABASE_URL`.

Example:

```text
@ becomes %40
# becomes %23
/ becomes %2F
: becomes %3A
```

The production database setup will be completed during the DirectAdmin deployment phase.

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