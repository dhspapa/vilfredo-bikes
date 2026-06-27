# Deployment handoff — Vilfredo Bikes

Use this document when deploying the MVP after acceptance testing.

## Project folder

```
vilfredo_bikes/
  config/                 # Django settings (config.settings)
  bikes/                  # Rental app
  templates/              # HTML templates
  locale/el/              # Greek translations
  manage.py
  requirements.txt
  .env.example            # Template only — copy to .env on the server
  DEPLOYMENT.md           # This file
  README.md               # Local dev + overview
```

Deploy the **`vilfredo_bikes/`** directory as the application root (where `manage.py` lives).

---

## Required environment variables

Copy `.env.example` to `.env` on the server and set:

| Variable | Required | Notes |
|----------|----------|-------|
| `DEBUG` | Yes | Must be `False` in production |
| `DJANGO_SECRET_KEY` | Yes | Long random string (not the dev default) |
| `ALLOWED_HOSTS` | Yes | Comma-separated domains, e.g. `yourdomain.com,www.yourdomain.com` |
| `CSRF_TRUSTED_ORIGINS` | Yes | Comma-separated HTTPS origins, e.g. `https://yourdomain.com` |
| `SITE_URL` | Yes | Public site URL, e.g. `https://yourdomain.com` |
| `DB_ENGINE` | Recommended | `django.db.backends.postgresql` for production |
| `DB_NAME` | If PostgreSQL | Database name |
| `DB_USER` | If PostgreSQL | Database user |
| `DB_PASSWORD` | If PostgreSQL | Database password |
| `DB_HOST` | If PostgreSQL | Usually `localhost` |
| `DB_PORT` | If PostgreSQL | Usually `5432` |
| `STATIC_ROOT` | Optional | Default `staticfiles` |
| `STRIPE_SECRET_KEY` | Yes | Live key `sk_live_...` |
| `STRIPE_PUBLIC_KEY` | Yes | Live key `pk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | Yes | Live webhook signing secret `whsec_...` |
| `LOCAL_STRIPE_SUCCESS_FALLBACK` | Yes | Must be `False` (also forced off when `DEBUG=False`) |
| `EMAIL_BACKEND` | Yes | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | Yes | SMTP hostname |
| `EMAIL_PORT` | Yes | Usually `587` |
| `EMAIL_HOST_USER` | Yes | SMTP username |
| `EMAIL_HOST_PASSWORD` | Yes | SMTP password |
| `EMAIL_USE_TLS` | Yes | Usually `True` |
| `DEFAULT_FROM_EMAIL` | Yes | Sender address for guest emails |
| `ADMIN_NOTIFICATION_EMAIL` | Yes | Owner inbox for new paid bookings |

Never commit `.env`. It is listed in `.gitignore`.

---

## Required commands (first deploy)

Run from the `vilfredo_bikes/` directory with virtualenv activated:

```bash
pip install -r requirements.txt
pip install psycopg2-binary    # if using PostgreSQL
pip install gunicorn             # if using a VPS

python manage.py migrate
python manage.py compile_translations
python manage.py collectstatic --noinput
python manage.py seed_data
python manage.py createsuperuser
python manage.py test
```

Restart the WSGI process after `.env` changes.

---

## Static files

```bash
python manage.py collectstatic --noinput
```

- **`STATIC_URL`:** `/static/`
- **`STATIC_ROOT`:** `staticfiles/` (by default)

Serve `/static/` from the `staticfiles/` directory via your host (PythonAnywhere static mapping or Nginx).

---

## Migrations

```bash
python manage.py migrate
```

Apply after every deploy that includes model changes.

---

## Superuser (admin access)

```bash
python manage.py createsuperuser
```

Admin URL: `/admin/`

---

## Stripe live webhook URL format

Register in the [Stripe Dashboard](https://dashboard.stripe.com/webhooks) (live mode):

```
https://YOUR_DOMAIN/stripe/webhook/
```

Examples:

- `https://yourdomain.com/stripe/webhook/`
- `https://yourusername.pythonanywhere.com/stripe/webhook/`

Events needed: **`checkout.session.completed`**

Copy the signing secret into `STRIPE_WEBHOOK_SECRET` on the server.

**Important:** Payment confirmation is webhook-only. Do not enable `LOCAL_STRIPE_SUCCESS_FALLBACK` in production.

---

## Email settings

