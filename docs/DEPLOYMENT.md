# Deploying to Render

This app is already production-ready per the repo's existing `Dockerfile` and
`config/settings/prod.py` (WhiteNoise-served static files, forced PostgreSQL, HTTPS security
settings). This guide walks through deploying that same image to
[Render](https://render.com), which offers a free tier suitable for a portfolio deployment.

> Render's dashboard and free-tier plan names change over time. If a step below doesn't match
> what you see, use it as a guide rather than a literal script — the underlying requirements
> (a Postgres database, a Redis/cache instance, and the env vars below) won't change.

## Before you deploy

Update the placeholder addresses in the source before going live:

- `config.settings.base.PROJECT_METADATA["CONTACT_EMAIL"]` — currently `admin@example.com`.
- `config.settings.prod.ADMINS` — currently `["admin@example.com"]`. This is where signup
  notifications (`apps/users/signals.py::_notify_admins_of_signup`) and error reports are sent.

## Why Redis is required even without a background worker

`config/settings/prod.py` switches Django's cache backend to Redis unconditionally whenever
`DEBUG=False` — this is independent of Celery. `CELERY_TASK_ALWAYS_EAGER=True` (used in this
deployment) means Celery tasks run synchronously in the web process, so **no separate worker
service is needed** — but a reachable Redis instance is still required for `REDIS_URL`, purely
for Django's cache. Render's free Redis/Key-Value plan is sufficient for this (no persistence
needed since it's cache-only).

## Option A — Blueprint (`render.yaml`)

1. Push this repo to GitHub (if you haven't already).
2. In the Render dashboard, choose **New +** → **Blueprint**, and point it at your repo. Render
   reads `render.yaml` from the repo root and proposes the services it defines (a free Postgres
   database, a free Redis instance, and a Docker web service).
3. Review the proposed plan, then apply it. Render will generate `SECRET_KEY` automatically and
   wire `DATABASE_URL` / `REDIS_URL` from the database/Redis resources it creates.
4. Once the first deploy finishes, open the web service's **Environment** tab and set
   `ALLOWED_HOSTS` to the `*.onrender.com` URL Render assigned you (and any custom domain you
   add later), e.g. `learning-platform.onrender.com`.
5. Trigger a redeploy so the new `ALLOWED_HOSTS` value takes effect.

If Render reports a schema error on `render.yaml`, fall back to Option B — Render's Blueprint
spec has evolved and this file may need small adjustments for your account's current plan
names.

## Option B — Manual setup via the dashboard

1. **Database:** New + → PostgreSQL. Pick the free plan. Once created, copy its **Internal
   Database URL** — you'll use it as `DATABASE_URL`.
2. **Cache:** New + → Redis (or "Key Value", depending on what Render currently calls it). Pick
   the free plan. Copy its internal connection URL for `REDIS_URL`.
3. **Web service:** New + → Web Service → connect your repo → choose **Docker** as the
   environment (Render will use the repo's `Dockerfile` directly, no build command needed).
4. Under **Environment**, add:

   | Key | Value |
   |-----|-------|
   | `DJANGO_SETTINGS_MODULE` | `config.settings.prod` |
   | `SECRET_KEY` | a long random string (`python -c "import secrets; print(secrets.token_urlsafe(64))"`) |
   | `DEBUG` | `False` |
   | `ALLOWED_HOSTS` | your Render URL, e.g. `learning-platform.onrender.com` |
   | `USE_HTTPS_IN_ABSOLUTE_URLS` | `True` |
   | `CELERY_TASK_ALWAYS_EAGER` | `True` |
   | `DATABASE_URL` | the Postgres Internal Database URL from step 1 |
   | `REDIS_URL` | the Redis/Key-Value connection URL from step 2 |

5. Deploy. The image's `CMD` (defined in the `Dockerfile` itself, not `docker-compose.yml`)
   runs `migrate` + `collectstatic` before starting gunicorn on every container start, so this
   happens automatically on Render without any extra configuration — no `startCommand` override
   needed in `render.yaml`.
6. Once live, create an instructor account: sign up normally (defaults to Student), then open
   `https://<your-app>.onrender.com/admin/`, log in with a superuser (see below), and edit that
   user's inline **Profile** to set **Role = Instructor**.

## Creating a superuser on Render

Render's free web services don't offer a persistent shell, so `createsuperuser` can't be run
interactively. Instead, set `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD` in the
web service's **Environment** tab (or via `render.yaml`'s `sync: false` prompts if using the
Blueprint) and redeploy. On startup, the container runs
`python manage.py create_superuser_from_env`
(`apps/users/management/commands/create_superuser_from_env.py`), which:

- Creates exactly one superuser with that email/password, if no user with that email exists yet.
- No-ops on every subsequent deploy once the account exists — it never touches an existing
  account's password, so it's safe to leave the env vars set indefinitely.
- Never writes the password to logs.

After the first successful deploy: log in at `/admin/`, change the password from the admin UI
(your own, not the bootstrap one — treat the env var password as a one-time bootstrap secret),
then optionally remove `DJANGO_SUPERUSER_EMAIL` / `DJANGO_SUPERUSER_PASSWORD` from Render's
Environment tab. Removing them doesn't affect the account that was already created — they're
only consulted when no matching user exists yet.

Don't use `DEV_SUPERUSER_EMAIL`/`DEV_SUPERUSER_PASSWORD` for this — those are consumed by
`apps/web`'s custom `runserver` command and are gated on `DEBUG=True`, so they do nothing in
production (`config.settings.prod` forces `DEBUG=False`).

## Known limitation: media storage

Render's free web-service tier has **no persistent disk** — uploaded files (user avatars,
course cover images) are written to the container's local filesystem and will be **lost on the
next restart or redeploy**. This is acceptable for a portfolio demo but not for real use.

**Future improvement (not implemented in this repo):** switch `DEFAULT_FILE_STORAGE` to an
S3-compatible backend via [`django-storages`](https://django-storages.readthedocs.io/), backed
by a free-tier bucket (e.g. Cloudflare R2, Backblaze B2, or AWS S3's free tier).

## Troubleshooting: static files 500ing / "No directory at: /code/static_root/"

This means `collectstatic` never ran, so `STATIC_ROOT` (`static_root/`) doesn't exist and
WhiteNoise has nothing to serve. As of this repo, `migrate` + `collectstatic` run automatically
as part of the image's `CMD` in the `Dockerfile` itself — if you're seeing this, you're likely
running an older image built before that was added. Rebuild and redeploy; there's nothing to
configure on Render's side (no `startCommand` override needed).

## Verifying the deployment

```bash
# from your local machine, against the deployed URL
curl -I https://<your-app>.onrender.com/
curl https://<your-app>.onrender.com/manifest.json
curl https://<your-app>.onrender.com/sw.js
```

Then in a browser: register an account, confirm you land on the Student dashboard, browse
`/courses/`, and check DevTools → Application → Manifest / Service Workers to confirm the PWA
is installable.
