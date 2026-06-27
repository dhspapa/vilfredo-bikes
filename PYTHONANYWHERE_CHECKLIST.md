# PythonAnywhere deployment checklist

Follow this inside the PythonAnywhere dashboard. Replace `YOUR_USERNAME` with your account name.

**Order:** Files → Bash console → Web tab → test → Stripe live keys only after test passes.

---

## Before you start

- [ ] Project code is in `/home/YOUR_USERNAME/vilfredo_bikes/` (with `manage.py` at that level)
- [ ] You have Stripe **test** keys ready (not live yet)
- [ ] You have SMTP details ready (or accept that emails may fail until SMTP is set)

---

## 1. Files tab

- [ ] Confirm project folder exists: `/home/YOUR_USERNAME/vilfredo_bikes/`
- [ ] Confirm these are present:
  - [ ] `manage.py`
  - [ ] `requirements.txt`
  - [ ] `.env.example`
  - [ ] `config/`, `bikes/`, `templates/`, `locale/`
- [ ] Confirm these are **not** uploaded:
  - [ ] `.env` (you create it on the server)
  - [ ] `.venv/`
  - [ ] `db.sqlite3` (created by migrate)
  - [ ] `staticfiles/` (created by collectstatic)
- [ ] Create `.env` on the server:
  - [ ] Copy `.env.example` → `.env` (via Bash or Files → copy/rename)
  - [ ] Edit `.env` with your values (see section 6 below)
  - [ ] Save `.env` in `/home/YOUR_USERNAME/vilfredo_bikes/.env`

---

## 2. Bash console

Run in order (activate virtualenv first if it already exists):

```bash
cd /home/YOUR_USERNAME/vilfredo_bikes
```

### Virtualenv (first time only)

```bash
mkvirtualenv --python=/usr/bin/python3.11 vilfredo-bikes
```

If 3.11 is unavailable:

```bash
mkvirtualenv --python=/usr/bin/python3.10 vilfredo-bikes
```

```bash
workon vilfredo-bikes
pip install --upgrade pip
pip install -r requirements.txt
```

### Deploy commands (every fresh deploy or update)

- [ ] `workon vilfredo-bikes`
- [ ] `cd /home/YOUR_USERNAME/vilfredo_bikes`
- [ ] `pip install -r requirements.txt` *(after code/requirements changes)*
- [ ] `python manage.py migrate`
- [ ] `python manage.py compile_translations`
- [ ] `python manage.py seed_data`
- [ ] `python manage.py collectstatic --noinput`
- [ ] `python manage.py createsuperuser` *(first time only)*

Optional sanity check:

```bash
python manage.py check
python manage.py test bikes
```

---

## 3. Web tab

Open **Web** in the dashboard.

### Code / virtualenv

- [ ] **Source code:** `/home/YOUR_USERNAME/vilfredo_bikes`
- [ ] **Working directory:** `/home/YOUR_USERNAME/vilfredo_bikes`
- [ ] **Virtualenv:** `/home/YOUR_USERNAME/.virtualenvs/vilfredo-bikes`

### Domain / HTTPS

- [ ] Note your site URL: `https://YOUR_USERNAME.pythonanywhere.com`
- [ ] Enable HTTPS if not already on (PythonAnywhere handles TLS)

### WSGI

- [ ] Click **WSGI configuration file** link
- [ ] Paste content from section 4 below
- [ ] Save

### Static files

- [ ] Add mapping from section 5 below
- [ ] Save

### Reload

- [ ] Click the green **Reload YOUR_USERNAME.pythonanywhere.com** button (see section 7)

---

## 4. WSGI file content

Replace the entire WSGI file with:

```python
import os
import sys

project_home = "/home/YOUR_USERNAME/vilfredo_bikes"
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

- [ ] Saved WSGI file
- [ ] Reloaded web app

---

## 5. Static files mapping

In **Web** tab → **Static files** → **Add a new mapping**:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/YOUR_USERNAME/vilfredo_bikes/staticfiles/` |

- [ ] Mapping saved
- [ ] `collectstatic` already run in Bash console
- [ ] Web app reloaded after collectstatic

---

## 6. Environment variables (`.env` file)

File location: `/home/YOUR_USERNAME/vilfredo_bikes/.env`

These variables **must** exist for production on PythonAnywhere:

