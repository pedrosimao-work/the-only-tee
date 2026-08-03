# The Only Drop

A full-stack Python web app for managing monthly limited T-shirt drops, user accounts, archive collections, Stripe-hosted checkout, Printify product synchronization, guarded Printify fulfillment, admin order visibility, and monthly drop lifecycle automation.

## Current Product Model

The Only Drop currently focuses on T-shirts.

The public portfolio demo domain is planned as:

```text
theonlydrop.pedrosimao.work
```

The support/contact email for the portfolio demo is:

```text
hello@pedrosimao.work
```

The current business rules are:

- One active T-shirt design per month
- One selected shirt color per design
- Multiple sizes per design
- No user-selected color changes
- Customers select size only
- Availability depends on Printify stock
- At the first second of each new month, the current design becomes archived
- The next scheduled design becomes the active monthly drop
- Previous drops remain visible in the permanent Archive Collection

## Current Status

The project currently includes:

- Flask application factory structure
- Blueprint-based application organization
- Bootstrap-based public layout
- SQLAlchemy database configuration
- Flask-Migrate migrations
- Drop model
- User model
- Order model
- User registration and login
- Password hashing
- Flask-Login session handling
- Admin-only dashboard
- Admin drop creation form
- Admin orders page
- Admin order detail page
- Admin test-order deletion action
- Database-powered homepage and archive page
- Monthly drop lifecycle automation
- Development seed command
- Printify shop and product lookup commands
- Printify product synchronization
- Printify mockup image synchronization
- Printify mockup carousel
- Checkout size selection
- Stripe-hosted Checkout integration
- Stripe webhook payment status handling
- Guarded Printify fulfillment flow
- Privacy Policy page
- Terms of Service page
- Shipping & Returns page
- Portfolio/demo checkout safety notices

## Tech Stack

- Python
- Flask
- Jinja2
- Bootstrap
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-Login
- Flask-WTF
- Requests
- Stripe Python SDK
- SQLite for local development
- MariaDB planned for production
- PyMySQL for future MariaDB connection
- DirectAdmin planned for production deployment

## Planned Integrations

- Stripe product and price synchronization from admin drops
- DirectAdmin deployment with MariaDB
- Cron-based monthly drop rotation in production
- Launch logging and error handling
- README and portfolio presentation polish

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

## Printify Configuration

The app connects monthly drops to existing Printify products and can submit paid orders to Printify through a guarded admin action.

Required environment variables:

```text
PRINTIFY_API_BASE_URL=https://api.printify.com/v1
PRINTIFY_API_TOKEN=your-printify-api-token
PRINTIFY_SHOP_ID=your-printify-shop-id
PRINTIFY_FULFILLMENT_ENABLED=false
```

Useful commands:

```bash
flask printify-shops
```

Lists Printify shops connected to the configured API token.

```bash
flask printify-product PRINTIFY_PRODUCT_ID
```

Shows a Printify product summary and available enabled variants.

```bash
flask printify-sync-drop 0001
```

Syncs a local drop with its configured Printify product ID, validates selected variant availability, stores mockup image URLs, and stores the size-to-Printify-variant map used during checkout.

### Current Printify Scope

The app can sync local drops with Printify products, validate selected variants, store product mockups, store available sizes, and prepare paid orders for fulfillment.

Printify fulfillment is disabled by default through:

```text
PRINTIFY_FULFILLMENT_ENABLED=false
```

When fulfillment is intentionally enabled, paid orders can be submitted to Printify from the admin order detail page.

The app prevents unpaid orders, orders without a selected Printify variant, and already-submitted orders from being submitted to Printify.

## Stripe Configuration

The app uses Stripe-hosted Checkout for payment simulation in the portfolio demo.

Required environment variables:

```text
STRIPE_SECRET_KEY=sk_test_your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=whsec_your-stripe-webhook-secret
```

The checkout flow currently supports:

- Stripe-hosted Checkout Session creation
- US-only shipping address collection
- Customer size selection before checkout
- Selected size stored in Stripe metadata
- Printify variant ID stored in Stripe metadata
- Local Order creation before redirecting to Stripe
- Webhook handling for `checkout.session.completed`
- Local payment status update after webhook completion
- Customer email update after webhook completion
- PaymentIntent ID storage after webhook completion
- Portfolio demo notices before and inside Stripe Checkout

The public portfolio demo is intended to run with Stripe test keys only.

Visitors should use Stripe test card:

```text
4242 4242 4242 4242
```

No real production order should be submitted from the portfolio demo.

## Demo Safety

This project is a portfolio demo and should not be treated as a live commercial store.

The app includes demo-safety protections:

- Stripe runs in test mode for the portfolio demo
- Checkout pages explain that this is a portfolio project
- Printify fulfillment is disabled by default
- Printify fulfillment requires `PRINTIFY_FULFILLMENT_ENABLED=true`
- Admin order deletion is labeled as local test-order deletion
- Test-order deletion does not refund Stripe and does not cancel external Printify orders
- Public support/contact copy uses `hello@pedrosimao.work`


## Logging and Error Handling

The app uses safe public error pages for 403, 404, and 500 responses. Technical error details are written to application logs instead of being shown to users.

Runtime logs are written to:

```text
instance/logs/the_only_drop.log
```

Logging can be configured with:

```text
LOG_LEVEL=INFO
LOG_TO_FILE=true
```

The `instance/` directory and log files must not be committed.


## Development Workflow

This project uses a professional GitHub workflow:

```text
Issue → Branch → Code → Commit → Pull Request → Merge → Done
```

## Planned Features

- Stripe product and price synchronization from admin drops
- Launch logging and error handling
- DirectAdmin deployment
- Production MariaDB configuration
- Cron-based monthly drop rotation in production
- README and portfolio presentation polish
- Tests with pytest
- Code quality tools