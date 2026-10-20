#!/usr/bin/env bash
# Builds and activates a release on the server, as the site user. Called by
# receive-release with the new release's directory (see deploy/README.md):
#
#   ~/app/releases/<time>-<sha>/  one directory per deploy (code, .venv, staticfiles)
#   ~/app/current                 symlink to the live release; uWSGI runs from it
#   ~/app/shared/.env             settings, shared by every release
#   ~/app/shared/postgres-ca.pem  the data VPS's Postgres certificate
#   ~/app/reload                  touched to make uWSGI reload gracefully
#
# Uploads are in a Cloudflare R2 bucket, not on the server.
#
# Nothing changes for visitors until every step before "Switching" succeeded.
# If the new release doesn't answer afterwards, `current` goes back to the
# previous one (migrations are not reverted).
set -euo pipefail

release="$1"
app="$HOME/app"
python=/usr/bin/python3.12  # must match uWSGI's python312 plugin
uwsgi_ini="/etc/uwsgi/apps-enabled/$USER.ini"  # written by setup-server.sh
keep_releases=5

exec 9> "$app/deploy.lock"
flock -n 9 || { echo "Another deploy is running." >&2; exit 1; }

previous="$(readlink -e "$app/current" || true)"  # empty on the first deploy
switched=false
trap '[[ $switched == true ]] || rm -rf "$release"' EXIT

switch_to() {
    ln -sfn "$1" "$app/current.new"
    mv -T "$app/current.new" "$app/current"
    touch "$app/reload"
}

cd "$release"
# The settings read the .env file next to the repository's root
ln -s "$app/shared/.env" .env
manage() { .venv/bin/python site_lavedonio_django/manage.py "$@"; }

echo "==> Installing dependencies"
"$python" -m venv .venv
.venv/bin/pip install --quiet --disable-pip-version-check -r requirements.txt

echo "==> Checking the settings"
manage check --deploy

echo "==> Migrating the database"
manage migrate --noinput
# The cache (single-use tokens) is a database table; does nothing if it exists
manage createcachetable

echo "==> Collecting static files"
manage collectstatic --noinput --verbosity 0

# Ask uWSGI directly, as the first host in ALLOWED_HOSTS (others get a 400).
port="$(sed -n 's/^http-socket = 127\.0\.0\.1:\([0-9]*\)$/\1/p' "$uwsgi_ini")"
# (without shell's message about its automatic imports, which goes to stdout)
host="$(manage shell --no-imports --verbosity 0 -c 'from django.conf import settings; print(settings.ALLOWED_HOSTS[0])' | tail -n 1)"
site_answers() {
    curl -fsS -o /dev/null --max-time 10 \
        -H "Host: $host" -H "X-Forwarded-Proto: https" "http://127.0.0.1:$port/"
}

echo "==> Switching to $(basename "$release")"
switch_to "$release"
switched=true

echo "==> Waiting for the site to answer"
sleep 3
for _ in $(seq 10); do
    if site_answers 2> /dev/null; then
        break
    fi
    sleep 3
done
if ! site_answers; then
    echo "!! The new release does not answer on port $port. Is uWSGI running?" >&2
    echo "!! (log: /var/log/uwsgi/app/$USER.log; as root: systemctl restart uwsgi)" >&2
    if [[ -n $previous ]]; then
        echo "!! Rolling back to $(basename "$previous")." >&2
        switch_to "$previous"
    fi
    exit 1
fi

echo "==> Removing old releases"
current="$(readlink -f "$app/current")"
ls -1d "$app"/releases/*/ | sed 's:/$::' | sort | head -n "-$keep_releases" | while read -r old; do
    [[ $old == "$current" ]] || rm -rf "$old"
done

echo "==> Deployed $(cat REVISION 2>/dev/null || basename "$release")"
