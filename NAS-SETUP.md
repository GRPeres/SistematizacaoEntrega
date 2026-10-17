# NAS deployment preparation

The original CD and rollback workflows still target Render. They must be adapted
to the chosen NAS connection before they can deploy here automatically.

Prerequisite: a Linux NAS with Docker Compose v2, compatible with the image
architecture. The current build workflow publishes linux/amd64 only.

Create two **untracked** files on the NAS, `.env.staging` and `.env.production`:

```dotenv
APP_IMAGE=ghcr.io/OWNER/REPOSITORY@sha256:REPLACE_WITH_BUILD_DIGEST
DB_PASSWORD=REPLACE_WITH_UNIQUE_RANDOM_ALPHANUMERIC_PASSWORD
APP_PORT=8001
BIND_ADDRESS=127.0.0.1
```

Use a different password in each file and port 8002 for production. Alphanumeric
passwords avoid needing URL escaping in DATABASE_URL. Replace the image reference
with the exact digest published by GitHub Actions; promote the same digest to both
environments. Do not set APP_VERSION manually: it is baked into the image.

```sh
docker compose --env-file .env.staging -p cafe-staging -f compose.nas.yml pull
docker compose --env-file .env.staging -p cafe-staging -f compose.nas.yml up -d
curl --fail http://127.0.0.1:8001/health
curl --fail http://127.0.0.1:8001/version
```

After staging passes and production approval is recorded, repeat with
`.env.production`, project `cafe-production`, and port 8002. Project names keep
the database volumes separate. Configure the NAS reverse proxy for the two
application ports; loopback binding assumes the proxy runs on the NAS host.
Containerized proxies may require a shared Docker network instead.

For rollback, restore the previous known-good image digest in the production env
file, run pull and up again, and verify health/version. Application rollback does
not undo database migrations. Back up PostgreSQL before schema changes and retain
backward-compatible migrations. Never use `down -v` on these environments.

For marking, real GitHub PRs, required checks, environment approval, deployment
runs, Dependabot review, release, and DORA evidence still need to be produced.
Local preparation does not establish those results.