| Variable | Example / notes |
|----------|-----------------|
| `DJANGO_SECRET_KEY` | Long random string (required when `DEBUG=False`) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `YOUR_USERNAME.pythonanywhere.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://YOUR_USERNAME.pythonanywhere.com` |
| `SITE_URL` | `https://YOUR_USERNAME.pythonanywhere.com` |
| `DB_ENGINE` | `django.db.backends.sqlite3` |
| `DB_NAME` | `db.sqlite3` |
| `STATIC_ROOT` | `staticfiles` |
| `SECURE_SSL_REDIRECT` | `False` *(PythonAnywhere handles HTTPS)* |
| `STRIPE_SECRET_KEY` | Test key first (`sk_test_...`) |
| `STRIPE_PUBLIC_KEY` | Test key first (`pk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | From Stripe **test** webhook (`whsec_...`) |
| `LOCAL_STRIPE_SUCCESS_FALLBACK` | `False` |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | Your SMTP host |
| `EMAIL_PORT` | `587` (typical) |
| `EMAIL_HOST_USER` | SMTP username |
| `EMAIL_HOST_PASSWORD` | SMTP password |
| `EMAIL_USE_TLS` | `True` |
| `DEFAULT_FROM_EMAIL` | Sender address |
| `ADMIN_NOTIFICATION_EMAIL` | Owner inbox |

- [ ] All variables set in `.env`
- [ ] `.env` is **not** committed to git
- [ ] Web app reloaded after editing `.env`

**Custom domain later:** add the new host to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`, update `SITE_URL`, reload.

---

## 7. Reload the web app

Do this after:

- WSGI changes
- `.env` changes
- `collectstatic`
- `pip install` / code updates

**Steps:**

1. Open **Web** tab
2. Click the green **Reload** button at the top
3. Wait a few seconds
4. Refresh your site in the browser

If something still looks wrong:

- [ ] Check **Web** tab → **Error log**
- [ ] Check **Web** tab → **Server log**

---

## 8. Testing

### Homepage (English)

- [ ] Open: `https://YOUR_USERNAME.pythonanywhere.com/en/`
- [ ] Page loads without `DisallowedHost` or 500 error
- [ ] Two bikes visible: City Bike and Electric Bike
- [ ] “Book now” links work

### Greek page

- [ ] Open: `https://YOUR_USERNAME.pythonanywhere.com/el/`
- [ ] Greek headings visible (not English body text)
- [ ] Language switcher EN / EL works
- [ ] Optional QR page: `https://YOUR_USERNAME.pythonanywhere.com/el/office-home-2/`

### Stripe test payment

**Prerequisite:** Stripe **test** keys in `.env`, webhook configured (below).

- [ ] Open booking form, e.g. `https://YOUR_USERNAME.pythonanywhere.com/en/bikes/1/`
- [ ] Fill form, accept terms, submit
- [ ] Redirected to Stripe Checkout
- [ ] Pay with test card `4242 4242 4242 4242` (any future expiry, any CVC)
- [ ] Returned to success page

### Webhook

**Stripe Dashboard (Test mode) → Webhooks → Add endpoint:**

```
https://YOUR_USERNAME.pythonanywhere.com/stripe/webhook/
```

- [ ] Event: `checkout.session.completed`
- [ ] Signing secret copied into `.env` as `STRIPE_WEBHOOK_SECRET`
- [ ] Web app reloaded
- [ ] Complete a test payment
- [ ] Stripe webhook log shows **200** response
- [ ] Success page shows **Paid** (refresh if it briefly said “Payment processing”)
- [ ] Admin reservation shows `paid=True` and `paid_at` set

### Admin login

- [ ] Open: `https://YOUR_USERNAME.pythonanywhere.com/admin/`
- [ ] Log in with superuser created in Bash console
- [ ] Reservations list loads
- [ ] Open a paid test reservation — rental price, deposit, total charged visible

---

## Go-live (only after all tests pass)

- [ ] Switch Stripe Dashboard to **Live mode**
- [ ] Create **live** webhook at same path: `https://YOUR_USERNAME.pythonanywhere.com/stripe/webhook/`
- [ ] Replace `.env` Stripe keys with **live** keys and **live** webhook secret
- [ ] Reload web app
- [ ] Run one small real payment to confirm

---

## Quick reference

| Item | Value |
|------|--------|
| Project root | `/home/YOUR_USERNAME/vilfredo_bikes` |
| Virtualenv | `/home/YOUR_USERNAME/.virtualenvs/vilfredo-bikes` |
| WSGI module | `config.wsgi.application` |
| Static URL | `/static/` → `.../staticfiles/` |
| Webhook | `https://YOUR_USERNAME.pythonanywhere.com/stripe/webhook/` |

Full Bash command list: **[PYTHONANYWHERE.md](PYTHONANYWHERE.md)**
