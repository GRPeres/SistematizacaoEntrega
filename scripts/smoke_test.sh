#!/usr/bin/env bash
set -euo pipefail
URL="${1:?Uso: bash scripts/smoke_test.sh <URL_BASE> [SHA_ESPERADO]}"
EXPECTED="${2:-}"
echo "Health:"
curl -fsS "$URL/health"; echo
echo "Version:"
VERSION="$(curl -fsS "$URL/version")"
echo "$VERSION"
if [ -n "$EXPECTED" ]; then
  echo "$VERSION" | grep -Fq "$EXPECTED"
fi
