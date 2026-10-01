# Email Assistant

A small phone-friendly inbox demo built with FastAPI and plain JavaScript. It sorts sample messages by keyword-based priority, shows short text previews, and displays upcoming sample calendar events.

**This is a local prototype.** Gmail, Outlook, calendar sync, and AI-provider connections are not implemented. The summaries are shortened text, not AI-generated summaries.

## Run

Requires Python 3.12 or 3.13 (the versions checked in CI).

```sh
python -m venv .venv
```

Activate the environment (`.venv\Scripts\activate` on Windows or `source .venv/bin/activate` on macOS/Linux), then:

```sh
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Under **Connect**, click **Load demo data** to create a fresh sample inbox and calendar. No credentials are needed. Local demo state is written to `data/state.json`, which is ignored by Git.

## Check

```sh
pip install -r requirements-dev.txt
python -m unittest -v
```

Tests cover priority classification, text previews, dashboard ordering, sample data, invalid requests, and static routes.

## Notes

- Priority comes from a small keyword list and can be wrong.
- The service worker caches the interface, not email or calendar responses. Inbox data still needs the local server.
- There is no login or multi-user support. Keep this demo on localhost.
- Next step: add one read-only email provider with OAuth and let users correct priorities.

## Project layout

- `app.py`: API, demo data, and local persistence.
- `static/`: interface, styles, icons, and service worker.
- `test_app.py`: API and interface-route regression tests.
- `requirements*.in`: allowed direct dependencies.
- `requirements*.txt`: exact dependency versions for repeatable installs.
- `data/`: local state, excluded from Git.

## Maintenance

GitHub Actions runs the existing tests on Python 3.12 and 3.13. Dependabot checks Python dependencies and workflow actions weekly.

To regenerate the locks in a Python 3.12 environment:

```sh
python -m pip install pip-tools
pip-compile --upgrade requirements.in
pip-compile --upgrade --constraint requirements.txt requirements-dev.in
python -m pip install -r requirements-dev.txt
python -m unittest -v
```
