#!/usr/bin/env bash
# Prepares a CloudPanel Python site to receive deploys (see deploy/README.md).
# Run as root on the CloudPanel VPS after creating the site in CloudPanel, from
# a copy of this repository's deploy/ directory:
#
#   setup-server.sh <site user> <domain> <app port> <staging|production> "<deploy public key>"
#
# Safe to run again: it never overwrites the .env file.
set -euo pipefail

if [[ $# -ne 5 || $EUID -ne 0 ]]; then
    echo "usage (as root): $0 <site user> <domain> <app port> <staging|production> \"<deploy public key>\"" >&2
    exit 2
fi
site_user="$1" domain="$2" app_port="$3" environment="$4" deploy_key="$5"
here="$(cd "$(dirname "$0")" && pwd)"
home="/home/$site_user"
docroot="$home/htdocs/$domain"
app="$home/app"
as_site_user() { runuser -u "$site_user" -- "$@"; }

[[ -d $docroot ]] || { echo "No $docroot: create the Python site in CloudPanel first." >&2; exit 1; }
[[ $environment == staging || $environment == production ]] || { echo "Unknown environment: $environment" >&2; exit 2; }
[[ $deploy_key == ssh-* ]] || { echo "The deploy key must be an OpenSSH public key." >&2; exit 2; }

if [[ $environment == production ]]; then
    bucket=lavedonio media_domain=media.lavedonio.com
else
    bucket="lavedonio-$environment" media_domain="media-$environment.lavedonio.com"
fi

echo "==> Release layout in $app"
as_site_user mkdir -p "$app/releases" "$app/shared" "$home/bin"
as_site_user touch "$app/reload"
install -o "$site_user" -g "$site_user" -m 0750 "$here/receive-release.sh" "$home/bin/receive-release"

if [[ ! -f $app/shared/.env ]]; then
    echo "==> Writing $app/shared/.env (fill in the empty values)"
    secret_key="$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"
    as_site_user install -m 0600 /dev/null "$app/shared/.env"
    cat > "$app/shared/.env" <<EOF
ENVIRONMENT=$environment
SECRET_KEY=$secret_key
DEBUG_VALUE=False

# Schema lavedonio_$environment of lavedonio_postgres on the data VPS (DB_HOST: its IP).
DB_NAME=lavedonio_postgres
DB_USER=lavedonio_$environment
DB_PASSWORD=
DB_HOST=
DB_PORT=5432
DB_SCHEMA=lavedonio_$environment
DB_SSLMODE=verify-full
DB_SSLROOTCERT=$app/shared/postgres-ca.pem

# Uploads: R2 bucket $bucket, served from its custom domain.
# The key is an R2 API token limited to that bucket (Object Read & Write).
R2_ACCOUNT_ID=
R2_BUCKET=$bucket
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
MEDIA_DOMAIN=$media_domain

# Cloudflare Turnstile widget of the contact form.
TURNSTILE_SITE_KEY=
TURNSTILE_SECRET_KEY=
EOF
else
    echo "==> Keeping the existing $app/shared/.env"
fi

echo "==> Static files served by nginx from $docroot"
as_site_user ln -sfn "$app/current/staticfiles" "$docroot/static"

echo "==> uWSGI app /etc/uwsgi/apps-enabled/$site_user.ini (port $app_port)"
sed -e "s/SITE_USER/$site_user/g" -e "s/APP_PORT/$app_port/g" "$here/uwsgi.ini" > "/etc/uwsgi/apps-enabled/$site_user.ini"
chown root:root "/etc/uwsgi/apps-enabled/$site_user.ini"
chmod 0644 "/etc/uwsgi/apps-enabled/$site_user.ini"

echo "==> Deploy key (can only run ~/bin/receive-release)"
key_line="restrict,command=\"$home/bin/receive-release\" $deploy_key"
if ! grep -qxF "$key_line" "$home/.ssh/authorized_keys"; then
    echo "$key_line" >> "$home/.ssh/authorized_keys"
fi

cat <<EOF

Done. Still to do (see deploy/README.md):
  - the empty values in $app/shared/.env, and the database's certificate in $app/shared/postgres-ca.pem
  - the first deploy, then: systemctl restart uwsgi
EOF
