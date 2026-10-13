"""Start the API using the environment settings shared by all launchers."""

import argparse
import webbrowser

import uvicorn

from api.config import settings


def main():
    parser = argparse.ArgumentParser(description="Jalankan server API NusaKlim.")
    parser.add_argument("--open-browser", action="store_true")
    args = parser.parse_args()

    browser_host = settings.host
    if browser_host in ("0.0.0.0", "::"):
        browser_host = "127.0.0.1"
    elif ":" in browser_host:
        browser_host = f"[{browser_host}]"
    url = f"http://{browser_host}:{settings.port}/docs"
    print(f"Swagger UI: {url}", flush=True)
    if args.open_browser:
        webbrowser.open(url)
    uvicorn.run("api.main:app", host=settings.host, port=settings.port,
                reload=settings.reload)


if __name__ == "__main__":
    main()
