# Vilfredo Bikes

Minimal guest bike rental app for Office Home stays. Guests pick a bike, enter stay details, pay with Stripe Checkout, and receive a paid reservation after Stripe confirms payment via webhook.

No login. No booking API. Django admin manages bikes, reservations, and routes.

## Requirements

- Python 3.11+
- Stripe account (test mode is fine for local development)
- [Stripe CLI](https://stripe.com/docs/stripe-cli) for local webhook testing

## Quick start

```bash
cd vilfredo_bikes

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your Stripe keys

python manage.py migrate
python manage.py seed_data
python manage.py createsuperuser

python manage.py compile_translations
python manage.py runserver 8002
```

Open [http://127.0.0.1:8002/en/](http://127.0.0.1:8002/en/).

Admin: [http://127.0.0.1:8002/admin/](http://127.0.0.1:8002/admin/)

### Run locally on port 8002

```powershell
cd vilfredo_bikes
.\.venv\Scripts\Activate.ps1
python manage.py runserver 8002
```

## Stripe setup

1. Copy your test keys from the [Stripe Dashboard](https://dashboard.stripe.com/test/apikeys) into `.env`:
   - `STRIPE_SECRET_KEY`
   - `STRIPE_PUBLIC_KEY`

2. Forward webhooks locally with the Stripe CLI:

```bash
stripe listen --forward-to localhost:8002/stripe/webhook/
```

Copy the webhook signing secret (`whsec_...`) into `.env` as `STRIPE_WEBHOOK_SECRET`, then restart Django.

3. Use Stripe test card `4242 4242 4242 4242` with any future expiry and CVC.

### Payment confirmation flow

- **Production:** reservations are marked paid only when Stripe sends `checkout.session.completed` to `/stripe/webhook/`.
- **Success page:** shows **Paid** after webhook confirmation, or **Payment processing** while waiting.
- **Local fallback (optional):** set `LOCAL_STRIPE_SUCCESS_FALLBACK=True` in `.env` to mark paid from the success page without webhook (development only). Default is `False`.

If a guest cancels checkout, the reservation stays unpaid and is not confirmed.

## Pages

| URL | Description |
|-----|-------------|
| `/en/` or `/el/` | Homepage with the two bikes |
| `/en/office-home-2/` or `/el/office-home-2/` | QR landing page for Office Home 2 |
| `/en/office-home-3/` or `/el/office-home-3/` | QR landing page for Office Home 3 |
| `/en/bikes/<id>/` | Booking form and Stripe Checkout |
| `/en/office-home-2/bikes/<id>/` | Booking with property preselected |
| `/en/booking/<id>/success/` | Payment success / processing status |
| `/en/booking/<id>/cancel/` | Payment cancelled |
| `/en/routes/` | Suggested routes |
| `/stripe/webhook/` | Stripe webhook endpoint (no language prefix) |

## Pricing and deposits

| Bike | Daily rate | Security deposit |
|------|------------|------------------|
| City Bike | 10,00 € | 150,00 € |
| Electric Bike | 20,00 € | 400,00 € |

Stripe Checkout charges **rental price + refundable security deposit** in one payment.

## Availability

A bike is unavailable when a **paid** reservation overlaps the requested rental dates:

```
existing.rental_start <= requested.rental_end
AND existing.rental_end >= requested.rental_start
```

Unpaid or cancelled reservations do **not** block availability.

Rental dates must fall within the guest's check-in and check-out dates.

## Admin workflow

After payment, manage reservations in Django admin:

- View rental price, deposit, and total charged
- **Mark selected reservations as returned**
- **Mark selected deposits as refunded**
- Add internal notes in `admin_notes`

## Translations

Greek UI strings live in `locale/el/LC_MESSAGES/django.po`. After editing translations, compile them:

```bash
python manage.py compile_translations
```

On Windows without GNU gettext, `compile_translations` uses `polib` (included in `requirements.txt`).

## Tests

```bash
python manage.py test
```

## Seed data

```bash
python manage.py seed_data
```

Creates:

- Electric Bike — 20,00 €/day (400,00 € deposit)
- City Bike — 10,00 €/day (150,00 € deposit)
- Three suggested routes (Thessaloniki Waterfront, White Tower Route, Kalamaria Ride)

## Environment variables

See `.env.example` for all supported variables. Never commit `.env` (it is listed in `.gitignore`).

For full deployment steps, see **[DEPLOYMENT.md](DEPLOYMENT.md)**.

For **PythonAnywhere**, see **[PYTHONANYWHERE.md](PYTHONANYWHERE.md)** (step-by-step) and **[PYTHONANYWHERE_CHECKLIST.md](PYTHONANYWHERE_CHECKLIST.md)** (dashboard checklist).

## PythonAnywhere deployment

Deploy the **`vilfredo_bikes/`** folder (where `manage.py` lives). Use **Stripe test keys first**; switch to live only after online testing passes.

**Dashboard checklist:** [PYTHONANYWHERE_CHECKLIST.md](PYTHONANYWHERE_CHECKLIST.md)  
**Full guide:** [PYTHONANYWHERE.md](PYTHONANYWHERE.md)

### Bash console (first deploy)

Replace `YOUR_USERNAME` with your PythonAnywhere username.

```bash
cd /home/YOUR_USERNAME/vilfredo_bikes

mkvirtualenv --python=/usr/bin/python3.11 vilfredo-bikes
# Or: mkvirtualenv --python=/usr/bin/python3.10 vilfredo-bikes

workon vilfredo-bikes
pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
nano .env

python manage.py migrate
python manage.py compile_translations
python manage.py seed_data
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### Server `.env` (minimum for PythonAnywhere)

Set at least: `DJANGO_SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `SITE_URL`, `SECURE_SSL_REDIRECT=False`, SQLite `DB_*` vars, Stripe test keys, `STRIPE_WEBHOOK_SECRET`, `LOCAL_STRIPE_SUCCESS_FALLBACK=False`, and SMTP `EMAIL_*` vars. See `.env.example`.

### Web tab

| Setting | Value |
|---------|--------|
| Source code / working directory | `/home/YOUR_USERNAME/vilfredo_bikes` |
| Virtualenv | `/home/YOUR_USERNAME/.virtualenvs/vilfredo-bikes` |
| Static URL | `/static/` |
| Static directory | `/home/YOUR_USERNAME/vilfredo_bikes/staticfiles/` |

WSGI file: import from `config.wsgi` with project on `sys.path` (see `PYTHONANYWHERE.md`).

### Stripe test webhook

```
https://YOUR_USERNAME.pythonanywhere.com/stripe/webhook/
```

Event: `checkout.session.completed`. Reload the web app after updating `.env`.

### Reload

**Web** tab → green **Reload** button after WSGI, `.env`, or `collectstatic` changes.

---

## Production checklist

- [ ] **`DEBUG=False`** on the server
- [ ] **`DJANGO_SECRET_KEY`** set to a long random value (not the dev default)
- [ ] **`ALLOWED_HOSTS`** includes your domain(s)
- [ ] **`CSRF_TRUSTED_ORIGINS`** set to your HTTPS origins (e.g. `https://yourdomain.com`)
- [ ] **`SITE_URL`** set to your public HTTPS URL
- [ ] **Database** configured (SQLite OK for PythonAnywhere MVP; PostgreSQL optional later)
- [ ] **`python manage.py migrate`** run on the server
- [ ] **Static files** collected with `python manage.py collectstatic --noinput`
- [ ] **Stripe live keys** (`sk_live_...`, `pk_live_...`) in server `.env`
- [ ] **Stripe live webhook** pointing to `https://yourdomain.com/stripe/webhook/`
- [ ] **`STRIPE_WEBHOOK_SECRET`** updated to the live webhook signing secret
- [ ] **`LOCAL_STRIPE_SUCCESS_FALLBACK=False`** (forced off when `DEBUG=False`)
- [ ] **SMTP email** configured (`EMAIL_HOST`, credentials, `DEFAULT_FROM_EMAIL`)
- [ ] **HTTPS** enabled at the reverse proxy / host (required for secure cookies)
- [ ] **`python manage.py createsuperuser`** for admin access
- [ ] **`python manage.py compile_translations`** for Greek UI
- [ ] **`python manage.py test`** passes before deploy

### Production environment variables

| Variable | Production value |
|----------|------------------|
| `DEBUG` | `False` |
| `DJANGO_SECRET_KEY` | Long random secret |
| `ALLOWED_HOSTS` | `yourdomain.com,www.yourdomain.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://yourdomain.com,https://www.yourdomain.com` |
| `SITE_URL` | `https://yourdomain.com` |
| `DB_ENGINE` | `django.db.backends.sqlite3` (PA MVP) or PostgreSQL (VPS) |
| `STATIC_ROOT` | `staticfiles` (default) |
| `SECURE_SSL_REDIRECT` | `False` on PythonAnywhere; `True` on VPS if desired |
| `STRIPE_SECRET_KEY` | `sk_live_...` |
| `STRIPE_PUBLIC_KEY` | `pk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | Live `whsec_...` from Stripe Dashboard |
| `EMAIL_*` | Production SMTP settings |

When `DEBUG=False`, Django enables secure cookies. HTTPS redirect is off by default (`SECURE_SSL_REDIRECT=False`); enable it on VPS via `.env` if needed.

## Deployment notes

Do **not** use `runserver` in production. Use PythonAnywhere WSGI or a VPS WSGI server behind HTTPS.

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for VPS notes.

## Project layout

```
vilfredo_bikes/
  config/          # Django project settings
  bikes/           # Rental app (models, views, Stripe)
  templates/       # Bootstrap templates
  locale/          # Greek translations
  manage.py
  requirements.txt
```

## Known limitations (MVP)

- Deposit refunds are tracked manually in admin; no automatic Stripe refund yet
- Admin notification emails are English-only
- Property names (Office Home 2/3) stay in English in both languages
- SQLite database (fine for MVP; use PostgreSQL in production)
- No guest login or booking modification after payment
