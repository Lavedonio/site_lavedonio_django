#!/usr/bin/env bash
# Issues the first Let's Encrypt certificate of a CloudPanel site behind
# Cloudflare's proxy (see deploy/README.md, "DNS and certificates"). Run as root
# on the CloudPanel VPS:
#
#   first-certificate.sh <document root> <domain> [other names...]
#
# Cloudflare (Full strict) rejects the self-signed certificate a new site starts
# with, so Let's Encrypt's challenge, redirected to HTTPS, never arrives. While
# the certificate is issued, this serves the challenges over plain HTTP instead.
# Renewals work through the proxy once the site has a valid certificate.
#
# For a domain without a subdomain (lavedonio.com), CloudPanel also puts
# www.<domain> in the certificate, and its www vhost redirects to the domain
# over HTTPS, so www's challenges are served here too. Its DNS record must
# already point at the VPS.
set -euo pipefail

if [[ $# -lt 2 || $EUID -ne 0 ]]; then
    echo "usage (as root): $0 <document root> <domain> [other names...]" >&2
    exit 2
fi
docroot="$1" domain="$2"
shift 2
override=/etc/nginx/sites-enabled/00-acme-over-http.conf

[[ -d $docroot ]] || { echo "No $docroot: create the site in CloudPanel first." >&2; exit 1; }

cat > "$override" <<EOF
# Temporary, written by first-certificate.sh: Let's Encrypt challenges over plain
# HTTP. Loaded before CloudPanel's vhosts, removed once the certificate is issued.
server {
  listen 80;
  listen [::]:80;
  server_name $domain www.$domain $*;
  location ^~ /.well-known/acme-challenge/ { root $docroot; }
  location / { return 301 https://\$host\$request_uri; }
}
EOF
trap 'rm -f "$override"; nginx -t -q && systemctl reload nginx' EXIT
nginx -t -q
systemctl reload nginx
sleep 2

alt_names="$(IFS=,; echo "$*")"
clpctl lets-encrypt:install:certificate --domainName="$domain" \
    ${alt_names:+--subjectAlternativeName="$alt_names"}
openssl x509 -in "/etc/nginx/ssl-certificates/$domain.crt" -noout -issuer -enddate
