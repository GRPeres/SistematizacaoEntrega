#!/usr/bin/env bash
set -euo pipefail
SOURCE="${1:?image reference required}"
CHANNEL="${2:?staging or production required}"
NAME="ghcr.io/${GITHUB_REPOSITORY,,}"
[[ "$CHANNEL" = staging || "$CHANNEL" = production ]] || exit 1
[[ "$SOURCE" =~ ^${NAME}@sha256:[a-f0-9]{64}$ ]] || {
  echo 'Source must be an immutable digest from this repository'; exit 1;
}
EXPECTED="${SOURCE##*@}"
docker buildx imagetools create --prefer-index=false --tag "$NAME:$CHANNEL" "$SOURCE"
ACTUAL="$(docker buildx imagetools inspect "$NAME:$CHANNEL" --format '{{.Manifest.Digest}}')"
[[ "$ACTUAL" = "$EXPECTED" ]] || { echo 'Promoted digest differs'; exit 1; }
printf '%s -> %s\n' "$CHANNEL" "$SOURCE" >> "$GITHUB_STEP_SUMMARY"
