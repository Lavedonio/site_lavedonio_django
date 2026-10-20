#!/usr/bin/env bash
# Forced command of the CI deploy key on the server (see deploy/README.md).
# Installed once as ~/bin/receive-release; GitHub Actions runs
#
#   git archive --format=tar.gz HEAD | ssh <site user>@<server> deploy <commit sha>
#
# It unpacks the release into a new directory and hands over to that release's
# deploy/release.sh, so the deploy steps are versioned with the code.
set -euo pipefail

read -r action sha extra <<< "${SSH_ORIGINAL_COMMAND:-}"
if [[ $action != deploy || ! $sha =~ ^[0-9a-f]{40}$ || -n $extra ]]; then
    echo "usage: deploy <full commit sha>, with the release tarball on stdin" >&2
    exit 2
fi

release="$HOME/app/releases/$(date -u +%Y%m%d-%H%M%S)-${sha:0:7}"
mkdir -p "$release"
if ! tar -xzf - -C "$release"; then
    rm -rf "$release"
    exit 1
fi
echo "$sha" > "$release/REVISION"

exec bash "$release/deploy/release.sh" "$release"