Production requires working SMTP so guests and the owner receive confirmation emails after payment.

Minimum `.env` values:

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=bikes@yourdomain.com
EMAIL_HOST_PASSWORD=your-smtp-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=bikes@yourdomain.com
ADMIN_NOTIFICATION_EMAIL=owner@yourdomain.com
```

Test by completing one live or test booking and confirming two emails are sent once.

---

## Production checklist

- [ ] `DEBUG=False`
- [ ] `DJANGO_SECRET_KEY` is unique and strong
- [ ] `ALLOWED_HOSTS` matches your domain(s)
- [ ] `CSRF_TRUSTED_ORIGINS` uses HTTPS origins
- [ ] `SITE_URL` is your public HTTPS URL
- [ ] PostgreSQL configured (recommended)
- [ ] `python manage.py migrate`
- [ ] `python manage.py compile_translations`
- [ ] `python manage.py collectstatic --noinput`
- [ ] `python manage.py seed_data` (creates only City Bike + Electric Bike)
- [ ] `python manage.py createsuperuser`
- [ ] Stripe **live** keys in `.env`
- [ ] Stripe **live** webhook registered and secret saved
- [ ] `LOCAL_STRIPE_SUCCESS_FALLBACK=False`
- [ ] SMTP email configured and tested
- [ ] HTTPS enabled at the host / reverse proxy
- [ ] QR URLs tested: `/en/office-home-2/`, `/el/office-home-3/`, etc.
- [ ] One end-to-end test booking in production or staging

---

## Deployment options

### Option A — PythonAnywhere

**Best for:** Fast MVP launch, minimal DevOps, low traffic.

1. Upload `vilfredo_bikes/` to PythonAnywhere.
2. Create virtualenv; `pip install -r requirements.txt`.
3. Add `.env` via the server (not in git).
4. Configure WSGI → `config.wsgi.application`.
5. Map static files: `/static/` → `.../vilfredo_bikes/staticfiles/`.
6. Run migrate, compile_translations, collectstatic, seed_data, createsuperuser.
7. Enable HTTPS in PythonAnywhere; set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.
8. Add Stripe live webhook URL.

**Pros:** Simple, cheap, no server admin.  
**Cons:** Less flexible than a full VPS; PostgreSQL requires paid plan.

### Option B — VPS (Ubuntu + Nginx + Gunicorn)

**Best for:** Full control, custom domain, PostgreSQL, future scaling.

1. Provision VPS; install Python, PostgreSQL, Nginx, Certbot.
2. Clone/upload project; virtualenv + requirements + `psycopg2-binary` + `gunicorn`.
3. `.env` with production values; PostgreSQL database created.
4. migrate → compile_translations → collectstatic → seed_data → createsuperuser.
5. Gunicorn systemd service binding to `127.0.0.1:8002`.
6. Nginx reverse proxy with TLS; serve `/static/` from `staticfiles/`.
7. Stripe live webhook → `https://yourdomain.com/stripe/webhook/`.

**Pros:** Standard production stack, PostgreSQL, full control.  
**Cons:** More setup and ongoing maintenance.

### Recommended for this MVP

**PythonAnywhere** is the recommended first deploy if you want the site live quickly with minimal ops. See **[PYTHONANYWHERE.md](PYTHONANYWHERE.md)** and the dashboard checklist **[PYTHONANYWHERE_CHECKLIST.md](PYTHONANYWHERE_CHECKLIST.md)**. Move to a **VPS** later if you need PostgreSQL on your own server, more traffic, or tighter control.

---

## Seed data behaviour

`python manage.py seed_data` is **idempotent**:

- Upserts **Electric Bike** and **City Bike** only as active catalog bikes
- Upserts three suggested routes
- **Removes** any other bikes with no reservations (e.g. stray test bikes)
- **Deactivates** non-seed bikes that still have reservations (does not delete history)

After seeding, the public site should list exactly two active bikes.

---

## Local production-mode smoke test

Before deploy, verify settings load with production flags:

```powershell
cd vilfredo_bikes
$env:DEBUG="False"
$env:DJANGO_SECRET_KEY="replace-with-a-long-random-local-test-secret"
$env:ALLOWED_HOSTS="127.0.0.1,localhost"
$env:CSRF_TRUSTED_ORIGINS="http://127.0.0.1:8002"
python manage.py check
```

Do not use `runserver` in production; this check only confirms configuration is valid.
