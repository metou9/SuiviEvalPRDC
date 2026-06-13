# 07 — Deployment

This document is the operational blueprint: the Dockerfiles, `docker-compose.yml`, the **host** nginx
configuration (the single entry point), the PostgreSQL bootstrap SQL, the environment contract, and a
runbook. It implements the topology in `01_architecture.md` §1.1.

> **Mental model.** `docker compose` brings up four containers — `db`, `backend`, `metabase`,
> `frontend` — each bound to **`127.0.0.1`** only. The **host's own nginx** (installed on the VM, not
> in Docker) terminates TLS and reverse-proxies to those local ports. Nothing in Docker is exposed to
> the public network directly.

```
                         ┌──────────────────────── Host VM ────────────────────────┐
  Internet ──443/80──►   │  nginx (host)  ──►  127.0.0.1:8080  frontend (SPA)        │
                         │                ──►  127.0.0.1:8000  backend  (gunicorn)   │
                         │                ──►  127.0.0.1:3000  metabase              │
                         │                                                            │
                         │   Docker network "internal":  backend, metabase ──► db    │
                         └────────────────────────────────────────────────────────────┘
```

---

## 7.1 Backend image — `backend/Dockerfile`

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim-bookworm

# --- System libraries -------------------------------------------------------
# WeasyPrint (PDF export) needs Pango/HarfBuzz + fonts at runtime. psycopg[binary]
# bundles libpq, so no libpq-dev is required.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libffi8 \
        libfontconfig1 libcairo2 libgdk-pixbuf-2.0-0 shared-mime-info \
        fonts-dejavu fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Collect static at build is optional; we do it at start (entrypoint) so env is available.
RUN chmod +x ./entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
```

`backend/entrypoint.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Wait for the database (simple loop; sync app, no extra deps).
echo "Waiting for database ${DB_HOST:-db}:${DB_PORT:-5432}…"
python - <<'PY'
import os, time, socket
host, port = os.getenv("DB_HOST","db"), int(os.getenv("DB_PORT","5432"))
for _ in range(60):
    try:
        socket.create_connection((host, port), timeout=2).close(); break
    except OSError:
        time.sleep(2)
else:
    raise SystemExit("Database not reachable")
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Optional one-shot seed of the reference project (idempotent). Off by default.
if [ "${SEED_ON_START:-0}" = "1" ]; then
  python manage.py seed_prdc || true
fi

exec gunicorn config.wsgi:application \
     --bind 0.0.0.0:8000 \
     --workers "${GUNICORN_WORKERS:-3}" \
     --threads "${GUNICORN_THREADS:-2}" \
     --worker-class sync \
     --timeout "${GUNICORN_TIMEOUT:-120}" \
     --access-logfile - --error-logfile -
