# Deployment

| Environment | URLs | Runs | Database | Uploads | Deploys |
| --- | --- | --- | --- | --- | --- |
| Local | http://localhost:8000 (EN), http://127.0.0.1:8000 (PT-BR) | `manage.py runserver` | SQLite (`db.sqlite3`) | `media/` | — |
| Staging | https://staging.lavedonio.com (EN), https://staging.lavedonio.com.br (PT-BR) | Django under uWSGI on the CloudPanel VPS: Python site `staging.lavedonio.com` (site user `lavedonio-staging`, app port 8091), plus the reverse-proxy site `staging.lavedonio.com.br` (site user `lavedonio-staging-br`) in front of the same uWSGI | Schema `lavedonio_staging` | R2 bucket `lavedonio-staging`, at https://media-staging.lavedonio.com | Every push to the `staging` branch ([workflow](../.github/workflows/deploy-staging.yml)) |
| Production | https://lavedonio.com, https://lavedonio.com.br | Not set up yet (v1 still runs on Heroku) | Schema `lavedonio_production` | R2 bucket `lavedonio`, at https://media.lavedonio.com | — |

The server addresses aren't in this repository, which is public: the sites are
behind Cloudflare's proxy, which keeps the origin server's address hidden. They
are in the private infrastructure notes (`personal_terraform`) and in the deploy
workflow's secrets.

- **CloudPanel VPS** (Hostinger): nginx, uWSGI and the sites.
- **Data VPS** (Hostinger): PostgreSQL 18 in Docker, managed by Terraform
  (`personal_terraform`, module `data-platform`). Only the CloudPanel and n8n
  VPSs can reach it, and only over TLS.
- **Cloudflare**: DNS and CDN of both domains (proxied records), R2 for uploads,
  and Turnstile for the contact form.

## How a staging deploy works

```mermaid
flowchart LR
  push["git push → staging"] --> tests["Tests job"]
  tests --> deploy["Deploy job:<br/>git archive | ssh deploy &lt;sha&gt;"]
  deploy --> recv["~/bin/receive-release<br/>(forced command)"]
  recv --> rel["deploy/release.sh<br/>venv · check · migrate · collectstatic"]
  rel --> switch["current → new release<br/>touch ~/app/reload"]
  switch --> uwsgi["uWSGI reloads"]
```

1. [`deploy-staging.yml`](../.github/workflows/deploy-staging.yml) runs the
   tests ([`tests.yml`](../.github/workflows/tests.yml), which also runs on pull
   requests), then streams `git archive HEAD` over SSH as `lavedonio-staging`.
2. The deploy key in that user's `authorized_keys` is
   `restrict,command="~/bin/receive-release"`: it can't open a shell or a tunnel,
   only hand over a tarball. [`receive-release.sh`](receive-release.sh) unpacks
   it into `~/app/releases/<time>-<sha>/` and runs that release's
   [`release.sh`](release.sh).
3. `release.sh` builds a fresh `.venv` with `/usr/bin/python3.12`, runs
   `check --deploy`, `migrate`, `createcachetable` and `collectstatic`, then
   points `~/app/current` at the new release and touches `~/app/reload`. uWSGI's
   `touch-reload` re-execs it from the new release. If any step before the
   switch fails, visitors keep the old release. If the site doesn't answer after
   the switch, `current` goes back to the previous release (migrations are not
   reverted). The last 5 releases are kept.
4. The workflow then checks both public URLs.

The workflow uses the `lavedonio-staging` environment's secrets, which only the
`staging` branch can use:

