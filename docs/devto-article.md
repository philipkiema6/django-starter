<!--
Draft for dev.to. Paste the body below into the dev.to editor (everything after the
front-matter block, or the whole thing if you're using the dev.to CLI / forem front-matter
format). Replace every [BRACKETED] placeholder before publishing.
-->

---
title: "Building a Learning Platform on Top of a Django SaaS Starter Template"
published: false
tags: django, python, htmx, webdev
cover_image: [COVER_IMAGE_URL]
---

## Introduction

For this project, the brief was open-ended: start from an existing Django starter template,
build a complete authentication flow with user profiles and role-based access, and ship a
"real" application on top of it — not a toy CRUD demo. I chose a **Learning Platform**:
instructors create courses made of ordered lessons, students browse a catalog, enroll, and
track their progress lesson by lesson.

This post walks through how it's built: the starter template I started from, the decisions I
made extending it, and what I learned along the way.

- **Live demo:** [LIVE_DEMO_URL]
- **Source code:** [GITHUB_URL]

## Planning

Before writing any code, the brief was: two roles, a real authentication flow, image uploads,
a modern UI with dark mode, PWA features, and a production deployment. Rather than pick a
domain first and figure out the roles afterward, I worked backwards from what would let two
roles do genuinely different, meaningful things — an Instructor/Student pair maps naturally
onto a learning platform in a way that, say, "Admin/User" on a generic CRUD app doesn't. That
became the anchor decision everything else was planned around.

## Understanding the Starter Template

The starter is a Pegasus-derived Django SaaS boilerplate — Django + `django-allauth` +
Django REST Framework + HTMX + Alpine.js + Tailwind CSS v4 + DaisyUI + Vite, wired together and
ready to run natively via `uv` and `npm` (no Docker needed for local development; Docker is
reserved for the production stack). Before writing anything, I audited what already existed:

- **Authentication** was essentially done. `django-allauth` was already configured for
  email-only login, with full template overrides for login, signup, logout, password reset,
  and password change. This was a big time-saver — the "complete authentication flow"
  requirement was mostly a verification exercise, not a build.
- **Profile updates** already existed (name, email, avatar upload with validation), but there
  was no `Profile` model, no `bio`/`phone`/`location`, and no concept of a role.
- **No example CRUD app** existed to copy patterns from — the two existing apps (`users`,
  `web`) are infrastructure, not features. Building `courses` meant establishing the first
  "real" feature-app pattern in the repo.
- **No dark mode, no PWA** — both had to be built from scratch, though the pieces
  (Tailwind config, DaisyUI, a service-worker-friendly static file setup) were already in
  place to make it straightforward.

The lesson here: **read before you write**. A lot of the "authentication flow" and "profile
update" requirements were already satisfied by the template; the actual net-new work was
narrower and more specific than the brief initially suggested.

## Project Architecture

I added one new Django app, `apps/courses`, with four models:

```python
class Course(BaseModel):
    instructor = models.ForeignKey(CustomUser, ...)
    title, slug, description, cover_image, is_published

class Lesson(BaseModel):
    course = models.ForeignKey(Course, ...)
    title, content, order

class Enrollment(BaseModel):
    student = models.ForeignKey(CustomUser, ...)
    course = models.ForeignKey(Course, ...)
    # progress_percent is a computed property, not a stored field

class LessonProgress(BaseModel):
    enrollment = models.ForeignKey(Enrollment, ...)
    lesson = models.ForeignKey(Lesson, ...)
    completed_at
```

`progress_percent` on `Enrollment` is deliberately a Python property
(`completed_lessons / total_lessons`), not a stored, denormalized field — one less thing that
can drift out of sync.

The app follows the starter's existing conventions: function-based views (Django REST
Framework is available in the project but I didn't reach for it here — more on that below),
`ModelForm`s, the Django messages framework for feedback, and a shared abstract `BaseModel`
(just `created_at`/`updated_at`) that the starter shipped but nothing had used yet.

### Why HTMX instead of a REST API

The starter has DRF fully wired (an OpenAPI schema, an auto-generated TypeScript client). It
would have been easy to build a `courses` API and drive the UI with `fetch()` calls. I didn't,
for two reasons: the app's two genuinely dynamic interactions — enrolling in a course, marking
a lesson complete — are small, single-purpose actions that don't need a general-purpose API
surface, and the template already leans on HTMX for exactly this kind of thing (there's a
global `hx-on::response-error` handler and an HTMX pagination component already in the base
templates). Reaching for DRF here would have meant building and maintaining two parallel
interfaces to the same data for no real benefit. The "enroll" button is a single
`hx-post` that swaps itself for a "Continue Learning" link; marking a lesson complete does an
HTMX out-of-band swap that updates both the completion badge *and* the sidebar progress bar
from one response.

## Authentication Implementation

As covered above, this was mostly already there. What I verified/exercised: registration
(defaults every new account to the Student role via a `post_save` signal), login, logout,
password reset (email-based, via allauth), password change, and profile update. I didn't touch
allauth's configuration — the existing `EmailAsUsernameAdapter` and custom signup form chain
(a honeypot + optional Cloudflare Turnstile captcha + terms-of-service checkbox) were already
solid.

## User Profiles

I added a `Profile` model (`OneToOneField` to `CustomUser`) rather than bolting fields onto the
user model directly, holding `role`, `bio`, `phone_number`, and `location`. It intentionally
does *not* duplicate `first_name`/`last_name`/`avatar`, which already live on `CustomUser` —
one representation of "the user's name" and "the user's picture," not two.

```python
@receiver(post_save, sender=CustomUser)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
```