```

> **Sync, on purpose.** `--worker-class sync` with a few workers/threads is all this volume needs
> (`01_architecture.md` §1.2). Exports run in-request; `--timeout 120` covers a large PDF/Excel.

---

## 7.2 Frontend image — `frontend/Dockerfile` + container nginx

```dockerfile
# frontend/Dockerfile — multi-stage: build the SPA, then serve it with nginx
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# Vite reads VITE_* from the environment at build time. Pass them as build args.
ARG VITE_API_BASE_URL=/api/v1
ARG VITE_MB_DASHBOARD_RESULTS_PHYSICAL
ARG VITE_MB_DASHBOARD_RESULTS_FRAMEWORK
ARG VITE_MB_DASHBOARD_FINANCE_CATEGORY
ARG VITE_MB_DASHBOARD_FINANCE_COMPONENT
ARG VITE_MB_DASHBOARD_PROCUREMENT
ARG VITE_MB_DASHBOARD_GRIEVANCES
ARG VITE_MB_DASHBOARD_IMPACT
ARG VITE_MB_DASHBOARD_ACTIVITIES
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
```

`frontend/nginx.conf` (the **container** nginx — serves the SPA and falls back to `index.html` for
client-side routes):

```nginx
server {
    listen 8080;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Cache hashed assets aggressively; never cache index.html.
    location /assets/ {
        try_files $uri =404;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        try_files $uri $uri/ /index.html;   # SPA fallback (React Router)
    }
}
```

> The container nginx serves **only static files**. It does **not** know about `/api`; the **host**
> nginx routes `/api` to the backend before it would ever reach the frontend container.

---

## 7.3 `docker-compose.yml`

```yaml
# docker-compose.yml
services:

  db:
    image: postgres:16
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}            # application DB, e.g. "mse"
      POSTGRES_USER: ${POSTGRES_USER}        # application owner role
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      # Passed to init.sql via psql variables:
      METABASE_DB_PASSWORD: ${METABASE_DB_PASSWORD}
      METABASE_DB_RO_PASSWORD: ${METABASE_DB_RO_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./deploy/postgres/init.sql:/docker-entrypoint-initdb.d/10-init.sql:ro
    ports:
      - "127.0.0.1:5432:5432"   # localhost only (handy for psql/backups; remove to fully isolate)
    networks: [internal]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 10

  backend:
    build: ./backend
    restart: unless-stopped
    env_file: .env
    environment:
      DB_HOST: db
      DB_PORT: "5432"
    volumes:
      - media:/app/media          # uploaded files (attachments, logos, generated reports)
      - staticfiles:/app/staticfiles
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "127.0.0.1:8000:8000"
    networks: [internal]

  metabase:
    image: metabase/metabase:latest   # pin to a specific tag in production, e.g. v0.5x.y
    restart: unless-stopped
    environment:
      MB_DB_TYPE: postgres
      MB_DB_DBNAME: metabaseappdb
      MB_DB_PORT: "5432"
      MB_DB_USER: metabase_app
      MB_DB_PASS: ${METABASE_DB_PASSWORD}
      MB_DB_HOST: db
      # Served under /metabase by the host nginx — tell Metabase its public base:
      MB_SITE_URL: ${METABASE_SITE_URL}
      JAVA_TIMEZONE: ${TZ:-UTC}
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "127.0.0.1:3000:3000"
    networks: [internal]

  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_BASE_URL: /api/v1
        VITE_MB_DASHBOARD_RESULTS_PHYSICAL:  ${VITE_MB_DASHBOARD_RESULTS_PHYSICAL:-}
        VITE_MB_DASHBOARD_RESULTS_FRAMEWORK: ${VITE_MB_DASHBOARD_RESULTS_FRAMEWORK:-}
        VITE_MB_DASHBOARD_FINANCE_CATEGORY:  ${VITE_MB_DASHBOARD_FINANCE_CATEGORY:-}
        VITE_MB_DASHBOARD_FINANCE_COMPONENT: ${VITE_MB_DASHBOARD_FINANCE_COMPONENT:-}
        VITE_MB_DASHBOARD_PROCUREMENT:       ${VITE_MB_DASHBOARD_PROCUREMENT:-}
        VITE_MB_DASHBOARD_GRIEVANCES:        ${VITE_MB_DASHBOARD_GRIEVANCES:-}
        VITE_MB_DASHBOARD_IMPACT:            ${VITE_MB_DASHBOARD_IMPACT:-}
        VITE_MB_DASHBOARD_ACTIVITIES:        ${VITE_MB_DASHBOARD_ACTIVITIES:-}
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:8080"
    networks: [internal]

volumes:
  pgdata:
  media:
  staticfiles:

networks:
  internal:
    driver: bridge
```

> **Static/media note.** WhiteNoise serves Django's collected static from inside the backend
> container, so the host nginx simply proxies `/static` and `/media` to the backend. (Alternative:
> mount the `media`/`staticfiles` volumes into the host nginx and serve them as files for slightly
> better performance. Either is fine — pick one and keep `04`/`07` consistent.)
>
> **Two dashboard-ID passes.** On the very first deploy the `VITE_MB_DASHBOARD_*` values are unknown
> (Metabase isn't provisioned yet). Bring the stack up with them empty, provision Metabase
> (`06_dashboards_metabase.md` §6.3), put the IDs in `.env`, then `docker compose build frontend &&
> docker compose up -d frontend` to rebuild the SPA with them baked in.

---

## 7.4 PostgreSQL bootstrap — `deploy/postgres/init.sql`

Runs **once**, on first cluster initialisation, as the superuser. The Postgres image already created
the application database/owner from `POSTGRES_DB`/`POSTGRES_USER`; this script adds the **second
database** for Metabase, the **Metabase app role**, and the **read-only reporting role** the
dashboards use.

```sql
-- deploy/postgres/init.sql
-- (variables METABASE_DB_PASSWORD / METABASE_DB_RO_PASSWORD are provided via env;
--  the official image substitutes them using the POSTGRES_* mechanism. If your image
--  version does not, replace the :'var' placeholders with literals or use an env_file.)

-- 1. Metabase's own metadata database + owner -------------------------------
CREATE ROLE metabase_app LOGIN PASSWORD :'METABASE_DB_PASSWORD';
CREATE DATABASE metabaseappdb OWNER metabase_app;

-- 2. Read-only role the BI tool uses to read the APPLICATION database --------
CREATE ROLE metabase_ro LOGIN PASSWORD :'METABASE_DB_RO_PASSWORD';

-- Grants on the application database (run inside it):
\connect :"POSTGRES_DB"

GRANT CONNECT ON DATABASE :"POSTGRES_DB" TO metabase_ro;
GRANT USAGE ON SCHEMA public TO metabase_ro;

-- The reporting VIEWS are created later by Django migrations; the migration that
-- creates them also GRANTs SELECT to metabase_ro (see 06 §6.1). As a safety net,
-- default privileges ensure any view the app owner creates is readable:
ALTER DEFAULT PRIVILEGES FOR ROLE :"POSTGRES_USER" IN SCHEMA public
    GRANT SELECT ON TABLES TO metabase_ro;

-- IMPORTANT: metabase_ro is intentionally NOT granted SELECT on base tables.
-- Dashboards read only the v_* reporting views.
```

> If your Postgres image tag doesn't expand `:'VAR'` from the environment inside
> `docker-entrypoint-initdb.d`, the simplest robust pattern is a tiny shell wrapper
> (`deploy/postgres/init.sh`) that `envsubst`s the SQL before piping it to `psql`. Keep the SQL above
> as the source of truth.

---

## 7.5 Host nginx — `deploy/nginx.host.conf`

This file goes on the **host** (e.g. `/etc/nginx/sites-available/me-platform`, symlinked into
`sites-enabled`). It is the single public entry point and terminates TLS.

```nginx
# deploy/nginx.host.conf

# Redirect all HTTP to HTTPS.
server {
    listen 80;
    listen [::]:80;
    server_name me-platform.example.org;          # <-- your domain
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name me-platform.example.org;           # <-- your domain

    # TLS (e.g. from certbot). Adjust paths to your certificate.
    ssl_certificate     /etc/letsencrypt/live/me-platform.example.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/me-platform.example.org/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    # Uploads (attachments, evidence photos from the field).
    client_max_body_size 25m;

    # Reasonable security headers (tune as needed).
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options SAMEORIGIN always;       # SPA frames Metabase from same origin
    add_header Referrer-Policy strict-origin-when-cross-origin always;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript application/xml image/svg+xml;
    gzip_min_length 1024;

    # --- Backend: API, Django admin, static & media ------------------------
    # proxy_pass WITHOUT a trailing path preserves the original URI (/api/..., etc.)
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;            # large in-request exports
    }
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /static/ {
        proxy_pass http://127.0.0.1:8000;   # served by WhiteNoise
        proxy_set_header Host $host;
    }
    location /media/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # --- Metabase (under /metabase) ----------------------------------------
    # MB_SITE_URL in compose is set to https://<host>/metabase so Metabase
    # generates correct subpath URLs; nginx forwards the full /metabase/ URI.
    location /metabase/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # --- Frontend SPA (everything else) ------------------------------------
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host              $host;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

> **Why the SPA can iframe Metabase:** both are served from the **same origin**
> (`https://me-platform.example.org`), so `X-Frame-Options: SAMEORIGIN` is satisfied and no
> cross-origin embedding configuration is needed. If you ever serve Metabase on a different host, set
> Metabase's *Embedding → Authorized origins* and relax the frame headers accordingly.

---

## 7.6 Environment contract — `.env.example`

```dotenv
# ===== PostgreSQL =====
POSTGRES_DB=mse
POSTGRES_USER=mse_app
POSTGRES_PASSWORD=change-me-strong
# Metabase DB roles (created by init.sql)
METABASE_DB_PASSWORD=change-me-strong
METABASE_DB_RO_PASSWORD=change-me-strong

# ===== Django backend =====
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=change-me-50-random-chars
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=me-platform.example.org
# CSRF/CORS — the SPA is same-origin, so this is mostly the public URL:
CSRF_TRUSTED_ORIGINS=https://me-platform.example.org
CORS_ALLOWED_ORIGINS=https://me-platform.example.org

# Database connection (entrypoint also injects DB_HOST=db, DB_PORT=5432)
DB_NAME=mse
DB_USER=mse_app
DB_PASSWORD=change-me-strong

# JWT lifetimes (minutes / days)
JWT_ACCESS_MINUTES=30
JWT_REFRESH_DAYS=7

# Gunicorn (sync)
GUNICORN_WORKERS=3
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=120

# Seed the reference project automatically on first start (0/1)
SEED_ON_START=0

# ===== Metabase embedding =====
METABASE_SITE_URL=https://me-platform.example.org/metabase
METABASE_EMBEDDING_SECRET=paste-after-enabling-static-embedding

# ===== Frontend build (dashboard IDs filled after Metabase provisioning) =====
VITE_MB_DASHBOARD_RESULTS_PHYSICAL=
VITE_MB_DASHBOARD_RESULTS_FRAMEWORK=
VITE_MB_DASHBOARD_FINANCE_CATEGORY=
VITE_MB_DASHBOARD_FINANCE_COMPONENT=
VITE_MB_DASHBOARD_PROCUREMENT=
VITE_MB_DASHBOARD_GRIEVANCES=
VITE_MB_DASHBOARD_IMPACT=
VITE_MB_DASHBOARD_ACTIVITIES=

# Misc
TZ=UTC
```

> `DJANGO_SETTINGS_MODULE`, `DB_*`, `JWT_*`, CORS/CSRF and the Metabase variables are consumed by
> `config/settings/prod.py` (and `base.py`) per `04_backend_spec.md` §4.2. Currency and locale are
> **not** here — they are per-`Project` fields in the database (`01_architecture.md` §1.6).

---

## 7.7 Scheduled tasks without a worker

The only periodic needs (e.g. reminder e-mails that a period's data is due, or a nightly refresh of a
materialised view if you later choose to materialise) are Django **management commands** triggered by
the **host crontab** — consistent with the "no Celery" decision.

```cron
# /etc/cron.d/me-platform   (host)
# Daily 06:00 — send "measurements due" reminders for the current period.
0 6 * * *  root  cd /opt/me-platform && docker compose exec -T backend python manage.py send_due_reminders >> /var/log/me-platform-cron.log 2>&1
```

(Implement `send_due_reminders` only if/when needed; listed here so the operational model is explicit.)

---

## 7.8 Runbook

### First deploy

1. Install Docker + Compose v2 and nginx on the host. Obtain a TLS cert (certbot).
2. `git clone` the repo to e.g. `/opt/me-platform`. `cp .env.example .env` and fill secrets.
3. Put `deploy/nginx.host.conf` into nginx (`sites-available` → symlink `sites-enabled`), set your
   domain and cert paths, `sudo nginx -t && sudo systemctl reload nginx`.
4. `docker compose up -d db` → wait healthy (init.sql creates `metabaseappdb`, `metabase_app`,
   `metabase_ro`).
5. `docker compose up -d backend` → entrypoint runs `migrate` + `collectstatic` (this also **creates
   the `v_*` reporting views** and grants them to `metabase_ro`).
6. Create an admin user: `docker compose exec backend python manage.py createsuperuser`.
7. Seed the reference project: `docker compose exec backend python manage.py seed_prdc`
   (idempotent — the **only** place PRDC values exist; see `02_domain_and_data_model.md`). For a
   different project, skip this and configure via the admin screens instead.
8. `docker compose up -d metabase`. Provision it per `06_dashboards_metabase.md` §6.3 (add the
   read-only DB, enable static embedding → copy secret into `.env` as
   `METABASE_EMBEDDING_SECRET`, build dashboards, note their IDs).
9. Put the dashboard IDs and the embedding secret in `.env`. Rebuild the SPA with the IDs baked in
   and (re)start everything:
   `docker compose build frontend && docker compose up -d`.
10. Smoke test: open `https://<host>/`, log in, confirm a dashboard renders inside the app, and that
    `https://<host>/api/v1/docs/` (Swagger) loads.

### Backups

- **Application data:** `docker compose exec -T db pg_dump -U $POSTGRES_USER $POSTGRES_DB > mse-$(date +%F).sql`
- **Metabase metadata:** `pg_dump … metabaseappdb` (dashboards/questions live here).
- **Uploaded files:** back up the `media` Docker volume (`docker run --rm -v me-platform_media:/m -v $PWD:/out alpine tar czf /out/media-$(date +%F).tgz -C /m .`).
- Schedule these via host cron; keep offsite copies. Test a restore periodically.

### Upgrades

- **App:** `git pull`, `docker compose build backend frontend`, `docker compose up -d`. Migrations run
  automatically on backend start; review the migration plan first on a staging copy.
- **Metabase:** bump the pinned image tag, `docker compose pull metabase && docker compose up -d
  metabase`. It self-migrates `metabaseappdb`. **Pin a specific tag in production** (avoid `latest`)
  so upgrades are deliberate.
- **PostgreSQL major upgrade:** dump → upgrade image → restore (standard PG procedure); never just
  swap the major version over an existing data volume.

### Logs & health

- `docker compose logs -f backend` (gunicorn access/error to stdout), `… metabase`, `… db`.
- `docker compose ps` shows health; the `db` healthcheck gates `backend`/`metabase` startup.
- nginx access/error logs on the host (`/var/log/nginx/`).

### Tuning (only if needed)

- Raise `GUNICORN_WORKERS`/`GUNICORN_THREADS` if concurrent users grow; this stays a **sync** server.
- If a particular export gets heavy, increase `proxy_read_timeout` in nginx and `GUNICORN_TIMEOUT`
  together. Do **not** introduce Celery for v1 — stream the response instead.

---

## 7.9 Acceptance criteria for deployment

- `docker compose up -d` brings up four healthy containers, all bound to `127.0.0.1`.
- The host nginx serves the SPA at `/`, proxies `/api`, `/admin`, `/static`, `/media` to the backend,
  and `/metabase` to Metabase — all over HTTPS.
- A fresh database has two databases (`mse`, `metabaseappdb`) and the `metabase_ro` role can read the
  `v_*` views but **not** base tables.
- `seed_prdc` populates the reference project idempotently; re-running changes nothing.
- An embedded dashboard renders inside the app, scoped to the selected project.
