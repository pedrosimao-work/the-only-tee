# The Only Drop

A full-stack Flask portfolio project for managing monthly limited T-shirt drops, archive collections, Stripe-hosted checkout, Printify product synchronization, guarded Printify fulfillment, admin order management, production logging, and DirectAdmin deployment.

Live demo:

```text
https://theonlydrop.pedrosimao.work
```

Support/contact email used in the demo:

```text
hello@pedrosimao.work
```

## Project Summary

The Only Drop is a limited-drop commerce platform prototype.

The app presents one active monthly T-shirt drop at a time. Previous drops are moved into a permanent archive collection, creating a simple product lifecycle:

```text
Draft -> Active -> Archived
```

The project was built as a real full-stack Python portfolio application, not as a static mockup. It includes authentication, admin-only management, database migrations, external API integrations, Stripe Checkout, Stripe webhooks, Printify product synchronization, guarded fulfillment, logging, safe error pages, and a deployed public demo.

## Core Business Rules

- One active T-shirt design per month
- One selected shirt color per design
- Customers select size only
- Previous drops remain visible in the Archive Collection
- Admin users create and manage drops
- Stripe Product and Price records are synchronized automatically
- Stripe Checkout handles test payments
- Stripe webhooks update local order status after payment
- Printify product data is synced into the app
- Printify fulfillment is disabled by default for public demo safety
- Paid orders can be manually submitted to Printify from the admin area only when fulfillment is intentionally enabled

## Live Demo Notes

The public demo is deployed at:

```text
https://theonlydrop.pedrosimao.work
```

The demo uses Stripe test mode.

Use Stripe test card:

```text
4242 4242 4242 4242
```

Use any future expiry date, any 3-digit CVC, and a valid postal code.

The public demo is not a real commercial store. No real card should be used.

Admin credentials are private and are not included in this repository.

## Implemented Features

### Public User Features

- Homepage with the current active monthly drop
- Archive Collection page for past drops
- Drop number, season, name, price, status, and mockup display
- Size selection before checkout
- Stripe-hosted Checkout redirect
- Checkout success and cancellation flows
- Portfolio/demo safety notices
- Legal pages:
  - Privacy Policy
  - Terms of Service
  - Shipping and Returns
- Safe public 403, 404, and 500 error pages

### Authentication

- User registration
- User login
- Password hashing
- Flask-Login session handling
- Protected routes
- Admin-only route protection

### Admin Features

- Admin dashboard
- Create drop
- Edit drop
- View drops
- View orders
- View order details
- Delete local test orders
- Visual Printify product picker
- Stripe Product and Price synchronization from drop data
- Manual Printify fulfillment action for paid orders

### Drop Management

- Drop model with lifecycle status
- Draft, active, and archived states
- One active drop concept
- Monthly rotation command
- Archive collection support
- Product type and shirt color validation
- Printify product association
- Printify size-to-variant mapping
- Mockup image synchronization

### Stripe Integration

- Stripe-hosted Checkout
- Automatic Stripe Product creation from admin drop creation
- Automatic USD Stripe Price creation from admin drop creation
- Stripe Product updates when drops are edited
- Replacement Stripe Price creation when price changes
- Saved Stripe Price ID usage during checkout
- Customer size stored in Stripe metadata
- Printify variant ID stored in Stripe metadata
- Local Order creation before redirecting to Stripe
- Stripe webhook endpoint for `checkout.session.completed`
- Local payment status update after webhook completion
- Customer email update after webhook completion
- PaymentIntent ID storage after webhook completion

### Printify Integration

- Printify shop lookup command
- Printify product lookup command
- Visual Printify product picker in admin forms
- Product title and mockup display in admin picker
- Product ID storage from picker selection
- Mockup image synchronization
- Size-to-variant mapping
- Variant availability validation
- Guarded manual fulfillment from admin order detail page
- Protection against submitting:
  - unpaid orders
  - orders without Printify variant IDs
  - already-submitted orders

### Production Features

- DirectAdmin deployment
- Passenger-compatible WSGI entrypoint
- MariaDB production database
- PyMySQL database connection
- Environment-based configuration
- Production database migrations with Flask-Migrate and Alembic
- Cloudflare DNS configuration
- Rotating application logs
- Safe error pages
- External service failure logging

## Tech Stack

### Backend

- Python
- Flask
- Flask application factory pattern
- Flask Blueprints
- Jinja2
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-Login
- Flask-WTF
- WTForms
- Requests
- Stripe Python SDK
- PyMySQL

### Frontend

- HTML
- CSS
- Bootstrap
- Jinja templates
- Responsive layout

### Database

- SQLite for local development
- MariaDB for production
- SQLAlchemy ORM
- Alembic migrations through Flask-Migrate

