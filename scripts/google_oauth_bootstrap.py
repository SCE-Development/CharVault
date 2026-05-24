"""One-time OAuth bootstrap.

Run locally with your `oauth_client.json` in the same directory:

    python scripts/google_oauth_bootstrap.py

A browser window opens, you sign in to the SCE Gmail account and click
"Allow". The script writes `token.json` next to the client file. Copy
that into the container's secrets mount and point GOOGLE_TOKEN_FILE at it.
"""

import argparse
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", default="oauth_client.json")
    parser.add_argument("--out", default="token.json")
    args = parser.parse_args()

    client_path = Path(args.client)
    if not client_path.exists():
        raise SystemExit(f"OAuth client file not found: {client_path}")

    flow = InstalledAppFlow.from_client_secrets_file(str(client_path), SCOPES)
    creds = flow.run_local_server(port=0)

    out_path = Path(args.out)
    out_path.write_text(creds.to_json())
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
