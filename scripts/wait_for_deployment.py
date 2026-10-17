"""Wait until a public environment serves the exact promoted commit."""

import json
import os
import re
import time
import urllib.error
import urllib.request


def verify_payloads(health, version, cafes, expected):
    return (
        isinstance(health, dict)
        and health.get("status") == "ok"
        and isinstance(version, dict)
        and version.get("version") == expected
        and isinstance(cafes, list)
        and len(cafes) >= 5
    )


def main():
    url = os.environ["APP_URL"].rstrip("/")
    expected = os.environ["EXPECTED_SHA"]
    if not url.startswith("https://") or not re.fullmatch(r"[a-f0-9]{40}", expected):
        raise SystemExit("Require HTTPS APP_URL and a full commit SHA")
    deadline = time.monotonic() + 720
    while time.monotonic() < deadline:
        try:
            payloads = []
            for route in ("health", "version", "cafes"):
                with urllib.request.urlopen(f"{url}/{route}", timeout=10) as response:
                    payloads.append(json.load(response))
            if verify_payloads(*payloads, expected):
                print(f"Deployment verified: {url}, SHA {expected}, seeded database")
                return
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            pass
        print("Waiting for Watchtower and the expected healthy version...", flush=True)
        time.sleep(10)
    raise SystemExit("Smoke tests timed out; check Watchtower logs and APP_URL")


if __name__ == "__main__":
    main()