| Secret | What |
| --- | --- |
| `STAGING_DEPLOY_SSH_KEY` | Private deploy key (its public half is in `lavedonio-staging`'s `authorized_keys`) |
| `STAGING_SSH_TARGET` | `lavedonio-staging@<CloudPanel VPS address>` |
| `STAGING_SSH_KNOWN_HOSTS` | The CloudPanel VPS's SSH host keys, pinned (`ssh-keyscan`, checked against the server) |

Layout on the server:

```
/home/lavedonio-staging/
  app/
    releases/<time>-<sha>/      code, .venv, staticfiles, REVISION, .env → shared/.env
    current → releases/...      what uWSGI runs
    shared/.env                 settings and secrets (0600)
    shared/postgres-ca.pem      the data VPS's Postgres certificate
    reload                      touched by each deploy
  bin/receive-release
  htdocs/staging.lavedonio.com/
    static → ~/app/current/staticfiles   served by nginx
/etc/uwsgi/apps-enabled/lavedonio-staging.ini   from deploy/uwsgi.ini (root-owned)
/var/log/uwsgi/app/lavedonio-staging.log
```

CloudPanel's Python vhost proxies every request to `127.0.0.1:8091`, where uWSGI
listens (`http-socket`), except files with a static extension (css, js, svg,
png...), which nginx serves from the document root, hence the `static` symlink.
`staging.lavedonio.com.br` is a reverse-proxy site to the same port, so it
passes everything to uWSGI and static files come from Django (WhiteNoise).
Static file names carry a hash of their content (`collectstatic` with
WhiteNoise's manifest storage), so Cloudflare and browsers can keep them for good.

Django answers both hosts (`ALLOWED_HOSTS` in `StagingSettings`, in
`env_settings.py`) and picks the language from the host. Uploads are in R2, so
the server has no `media` folder; old `/media/...` links (from posts imported
from v1) redirect to the bucket's domain.

Staging sends `X-Robots-Tag: noindex` and a `Disallow: /` robots.txt, and the
contact form's e-mails are only written to the uWSGI log.

## Everyday operations

Root commands use the key `personal_terraform` uses for the VPSs
(`~/.ssh/id_ed25519_hostinger`); in the examples, `$CLOUDPANEL` is the CloudPanel
VPS's address.

| To... | Do |
| --- | --- |
| Deploy a branch to staging | `git push origin <branch>:staging` (add `--force` to replace what staging has). Or re-run the workflow from the Actions tab. |
| See what's live | `cat ~/app/current/REVISION` as the site user |
| Read the logs | `/var/log/uwsgi/app/lavedonio-staging.log` (Django warnings and errors, and the contact form e-mails) and `~/logs/nginx/` |
| Run a management command | as root: `runuser -u lavedonio-staging -- bash -c 'cd ~/app/current/site_lavedonio_django && ../.venv/bin/python manage.py <command>'` |
| Roll back | as root: `runuser -u lavedonio-staging -- bash -c 'cd ~/app && ln -sfn releases/<older> current && touch reload'`. Migrations aren't reverted. |
| Restart uWSGI | as root: `systemctl restart uwsgi` (restarts every uWSGI app on the VPS) |
| Change a setting | edit `~/app/shared/.env` as the site user, then `touch ~/app/reload` (uWSGI loads Django only in its workers, so a reload reads it again) |

Interactive commands need `ssh -t`. For example, to create an admin user:

```bash
ssh -t -i ~/.ssh/id_ed25519_hostinger root@$CLOUDPANEL \
  "runuser -u lavedonio-staging -- bash -c 'cd ~/app/current/site_lavedonio_django && ../.venv/bin/python manage.py createsuperuser'"
```

To fill staging with fake posts and projects (they're tagged so they can be
removed), run the `create_demo_content` command, or `create_demo_content --delete`
to remove them. It refuses to run in production.

## Database

Each environment has a role and a schema of the same name in
`lavedonio_postgres`, owned by that role, with the role's `search_path` set to
it. Django also sets it (`DB_SCHEMA`). The roles can't see each other's schema.

| Role / schema | Login | Used by |
| --- | --- | --- |
| `lavedonio_staging` | yes (password in staging's `.env`) | staging |
| `lavedonio_production` | not yet | nothing yet |

They're created by hand (not by Terraform), as superuser on the data VPS
(`cd /opt/data-platform && docker compose exec postgres psql -U postgres -d lavedonio_postgres`):

```sql
CREATE ROLE lavedonio_staging LOGIN PASSWORD '...' CONNECTION LIMIT 20;
CREATE SCHEMA lavedonio_staging AUTHORIZATION lavedonio_staging;
ALTER ROLE lavedonio_staging IN DATABASE lavedonio_postgres SET search_path = lavedonio_staging;
```

Django connects with `sslmode=verify-full` against the data VPS's self-signed
certificate (`shared/postgres-ca.pem`). Terraform rotates it within 30 days of
expiry; copy the new one to each site afterwards (`scripts/tf data output -raw
db_tls_certificate_pem` in `personal_terraform`).

Metabase's `metabase_reader` can read every schema of the server
(`pg_read_all_data`), including `auth_user`. The nightly backup of the data VPS
covers these schemas too.

## Uploads (Cloudflare R2)

Each environment has its own bucket, public only through its custom domain
(served and cached by Cloudflare's CDN): `lavedonio-staging` at
`media-staging.lavedonio.com` and `lavedonio` at `media.lavedonio.com`. Django
writes to it through R2's S3 API (django-storages), with an R2 API token limited
to that bucket (*Object Read & Write*), whose key is in the `.env`
(`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`). Uploaded files never replace one
with the same name and are sent with a one-year `Cache-Control`.

The custom domains are one level below the zones (`media-staging`, not
`media.staging`), so Cloudflare's free certificate (`*.lavedonio.com`) covers them.

## DNS and certificates

Both zones, `lavedonio.com` and `lavedonio.com.br`, are on Cloudflare with
*SSL/TLS → Overview* set to **Full (strict)**: Cloudflare validates the server's
certificate. Never use *Flexible*: Cloudflare would then talk to the server over
plain HTTP, and CloudPanel redirects that back to HTTPS forever. `staging` in
each zone is a proxied `A` record to the CloudPanel VPS. A record that points at
the VPS before CloudPanel has a site for it gets error 525 from Cloudflare.

Each site has a Let's Encrypt certificate issued by CloudPanel, which renews them
daily through the proxy. The **first** certificate of a new site can't be issued
that way (Cloudflare rejects the self-signed certificate CloudPanel starts with),
so [`first-certificate.sh`](first-certificate.sh) serves the challenges over
plain HTTP while it's issued:

```bash
tar -czf - deploy | ssh -i ~/.ssh/id_ed25519_hostinger root@$CLOUDPANEL \
  "d=\$(mktemp -d) && tar -xzf - -C \$d && bash \$d/deploy/first-certificate.sh \
   /home/lavedonio-staging/htdocs/staging.lavedonio.com staging.lavedonio.com; rm -rf \$d"
```

## Setting up an environment from scratch

Example values are staging's.

1. **DNS** (Cloudflare): proxied `A` records for `staging` in both zones, to the
   CloudPanel VPS.
2. **CloudPanel sites** (as root on the VPS), then their certificates with
   `first-certificate.sh`:
   ```bash
   clpctl site:add:python --domainName=staging.lavedonio.com --pythonVersion=3.12 \
     --appPort=8091 --siteUser=lavedonio-staging --siteUserPassword="$(openssl rand -base64 30)"
   clpctl site:add:reverse-proxy --domainName=staging.lavedonio.com.br --reverseProxyUrl=http://127.0.0.1:8091 \
     --siteUser=lavedonio-staging-br --siteUserPassword="$(openssl rand -base64 30)"
   ```
3. **Database**: the role and schema (see *Database*).
4. **R2**: the bucket's custom domain, and an API token limited to it.
5. **Deploy key**: `ssh-keygen -t ed25519 -N '' -C 'github-actions deploy staging' -f deploy_key`.
   Store the private key and the other two secrets (see *How a staging deploy
   works*) in the `lavedonio-staging` environment in GitHub, then delete the
   key locally.
6. **Server layout**, from the repo root:
   ```bash
   tar -czf - deploy | ssh -i ~/.ssh/id_ed25519_hostinger root@$CLOUDPANEL \
     "d=\$(mktemp -d) && tar -xzf - -C \$d && bash \$d/deploy/setup-server.sh lavedonio-staging \
      staging.lavedonio.com 8091 staging '$(cat deploy_key.pub)'; rm -rf \$d"
   ```
   [`setup-server.sh`](setup-server.sh) is safe to run again: it never
   overwrites `.env`.
7. **Secrets on the server**: fill in the empty values of `~/app/shared/.env`
   (database password and host, R2 key, Turnstile keys), and copy the database
   certificate to `~/app/shared/postgres-ca.pem`.
8. **First deploy**: push to `staging`. It stops at "does not answer" because
   uWSGI isn't running the app yet: run `systemctl restart uwsgi` as root, then
   re-run the workflow.
