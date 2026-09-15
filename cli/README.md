# jobscout-cli

Search [Job Scout](../README.md) listings from the terminal — same data as the website, no browser needed.

## Install (locally, from source)

```bash
cd job-scout/cli
pip install -e .
```

This registers a `jobscout` command via pip's console-scripts mechanism.

## Usage

```bash
# Point it at your deployed API once you've deployed the backend
export JOBSCOUT_API_URL=https://your-app.onrender.com

jobscout "python remote"
jobscout "react" --type contract --remote-only
jobscout "" --sort type --limit 30
```

Without `JOBSCOUT_API_URL` set, it defaults to `http://localhost:8000` (a locally running backend).

## Publishing to PyPI (so `pip install jobscout-cli` works for anyone)

This step needs your own PyPI account and credentials, so it isn't something that can be done
on your behalf. Once you have a [PyPI account](https://pypi.org/account/register/) and an API token:

```bash
cd job-scout/cli
python -m pip install build twine
python -m build
python -m twine upload dist/*
```