### External Services

- Stripe Checkout
- Stripe Webhooks
- Printify API
- Cloudflare DNS
- DirectAdmin shared hosting
- Passenger WSGI

## Architecture Overview

The project uses a modular Flask structure.

```text
app/
|-- __init__.py              # Flask application factory
|-- config.py                # Environment-based configuration
|-- extensions.py            # Shared Flask extensions
|-- models.py                # SQLAlchemy models
|-- errors.py                # Error handlers
|-- logging_config.py        # Application logging setup
|-- admin/                   # Admin dashboard, drops, and orders
|-- auth/                    # Registration, login, logout
|-- checkout/                # Stripe Checkout and webhook routes
|-- drops/                   # Public drop/archive routes
|-- legal/                   # Legal/demo policy pages
|-- services/                # Stripe and Printify service logic
|-- static/                  # CSS/static assets
`-- templates/               # Jinja templates
```

Core models:

```text
User
Drop
Order
```

Core service responsibilities:

```text
Stripe Checkout service:
- creates Checkout Sessions
- creates local Orders
- marks Orders paid after webhook completion

Printify service:
- reads Printify shops/products
- syncs product mockups and variants
- submits paid Orders to Printify when explicitly enabled

Drop lifecycle logic:
- archives expired active drops
- activates scheduled draft drops
```

## Data Flow

### Admin Drop Creation

```text
Admin creates drop
-> Admin selects Printify product from picker
-> App syncs Printify mockups and variants
-> App creates/updates Stripe Product
-> App creates Stripe Price
-> Drop is saved with Stripe and Printify references
```

### Checkout Flow

```text
Customer selects size
-> App maps size to Printify variant
-> App creates local Order
-> App creates Stripe Checkout Session
-> Customer completes Stripe test payment
-> Stripe sends checkout.session.completed webhook
-> App marks local Order as paid
```

### Guarded Printify Fulfillment Flow

```text
Admin opens paid Order
-> PRINTIFY_FULFILLMENT_ENABLED must be true
-> Admin clicks submit to Printify
-> App creates Printify order
-> Printify order appears in Printify
-> Printify manual approval controls real production fulfillment
```

For the public demo, fulfillment is restored to:

```text
PRINTIFY_FULFILLMENT_ENABLED=false
```

## Demo Safety

This project is a portfolio demo and should not be treated as a live commercial store.

Safety protections:

- Stripe uses test keys
- Checkout pages identify the project as a demo
- Printify fulfillment is disabled by default
- Printify fulfillment requires `PRINTIFY_FULFILLMENT_ENABLED=true`
- Printify submission is admin-controlled
- Printify manual approval remains a final external safety layer
- Local test-order deletion does not refund Stripe payments
- Local test-order deletion does not cancel external Printify orders
- Secrets and credentials are stored only in environment variables

## Environment Variables

Create a local `.env` file based on:

```text
.env.example
```

Production variables are documented in:

```text
.env.production.example
```

Important variables:

```text
SECRET_KEY=
FLASK_DEBUG=false
BASE_URL=https://theonlydrop.pedrosimao.work
BRAND_NAME=THE ONLY DROP
CONTACT_EMAIL=hello@pedrosimao.work

DATABASE_URL=

STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=

PRINTIFY_API_BASE_URL=https://api.printify.com/v1
PRINTIFY_API_TOKEN=
PRINTIFY_SHOP_ID=
PRINTIFY_FULFILLMENT_ENABLED=false