Every new user gets a `Profile` the instant their account is created, defaulting to the
Student role. Existing users (from before this migration) are backfilled via a `RunPython`
data migration in the same migration file that adds the model — worth remembering if you're
retrofitting a "give every user a related object" pattern onto a project with existing data.

## Role-Based Access

Two roles, Instructor and Student, stored as `Profile.role`. New accounts default to Student.
An Instructor is *promoted*, not self-selected at signup — a staff user does this from Django's
built-in admin, editing the `Profile` inline on the user's admin page. That admin surface also
doubles as the "Admin" capability the brief asked for: I didn't build a custom admin dashboard,
because Django's admin already provides staff-gated CRUD for users, courses, and enrollments
out of the box. Building a parallel one would have been pure duplication.

Permission enforcement is a small decorator, not Django Groups or a permissions framework —
the two roles are simple enough that a `role` field plus one decorator covers it:

```python
def instructor_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.profile.is_instructor:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped
```

Course ownership is checked inline (`get_object_or_404(Course, slug=slug,
instructor=request.user)`), returning a 404 rather than a 403 for another instructor's course —
standard practice to avoid leaking whether a resource exists to someone who shouldn't see it.

## Frontend Development

The dashboard, navigation, forms, tables, and empty states all extend the starter's existing
`web/app/app_base.html` (sidebar + content shell) rather than introducing a parallel layout
system. The home dashboard now branches on `profile.is_instructor` to show course stats and a
"create course" CTA, or enrolled-course cards with progress bars, reusing the same template
that used to just say "You're Signed In!"

## Tailwind CSS & Dark Mode

The starter uses Tailwind v4 with DaisyUI v5, but shipped with a single hardcoded
`data-theme="light"` and no toggle. DaisyUI v5 configures multiple themes directly in CSS:

```css
@plugin "daisyui" {
  themes: light --default, dark --prefersdark;
}
```

The toggle itself is a few lines of Alpine-friendly JS persisting the choice to
`localStorage`, plus a small inline script in the page `<head>` that applies the stored theme
*before* first paint — otherwise you get a flash of the wrong theme on every page load. One
subtlety: the project's Tailwind config uses the `class` dark-mode strategy for its own
`dark:` utility variants, which is separate from DaisyUI's `data-theme` attribute. The toggle
sets both together so the two systems stay in sync.

## PWA Implementation

Two features, kept deliberately minimal: an installable manifest and a service worker with an
offline fallback page.

The trickiest part wasn't the service worker logic itself (a straightforward cache-first
strategy for static assets, network-first-with-offline-fallback for page navigations) — it was
**scope**. A service worker's default scope is the directory it's served from. My first
instinct was to drop `sw.js` straight into the `static/` folder (consistent with how favicons
are already served) and register it at `/static/sw.js` — which would have quietly limited it to
only controlling requests under `/static/`, never intercepting actual page navigations. The
fix: keep the source file in `static/` for convenience, but serve it at the site root (`/sw.js`)
through a thin Django view, so its scope covers the whole site.

## Deployment

The starter already ships a production-ready `Dockerfile` and `docker-compose.yml`
(Postgres + Redis + gunicorn + a Celery worker), plus a `config/settings/prod.py` that forces
`DEBUG=False`, requires Postgres, and turns on WhiteNoise + HTTPS security settings. Deploying
to [Render](https://render.com) reuses that same `Dockerfile` directly — no separate build
pipeline needed.

One thing worth calling out: I initially planned to drop Redis entirely from the deployment,
since this app has no background/scheduled tasks. That turned out to be wrong —
`config/settings/prod.py` switches Django's *cache* backend to Redis unconditionally whenever
`DEBUG=False`, independent of Celery. So Redis stays, but as a small free-tier instance used
purely for caching; `CELERY_TASK_ALWAYS_EAGER=True` means no dedicated worker process is
needed. Full write-up in `docs/DEPLOYMENT.md`.

## Lessons Learned

- **Audit before building.** The single biggest time-saver on this project was spending the
  first pass reading the existing codebase instead of assuming the brief's requirements were
  all unmet. Auth, profile editing, form styling, the messages/toast system — all already
  existed.
- **A framework being available isn't a reason to use it.** DRF was there; I didn't reach for
  it, because HTMX was already the established pattern for this kind of small, page-embedded
  interaction, and adding a parallel API would have been duplicated effort for no user-facing
  benefit.
- **"Static file" and "service worker" aren't the same thing.** A service worker's scope
  rules are easy to get wrong quietly — the failure mode isn't an error, it's a service worker
  that silently never intercepts the requests you wanted it to.

## Challenges Encountered

- Getting DaisyUI v5's multi-theme config and Tailwind's separate `class`-based dark-mode
  strategy to agree with each other, rather than fighting each other.
- The Redis-for-cache-not-just-Celery discovery above, which changed the deployment topology
  midway through planning it.

## Future Improvements

- S3-compatible object storage (`django-storages`) for uploaded media — Render's free tier has
  no persistent disk, so avatars and course covers currently don't survive a redeploy.
- Per-lesson quizzes/assessments.
- A custom "Add to Home Screen" install-prompt button, instead of relying on the browser's
  native install UI.
- Markdown or rich-text lesson content instead of plain text.

## Conclusion

The constraint that mattered most on this project wasn't "what can I build" — it was "what's
already here, and what's actually missing." Extending an existing, opinionated starter template
well means resisting the urge to rebuild things it already does, and being precise about where
your own code needs to start.

- **Live demo:** [LIVE_DEMO_URL]
- **Source code:** [GITHUB_URL]

Screenshots: [SCREENSHOT: catalog page] · [SCREENSHOT: course detail] · [SCREENSHOT: learn view
with progress bar] · [SCREENSHOT: instructor dashboard] · [SCREENSHOT: dark mode]

Thanks for reading — happy to answer questions in the comments.
