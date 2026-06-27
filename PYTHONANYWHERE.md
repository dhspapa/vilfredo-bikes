# PythonAnywhere deployment — Vilfredo Bikes

Step-by-step guide for hosting `vilfredo_bikes` on [PythonAnywhere](https://www.pythonanywhere.com/).

**Do not switch to Stripe live keys until the online test-mode booking passes end-to-end.**

Replace `YOUR_USERNAME` with your PythonAnywhere username and `YOUR_DOMAIN` with your eventual subdomain or custom domain (e.g. `yourusername.pythonanywhere.com`).

---

## Compatibility check (project is ready)

| Item | Project setting | PythonAnywhere notes |
|------|-----------------|----------------------|
| **STATIC_ROOT** | `BASE_DIR / staticfiles` | Map `/static/` to this folder in the Web tab |
| **STATIC_URL** | `/static/` | Matches PythonAnywhere static files URL |
| **ALLOWED_HOSTS** | From `.env` | Set your `*.pythonanywhere.com` host (and custom domain later) |
| **WSGI module** | `config.wsgi.application` | Point the Web tab WSGI file at your project’s `config/wsgi.py` |
| **Database** | SQLite by default | Acceptable for MVP; `db.sqlite3` lives in the project root |
| **`.env` loading** | `load_dotenv(BASE_DIR / ".env")` | Place `.env` next to `manage.py` on the server |
| **HTTPS** | `SECURE_PROXY_SSL_HEADER` when `DEBUG=False` | Set `SECURE_SSL_REDIRECT=False` on PythonAnywhere (PA handles HTTPS) |

**No code changes are required before upload** if you configure `.env` correctly on the server (see step 4 and the notes at the end).

---

## What to upload (and what not to)

Upload the **`vilfredo_bikes/`** folder contents (where `manage.py` lives).

**Include:**

- `config/`, `bikes/`, `templates/`, `locale/`
- `manage.py`, `requirements.txt`, `.env.example`

**Do not upload:**

- `.env` (create on server only)
- `.venv/`
- `db.sqlite3` (created by migrate on server)
- `staticfiles/` (created by collectstatic on server)
- `__pycache__/`, `*.pyc`

**Recommended:** push via GitHub and clone on PythonAnywhere, or upload a zip excluding the folders above.

---

## Step 1 — Upload / push project code

### Option A — Git (recommended)

1. Push the repo to GitHub (without `.env`, `.venv`, `db.sqlite3`).
2. Open a **Bash console** on PythonAnywhere.
3. Clone into your home directory:

```bash
cd ~
git clone https://github.com/YOUR_ORG/YOUR_REPO.git
# If the repo root is the monorepo, move or clone only vilfredo_bikes:
# the app root must be ~/vilfredo_bikes (where manage.py lives)
```

If the git repo root is `vilfredo/` and the app is in `vilfredo_bikes/`:

```bash
cd ~/vilfredo/vilfredo_bikes
```

### Option B — Upload zip

1. Zip the `vilfredo_bikes` folder (exclude `.venv`, `.env`, `db.sqlite3`, `staticfiles`).
2. Upload via the **Files** tab to `/home/YOUR_USERNAME/vilfredo_bikes/`.
3. Unzip in a Bash console.

Confirm:

```bash
ls ~/vilfredo_bikes/manage.py
```

---

## Step 2 — Create virtualenv

In a PythonAnywhere **Bash** console:

```bash
cd ~/vilfredo_bikes
mkvirtualenv --python=/usr/bin/python3.11 vilfredo-bikes
# Or: python3.11 -m venv ~/.virtualenvs/vilfredo-bikes
```

Note the virtualenv path (e.g. `/home/YOUR_USERNAME/.virtualenvs/vilfredo-bikes`).

---

## Step 3 — Install requirements

```bash
workon vilfredo-bikes   # if using mkvirtualenv
cd ~/vilfredo_bikes
pip install --upgrade pip
pip install -r requirements.txt
```

Dependencies: Django, stripe, python-dotenv, polib (for `compile_translations`).

---

## Step 4 — Configure `.env`

On the server only (never commit):

```bash
cd ~/vilfredo_bikes
cp .env.example .env
nano .env   # or use the Files tab editor
```

### Phase A — Online test mode (before go-live)

Use these values first (adjust host when your domain is known):

```env
DJANGO_SECRET_KEY=generate-a-long-random-secret-here
DEBUG=False
ALLOWED_HOSTS=YOUR_USERNAME.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://YOUR_USERNAME.pythonanywhere.com
SITE_URL=https://YOUR_USERNAME.pythonanywhere.com

DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
STATIC_ROOT=staticfiles

# PythonAnywhere: PA terminates HTTPS — do not redirect at Django level
SECURE_SSL_REDIRECT=False

# Stripe TEST keys first
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

LOCAL_STRIPE_SUCCESS_FALLBACK=False

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=bikes@example.com
ADMIN_NOTIFICATION_EMAIL=owner@example.com
```

When you add a **custom domain** later, update `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `SITE_URL`.

---

## Step 5 — Configure WSGI file

Open the **Web** tab → **WSGI configuration file**.

Replace its contents with (adjust paths):

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

On the same **Web** tab:

- **Virtualenv:** `/home/YOUR_USERNAME/.virtualenvs/vilfredo-bikes`
- **Source code / working directory:** `/home/YOUR_USERNAME/vilfredo_bikes`

Save and reload the web app.

---

## Step 6 — Configure static files

In the **Web** tab → **Static files**:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/YOUR_USERNAME/vilfredo_bikes/staticfiles/` |

Then collect static files (step 7 below).

---

## Step 7 — Run migrations

```bash
workon vilfredo-bikes
cd ~/vilfredo_bikes
python manage.py migrate
python manage.py compile_translations
python manage.py collectstatic --noinput
```

Reload the web app after `collectstatic`.

---

## Step 8 — Seed bikes and routes

```bash
python manage.py seed_data
```

Expected active bikes:

- **City Bike** — 10,00 €/day, 150,00 € deposit
- **Electric Bike** — 20,00 €/day, 400,00 € deposit

Plus three suggested routes. The command is idempotent and removes stray test bikes.

---

## Step 9 — Create superuser

```bash
python manage.py createsuperuser
```

Admin URL: `https://YOUR_USERNAME.pythonanywhere.com/admin/`

---

## Step 10 — Configure allowed hosts

Already in `.env` (step 4). Must include every host you serve:

```env
ALLOWED_HOSTS=YOUR_USERNAME.pythonanywhere.com
```

When using a custom domain:

```env
ALLOWED_HOSTS=YOUR_USERNAME.pythonanywhere.com,yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://YOUR_USERNAME.pythonanywhere.com,https://yourdomain.com,https://www.yourdomain.com
SITE_URL=https://yourdomain.com
```

Reload the web app after `.env` changes.

---

## Step 11 — Configure Stripe test webhook URL

In the [Stripe Dashboard](https://dashboard.stripe.com/test/webhooks) ( **Test mode** ):

1. **Add endpoint**
2. **URL:**

```
https://YOUR_USERNAME.pythonanywhere.com/stripe/webhook/
```

3. **Events:** `checkout.session.completed`
4. Copy the **signing secret** (`whsec_...`) into server `.env` as `STRIPE_WEBHOOK_SECRET`
5. Reload the web app

**Note:** The webhook path has **no** language prefix (`/en/` or `/el/`).

---

## Step 12 — Test online with Stripe test keys

Checklist:

- [ ] Homepage loads: `https://YOUR_USERNAME.pythonanywhere.com/en/`
- [ ] Greek homepage: `https://YOUR_USERNAME.pythonanywhere.com/el/`
- [ ] QR landing: `https://YOUR_USERNAME.pythonanywhere.com/en/office-home-2/`
- [ ] Complete a booking with test card `4242 4242 4242 4242`
- [ ] Stripe webhook delivers `checkout.session.completed` (check Stripe Dashboard → Webhooks → event log)
- [ ] Success page shows **Paid** after webhook (not stuck on “Payment processing”)
- [ ] Admin shows reservation as paid with correct rental + deposit + total
- [ ] Guest and admin emails sent once (if SMTP configured)
- [ ] Cancel flow: start checkout → cancel → reservation stays unpaid

If webhook fails:

- Confirm `STRIPE_WEBHOOK_SECRET` matches the **test** endpoint secret
- Confirm URL is exactly `/stripe/webhook/` over HTTPS
- Check PythonAnywhere **Error log** and Stripe webhook response code (expect 200)

---

## Step 13 — Switch to Stripe live keys (only after test passes)

**Only after step 12 passes completely:**

1. In Stripe Dashboard, switch to **Live mode**
2. Create a **live** webhook:

```
https://YOUR_DOMAIN/stripe/webhook/
```

3. Update server `.env`:

```env
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...   # from LIVE webhook, not test
LOCAL_STRIPE_SUCCESS_FALLBACK=False
```

4. Reload the web app
5. Run **one** small real payment to verify live webhook + emails
6. Do **not** delete the test webhook until live flow is confirmed

---

## PythonAnywhere quick reference

| Setting | Value |
|---------|-------|
| Project root | `/home/YOUR_USERNAME/vilfredo_bikes` |
| WSGI | `config.wsgi.application` |
| Settings module | `config.settings` |
| Static URL | `/static/` → `.../staticfiles/` |
| Webhook | `https://YOUR_DOMAIN/stripe/webhook/` |
| Admin | `https://YOUR_DOMAIN/admin/` |

---

## Troubleshooting

| Problem | Likely fix |
|---------|------------|
| `DisallowedHost` | Add host to `ALLOWED_HOSTS` in `.env`, reload |
| CSRF error on form submit | Add HTTPS origin to `CSRF_TRUSTED_ORIGINS` |
| Static CSS missing | Run `collectstatic`, check Web tab static mapping |
| Redirect loop | Set `SECURE_SSL_REDIRECT=False` on PythonAnywhere |
| Payment stuck “processing” | Webhook secret/URL wrong; check Stripe event log |
| Greek UI in English | Run `python manage.py compile_translations` |
| `ImproperlyConfigured` SECRET_KEY | Set `DJANGO_SECRET_KEY` in `.env` when `DEBUG=False` |

---

## After deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for the full production checklist and VPS alternative.
