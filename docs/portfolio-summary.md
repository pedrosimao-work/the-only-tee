# The Only Drop — Portfolio Summary

## One-Sentence Pitch

The Only Drop is a full-stack Flask application for managing monthly limited T-shirt drops with Stripe Checkout, Printify integration, admin-controlled fulfillment, MariaDB production deployment, and safe portfolio-demo protections.

## What This Project Demonstrates

- Full-stack Flask application structure
- Authentication and admin authorization
- SQLAlchemy models and migrations
- Real external API integrations
- Stripe Checkout and webhook handling
- Printify product synchronization and guarded fulfillment
- Production MariaDB deployment
- DirectAdmin Passenger deployment
- Cloudflare DNS setup
- Environment-based configuration
- Production logging and safe error handling
- Professional GitHub issue/branch/PR workflow

## Main Technical Challenge

The main challenge was coordinating a realistic commerce flow without turning the public demo into an unsafe live store.

The final flow separates payment validation from real fulfillment:

```text
Stripe Checkout confirms payment
-> Stripe webhook marks local Order as paid
-> Admin manually reviews the Order
-> Printify fulfillment only works when PRINTIFY_FULFILLMENT_ENABLED=true
-> Printify manual approval remains the final safety layer
```

## Architecture Summary

The app uses a modular Flask architecture:

```text
Application factory
Blueprints
SQLAlchemy models
Service layer for Stripe and Printify
Environment-based configuration
MariaDB production database
Passenger WSGI deployment
```

## Production Validation

The deployed demo was validated with:

```text
Public URL live
MariaDB connected and migrated
Admin login working
Active and archived drops created
Stripe Checkout test payment completed
Stripe webhook processed checkout.session.completed
Paid order saved in MariaDB
Manual Printify fulfillment tested
Printify order created and cancelled before production fulfillment
PRINTIFY_FULFILLMENT_ENABLED restored to false
Production logs checked
```

## Interview Talking Points

### Why Flask?

Flask was chosen because it allows explicit control over application structure, routing, authentication, service layers, and deployment configuration. This made it suitable for demonstrating backend architecture rather than relying on too much framework magic.

### Why Stripe Checkout?

Stripe Checkout reduces payment-surface complexity while still allowing a real payment lifecycle: session creation, customer redirect, webhook handling, local order creation, and payment status updates.

### Why Printify fulfillment is guarded?

Printify order creation is intentionally protected by an environment flag and an admin action. This prevents public demo users from creating external fulfillment orders accidentally.

### Why MariaDB in production?

The app uses SQLite locally for simple development, but production runs on MariaDB through SQLAlchemy and PyMySQL to demonstrate a real hosted relational database deployment.

### What would improve next?

The strongest next improvements would be pytest coverage, GitHub Actions CI, automated cron-based monthly rotation, and stronger admin order filtering.