LOG_LEVEL=INFO
LOG_TO_FILE=true
```

Never commit real secrets.

## Local Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local environment file:

```bash
copy .env.example .env
```

Run migrations:

```bash
flask db upgrade
```

Seed development drop data:

```bash
flask seed-drops
```

Run the app locally:

```bash
python run.py
```

Open:

```text
http://127.0.0.1:5000
```

## Useful Flask Commands

Inspect the active database configuration:

```bash
flask db-info
```

Run monthly drop rotation manually:

```bash
flask rotate-drops
```

List connected Printify shops:

```bash
flask printify-shops
```

Inspect a Printify product:

```bash
flask printify-product PRINTIFY_PRODUCT_ID
```

Sync one drop with Printify:

```bash
flask printify-sync-drop DROP_NUMBER
```

## Database Configuration

Local development defaults to SQLite:

```text
sqlite:///the_only_drop.db
```

Production uses MariaDB through PyMySQL.

Standard production format:

```text
mysql+pymysql://database_user:database_password@localhost/database_name
```

On the DirectAdmin deployment, the MariaDB connection required the local MySQL socket:

```text
mysql+pymysql://database_user:database_password@localhost/database_name?unix_socket=/var/lib/mysql/mysql.sock
```

Real database credentials must be stored in environment variables and must never be committed to Git.

## DirectAdmin Deployment Summary

The deployed demo uses:

```text
Domain: theonlydrop.pedrosimao.work
Hosting: DirectAdmin shared hosting
Python: 3.11
WSGI: Passenger
Database: MariaDB
DNS: Cloudflare
```

DirectAdmin Python app settings:

```text
Application root: domains/theonlydrop.pedrosimao.work/public_html
Application URL: theonlydrop.pedrosimao.work
Startup file: passenger_wsgi.py
Application entry point: application
```

The app exposes the Passenger callable through:

```text
passenger_wsgi.py
```

Production deployment steps included:

```text
Create subdomain
Create DirectAdmin Python app
Clone GitHub repository into public_html
Install requirements in DirectAdmin virtual environment
Create MariaDB database and user
Configure production environment variables
Run Flask database migrations
Create production admin user
Configure Cloudflare DNS
Configure Stripe webhook
Validate Stripe Checkout
Validate Printify manual fulfillment
Restore Printify fulfillment safety flag
Check production logs
```

## Logging and Error Handling

The app uses safe public error pages for:

```text
403 Forbidden
404 Not Found
500 Internal Server Error
```

Technical details are written to application logs instead of being shown to users.

Runtime logs are written to:

```text
instance/logs/the_only_drop.log
```

Logging configuration:

```text
LOG_LEVEL=INFO
LOG_TO_FILE=true
```

The app logs important events and failures around:

- Stripe Checkout
- Stripe webhooks
- Stripe product synchronization
- Stripe price synchronization
- Printify product synchronization
- Printify fulfillment
- Admin external-service actions
- 403, 404, and 500 responses

The `instance/` directory and log files must not be committed.

## Deployment Validation

The deployed demo was validated with:

```text
Public URL live
DNS resolving through Cloudflare
Flask app importing through Passenger
MariaDB connected through PyMySQL and unix_socket
Production migrations applied
Admin user created
Admin login verified
Active drop created
Archived drop created
Printify product picker verified
Printify mockup sync verified
Stripe Checkout test payment completed
Stripe webhook processed checkout.session.completed
Paid Order saved in MariaDB
Manual Printify fulfillment submission verified
Printify order appeared in Printify
Printify order cancelled before production fulfillment
PRINTIFY_FULFILLMENT_ENABLED restored to false
Production logs checked with no ERROR or Traceback after validation
```

## Screenshots

### Homepage Active Drop

![Homepage active drop](docs/screenshots/homepage-active-drop.png)

### Archive Collection

![Archive Collection](docs/screenshots/archive-collection.png)

### Admin Drops List

![Admin drops list](docs/screenshots/admin-drops-list.png)

### Admin Drop Edit With Printify Picker

![Admin drop edit with Printify picker](docs/screenshots/admin-drop-edit-printify-picker.png)

### Admin Paid Order Detail

![Admin paid order detail](docs/screenshots/admin-order-detail-paid.png)

### Stripe Checkout Test Page

![Stripe Checkout test page](docs/screenshots/stripe-checkout-test.png)

Screenshot safety rules:

```text
No API keys
No webhook secrets
No database credentials
No private customer data
No admin password
```

Stripe webhook processing and Printify manual fulfillment were validated during deployment, but private provider-dashboard screenshots are intentionally excluded from the public repository.

## Development Workflow

This project used a professional GitHub workflow:

```text
Issue -> Branch -> Code -> Commit -> Pull Request -> Merge -> Done
```

The workflow included:

- GitHub Issues for project phases
- Feature branches for implementation work
- Pull requests before merging to `main`
- Deployment validation before closing deployment work
- Environment variables instead of committed secrets
- Production logs checked after external-service validation

## Portfolio Value

This project demonstrates:

- Full-stack Flask application development
- Authentication and authorization
- Relational database modeling
- SQLAlchemy ORM usage
- Production database migrations
- External API integration
- Stripe Checkout integration
- Stripe webhook handling
- Printify product and fulfillment integration
- Guarded production safety flags
- Admin dashboard workflows
- Server deployment on shared hosting
- Cloudflare DNS setup
- Production logging and error handling
- Realistic Git/GitHub workflow

## Future Improvements

Planned improvements after the deployed portfolio version:

- Add pytest test suite
- Add GitHub Actions CI
- Add code formatting/linting tools
- Add automated production cron job for monthly rotation
- Add richer screenshot documentation
- Add admin analytics summary
- Add improved order filtering/search
- Add Docker setup for local development
- Add stronger API documentation for internal service flows

## License

This project is a portfolio/demo project.

Real API keys, database credentials, Stripe secrets, Printify tokens, and production environment files are intentionally excluded from version control.