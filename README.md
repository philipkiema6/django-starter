# Learning Platform

> A course/lesson/enrollment learning platform built on top of the
> [django-starter](https://github.com/ChrisDevCode-Technologies/django-starter) template
> (itself inherited from [SaaS Pegasus](https://www.saaspegasus.com/)).

- **Live demo:** [LIVE_DEMO_URL]
- **Repository:** [GITHUB_URL]

## Project Overview

A small but complete Learning Management System: instructors create courses made of ordered
lessons; students browse a public catalog, enroll, work through lessons, and track their
progress. It's a portfolio project demonstrating a full authentication flow, role-based
permissions, HTMX-driven interactions on top of server-rendered Django templates, a
Tailwind/DaisyUI UI with dark mode, and basic PWA support — all built by extending the
existing starter template rather than replacing its architecture.

### Features

- Full authentication flow (registration, login, logout, password reset, password change) via
  `django-allauth`.
- User profiles with avatar upload, bio, phone number, and location.
- Three-tier access — **Admin**, **Instructor**, **Student** — with role-specific dashboards,
  navigation, and server-side permission checks.
- Instructors: create/edit/delete courses and lessons, publish courses, see enrolled students
  and their progress.
- Students: browse a paginated course catalog, enroll (HTMX, no page reload), work through
  lessons, mark lessons complete with a live-updating progress bar, and download a generated
  PDF certificate once a course is 100% complete.
- Admins: a dedicated dashboard (`/staff/`) with site-wide stats, a user directory they can
  filter by role, an "Add User" form to provision Instructor/Student accounts directly, the
  ability to activate/deactivate any account, and a searchable activity log of notable events
  across the site (signups, courses created/published, enrollments, completions, certificate
  downloads, admin actions).
- Dark mode (DaisyUI theme toggle, persisted per-browser).
- Installable PWA with offline fallback page and runtime asset caching.

### Authentication Flow

Registration, login, logout, password reset, and password change are all provided by
`django-allauth` at `/accounts/...` (see `apps/users/`) — this repo only adds the extra profile
fields and role on top. New accounts default to the **Student** role. A deactivated account
(see [User Roles](#user-roles)) is force-logged-out on its next request and can't sign back in
— see `apps/users/middleware.py::DeactivatedAccountMiddleware`.

### User Roles

| Role | How it's granted | What they can do |
|------|-------------------|-------------------|
| **Student** | Default for every new signup, or created directly by an Admin | Browse courses, enroll, complete lessons, track progress, download certificates |
| **Instructor** | An Admin promotes a user's `Profile.role` (via `/admin/`'s Profile inline, or by creating the account directly at `/staff/users/new/`) | Create/edit/delete their own courses and lessons, view enrolled students |
| **Admin** | Django `is_staff` / `is_superuser` | Everything: a dedicated dashboard, add/deactivate any account, view the full activity log, plus full Django admin access |

Permissions are enforced server-side (`apps/courses/permissions.py`, `apps/adminpanel/permissions.py`)
and reflected in the UI (role-gated navigation, 403/404 on unauthorized access).

### Admin Dashboard & Activity Log

Staff accounts land on `/staff/` instead of the regular dashboard — a distinct area, not a
themed variant of the student/instructor view. It's a thin custom UI (`apps/adminpanel/`) on
top of Django's own permission system (`is_staff`/`is_superuser`), not a reimplementation of
it — anything not covered by the custom pages (deep edits, groups/permissions) is still just a
click away at `/admin/`. Every notable event — registration, course created/published,
enrollment, lesson/course completion, certificate downloads, and admin actions (account
creation/activation/deactivation) — is written to `apps/activity/models.py::ActivityLog` from
the exact view where it happens (not inferred generically), and is browsable at `/staff/logs/`.

### Certificates

Once a student completes every lesson in a course, a "Download Certificate" button appears (on
the course's learning page and on `/courses/my-learning/`) that generates a PDF on demand —
see `apps/courses/certificates.py`. It uses `reportlab` (pure Python, no system libraries)
rather than an HTML-to-PDF renderer like WeasyPrint, which needs Pango/Cairo/GDK-Pixbuf
installed on the host. The certificate's seal is a hand-drawn vector shape, not a fabricated
logo image.

### PWA Features

- `manifest.json` (`/manifest.json`) — makes the app installable.
- A service worker (`/sw.js`) — runtime-caches static assets and serves an offline fallback
  page (`/offline/`) when navigation fails due to no network.

### Technology Stack

Django 6 · django-allauth · Django REST Framework · HTMX · Alpine.js · Tailwind CSS v4 ·
DaisyUI v5 · Vite + django-vite · SQLite (local) / PostgreSQL (production) · Celery (eager
locally) · Docker / Docker Compose (production) · WhiteNoise · ReportLab (PDF certificates).

### Folder Structure

```
apps/
  users/       CustomUser, Profile (role/bio/phone/location), allauth adapter/forms/signals,
               profile view + avatar upload, deactivation-enforcement middleware
  activity/    ActivityLog model + log_activity() helper used across apps
  courses/     Course, Lesson, Enrollment, LessonProgress models; instructor & student views;
               permissions; dashboard selectors; certificate PDF generation
  adminpanel/  Staff-only dashboard, user directory/creation/deactivation, activity log viewer
  web/         Marketing shell, authenticated dashboard, base templates, nav, PWA views
               (manifest.json, sw.js, offline page)
  utils/       Shared abstract BaseModel (created_at/updated_at)
config/
  settings/    base.py (shared), dev.py (local, default), prod.py (production overrides)
  urls.py      Root URLConf
templates/
  web/         Base layout, landing page, dashboard, nav components, PWA templates
  account/     django-allauth template overrides (login, signup, password reset/change, profile)
  courses/     Catalog, course detail, learn view, and instructor management templates
  adminpanel/  Admin dashboard, user directory/creation, activity log templates
assets/        Front-end source (JS in assets/javascript/, CSS in assets/styles/), built by Vite
static/        Built front-end output + committed assets (favicons, sw.js, offline JS)
docs/
  DEPLOYMENT.md    Step-by-step Render deployment guide
  devto-article.md Draft article for dev.to
```

### Screenshots

| Catalog | Course detail | Learning view |
|---------|----------------|----------------|
| [SCREENSHOT] | [SCREENSHOT] | [SCREENSHOT] |

| Instructor dashboard | Student dashboard | Dark mode |
|------------------------|---------------------|-----------|
| [SCREENSHOT] | [SCREENSHOT] | [SCREENSHOT] |

| Admin dashboard | Activity log | Certificate |
|------------------|----------------|--------------|
| [SCREENSHOT] | [SCREENSHOT] | [SCREENSHOT] |

### Future Improvements

- S3-compatible object storage (`django-storages`) for uploaded media, so avatars/course
  covers survive redeploys on hosts without a persistent disk (see
  [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)).
- Email an admin-created account's initial password/login link instead of the admin having to
  relay it manually — needs a real `EMAIL_BACKEND` configured (see `.env.prod.example`).
- Quizzes/assessments per lesson.
- A custom "Add to Home Screen" install-prompt button (currently relies on the browser's
  native install UI).
- Rich-text/Markdown lesson content instead of plain text.

### License

MIT — see [LICENSE](LICENSE).

---

This project runs in **two distinct modes**:

| Mode | How it runs | Database | Cache / broker | Celery | Used for |
|------|-------------|----------|----------------|--------|----------|
| **Local** | Natively on your machine via [uv](https://docs.astral.sh/uv/) + `npm` | SQLite (`db.sqlite3`) | DummyCache (no Redis needed) | Eager (synchronous) | Day-to-day development |
| **Production** | Docker Compose (Postgres + Redis + web + Vite + Celery) | Postgres | Redis | Real worker + beat | Containerized / deployed stack |

The split is driven by `DEBUG` and a few environment variables — see [Configuration](#configuration). You do
**not** need Docker for everyday development.

---

## Table of contents

- [Project Overview](#project-overview)
- [Admin Dashboard & Activity Log](#admin-dashboard--activity-log)
- [Certificates](#certificates)
- [Local development](#local-development)
  - [Prerequisites](#prerequisites)
  - [1. Bootstrap](#1-bootstrap-make-init)
  - [2. Admin user](#2-admin-user-automatic)
  - [3. Run the app (two processes)](#3-run-the-app-two-processes)
  - [4. Open it](#4-open-it)
- [Everyday commands](#everyday-commands)
- [Database](#database)
- [Front end](#front-end)
- [Generating the API client](#generating-the-api-client)
- [Celery & background tasks](#celery--background-tasks)
- [Testing](#testing)
- [Code quality & git hooks](#code-quality--git-hooks)
- [Configuration](#configuration)
- [Production](#production)

---

## Local development

Local development runs **natively** on your Python environment (managed with
[uv](https://docs.astral.sh/uv/)) against a **SQLite** database. No Docker, Postgres, or Redis
required.

### Prerequisites

Install these once on your machine:

- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** — manages the virtual environment
  and provisions Python 3.14 for you (you do **not** need to install Python 3.14 separately):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh   # or: brew install uv
  ```
- **[Node.js](https://nodejs.org/) 20+** — provides `node` and `npm` for the front-end build.
- **`make`** — preinstalled on macOS/Linux. On Windows,
  [follow these instructions](https://stackoverflow.com/a/57042516/8207).

### 1. Bootstrap (`make init`)

From the project root:

```bash
make init
```

This single command:

1. Copies `.env.example` → `.env` (only if `.env` doesn't already exist).
2. Installs Python dependencies into a local `.venv` with `uv sync`.
3. Installs front-end dependencies with `npm install`.
4. Creates the SQLite database (`db.sqlite3`) and applies all migrations.

### 2. Admin user (automatic)

In `DEBUG`, `make start` (i.e. `runserver`) **automatically creates a development superuser** the
first time it runs, then silently skips it afterwards. Defaults:

| Field    | Value               |
|----------|---------------------|
| Email    | `admin@example.com` |
| Password | `admin`             |

Override via `DEV_SUPERUSER_EMAIL` / `DEV_SUPERUSER_PASSWORD` in `.env`. This only happens when
`DEBUG` is true, so production is never affected. You can still create more accounts with
`make manage ARGS='createsuperuser'`.

### 3. Run the app (two processes)

Local development needs **two terminals running simultaneously** — the Django server *and* the Vite
front-end server. In `DEBUG`, CSS/JS are served by Vite, so **if you skip the second process the page
loads unstyled.**

**Terminal 1 — Django backend (port 8000):**

```bash
make start
```

**Terminal 2 — Vite front end (port 5173):**

```bash
make npm-dev
```

### 4. Open it

Visit **[http://localhost:8000](http://localhost:8000/)** — you should see a fully styled page. The
Django admin is at [http://localhost:8000/admin/](http://localhost:8000/admin/) (log in with the
auto-created dev superuser from step 2).

> **Styles not loading?** It almost always means the Vite dev server (step 3, Terminal 2) isn't
> running, or `node_modules` is missing. Run `make npm-install` then `make npm-dev` and refresh.

New to Pegasus? [Try these next steps](https://docs.saaspegasus.com/getting-started/#post-installation-steps).

---

## Everyday commands

Run `make` with no arguments to list every available target. Local targets (`start`, `migrate`,
`test`, `shell`, …) run natively via `uv`; production targets are prefixed with `prod-` and use Docker.

| Command | What it does |
|---------|--------------|
| `make start` | Run the Django dev server |
| `make shell` | Open a Django Python shell |
| `make dbshell` | Open a database shell (SQLite locally) |
| `make manage ARGS='<cmd>'` | Run any `manage.py` command, e.g. `ARGS='createsuperuser'` |
| `make migrations` | Create new migrations |
| `make migrate` | Apply migrations |
| `make test` | Run the test suite |
| `make ruff` | Format **and** lint Python with Ruff |
| `make npm-dev` | Run the Vite dev server |
| `make npm-build` | Build production front-end assets |

Management commands can also be run directly: `uv run python manage.py <command>`.

---

## Database

Local development uses **SQLite** by default — no setup required. Leaving `DATABASE_URL` unset makes
Django use the `db.sqlite3` file in the project root.

```bash
make migrations   # uv run python manage.py makemigrations
make migrate      # uv run python manage.py migrate
```

In production, set `DATABASE_URL` (e.g. a Postgres connection string) in the environment — it takes
precedence over SQLite automatically.

---

## Front end

JavaScript/TypeScript lives in `assets/` and is bundled by [Vite](https://vitejs.dev/) and served
through [`django-vite`](https://github.com/MrBin99/django-vite). Tailwind v4 + DaisyUI provide styling.

```bash
make npm-install            # install all npm packages
make npm-install <package>  # install a specific package
make npm-dev                # Vite dev server with hot reload (local development)
make npm-build              # build optimized assets (production)
make npm-type-check         # TypeScript type checking
```

In `DEBUG`, `DJANGO_VITE["default"]["dev_mode"]` is `True`, so assets are served live from the Vite
dev server. With `DEBUG=False`, Django serves the built manifest from `npm-build` instead.

---

## Generating the API client

The REST API (Django Rest Framework) publishes an OpenAPI schema via `drf-spectacular` at
`/api/schema/`. The TypeScript client in `api-client/` is **generated from that schema** and consumed
by the front end (see `assets/javascript/api.js`). It is generated code — don't edit it by hand.

Whenever you add or change API endpoints, regenerate the client:

```bash
make generate-api-client
```

This target:

1. Exports the OpenAPI schema from Django (`manage.py spectacular`).
2. Runs [OpenAPI Generator](https://openapi-generator.tech) (`typescript-fetch`), pinned to the
   version in `OPENAPI_GENERATOR_VERSION` (kept in sync with `api-client/.openapi-generator/VERSION`),
   via `npx @openapitools/openapi-generator-cli`.
3. Writes the result into `api-client/` and cleans up the temporary schema file.

**Requirements:** `node`/`npx` and a Java runtime (the generator runs on the JVM). Review the diff
before committing.

---

## Celery & background tasks

Celery runs background and scheduled tasks. **Locally, tasks run eagerly (synchronously)** by default
(`CELERY_TASK_ALWAYS_EAGER` defaults to `DEBUG`), so **no broker is required**.

To exercise the real worker locally, run a Redis instance, set `REDIS_URL` in `.env`, then:

```bash
make celery
# or directly:
uv run celery -A config worker -l INFO --beat --pool=solo
```

> The `solo` pool is fine for development but **not** for production.

In production (`DEBUG=False`) tasks dispatch to the Redis broker and are processed by the dedicated
`celery` container (see [Production](#production)).

---

## Testing

```bash
make test                                              # run everything
make test ARGS='apps.web.tests.test_basic_views'       # a single module
make test ARGS='apps.web.tests.test_basic_views --keepdb'  # reuse the test DB (faster)
```

On Linux you can re-run tests on change:

```bash
find . -name '*.py' | entr uv run python manage.py test apps.web.tests.test_basic_views
```

---

## Code quality & git hooks

```bash
make ruff           # ruff format + lint --fix
make ruff-format    # format only
make ruff-lint      # lint + autofix only
make type-check     # mypy
```

Install the pre-commit hooks (run automatically on every commit):

```bash
uv run pre-commit install --install-hooks
```

See the [Pegasus code-formatting docs](https://docs.saaspegasus.com/code-structure#code-formatting)
for details.

---

## Configuration

Configuration is read from environment variables (via `.env` locally). `make init` /
`make setup-env` copy `.env.example` → `.env` for you. The most important variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `SECRET_KEY` | insecure dev key | Django secret key. **Set a strong value in production.** |
| `DEBUG` | `True` | Debug mode. **Must be `False` in production** (or use `config.settings.prod`). |
| `ALLOWED_HOSTS` | `*` | Comma-separated allowed hosts. Restrict in production. |
| `DATABASE_URL` | *(unset → SQLite)* | Postgres connection string in production. |
| `REDIS_URL` | *(unset → `redis://localhost:6379/0`)* | Cache + Celery broker. Required in production. |
| `CELERY_TASK_ALWAYS_EAGER` | `= DEBUG` | Run tasks synchronously when true. |
| `DEV_SUPERUSER_EMAIL` / `DEV_SUPERUSER_PASSWORD` | `admin@example.com` / `admin` | Auto-created dev superuser (DEBUG only). |
| `ENABLE_DEBUG_TOOLBAR` | `False`¹ | Django Debug Toolbar (disabled during tests). |
| `EMAIL_BACKEND` | console backend | Email backend; configure a real one (e.g. Mailgun/Anymail) in production. |
| `DJANGO_PORT` / `DJANGO_VITE_PORT` | `8000` / `5173` | Dev server ports. |
| `POSTGRES_PORT` / `REDIS_PORT` | `5432` / `6379` | Docker service ports. |
| `TURNSTILE_KEY` / `TURNSTILE_SECRET` | *(empty)* | Cloudflare Turnstile keys (optional). |
| `GOOGLE_ANALYTICS_ID` | *(empty)* | GA measurement ID (optional). |

¹ `.env.example` ships with `ENABLE_DEBUG_TOOLBAR=True` for convenience.

> Never commit `.env` — it's git-ignored. See `.env.example` for the full, annotated list.

**Settings modules:** live in the `config/settings/` package.

- `config.settings.base` — shared settings imported by both environment modules. Not selected directly.
- `config.settings.dev` — the default, used everywhere unless overridden. `DEBUG` defaults to `True`.
- `config.settings.prod` — imports everything from `base`, then forces `DEBUG=False`
  and enables the security hardening (SSL redirect, secure cookies, HSTS scaffolding, etc.). Select it
  in production via `DJANGO_SETTINGS_MODULE=config.settings.prod`.

---

## Production

Docker Compose runs a production-ready stack — **Postgres, Redis, a gunicorn web server, and a
Celery worker (with beat)**. The web and Celery services share one image built from `Dockerfile`
(a multi-stage build that compiles the front-end assets with Vite, then installs the production
Python dependencies) and run with `DJANGO_SETTINGS_MODULE=config.settings.prod`.

**Requirements:** [Docker](https://www.docker.com/get-started) and
[Docker Compose](https://docs.docker.com/compose/install).

### 1. Configure secrets

```bash
make setup-env-prod    # copies .env.prod.example -> .env.prod (git-ignored)
```

Edit `.env.prod` and set real values — at minimum `SECRET_KEY`, `ALLOWED_HOSTS`,
`POSTGRES_PASSWORD` / `DATABASE_URL`, and `REDIS_URL`. `DEBUG=False` is required (see the notes in
the file). For real email, configure `EMAIL_BACKEND` and its credentials (e.g. Mailgun via Anymail).

### 2. Build and run

```bash
make prod-build                    # build the production image
make prod-start                    # start the stack (foreground)
make prod-start-bg                 # start the stack (background)
make prod-stop                     # stop the stack
make prod-restart                  # stop + start
make prod-ssh                      # shell into the running web container
make prod-manage ARGS='migrate'    # run a manage.py command in the web container
```

On startup the `web` service **applies migrations and runs `collectstatic` automatically**, then
serves the app with gunicorn on port `8000`. Static files are served directly by the app via
[WhiteNoise](https://whitenoise.readthedocs.io/) — no separate web server is required (put a
TLS-terminating reverse proxy in front for HTTPS; the production settings honour the
`X-Forwarded-Proto` header).

### What the stack contains

`docker-compose.yml` defines four services:

| Service | Image / build | Role |
|---------|---------------|------|
| `db` | `postgres:17` | Postgres database (persisted in the `postgres_data` volume) |
| `redis` | `redis:7` | Cache + Celery broker (persisted in `redis_data`) |
| `web` | `Dockerfile` | Django app under gunicorn on port `8000` (runs migrate + collectstatic on boot) |
| `celery` | `Dockerfile` | Celery worker + beat |

Uploaded media persists in the `media_files` volume. `MY_UID` / `MY_GID` (in the `Makefile`) set the
container user/group so files created in mounted volumes belong to your host user rather than `root`.
The defaults (`1000`) suit most setups.

### Before going live

Validate the deployment settings:

```bash
make prod-manage ARGS='check --deploy'
```

Consider also enabling HSTS (see the commented block in `config/settings/prod.py`) once you're
confident HTTPS works, and scaling `GUNICORN_WORKERS` in `.env.prod` to `(2 × CPU cores) + 1`.

### Deploying to Render

This repo includes a `render.yaml` Blueprint for deploying the existing `Dockerfile` + a free
Postgres database to [Render](https://render.com) at no cost. See
**[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** for the full step-by-step guide, required env vars,
and known limitations of the free tier (no persistent disk for uploaded media).

---

*Built with [SaaS Pegasus](https://www.saaspegasus.com/), the Django SaaS boilerplate.*
