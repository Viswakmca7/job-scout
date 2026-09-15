# vjobs-cli

Search [Vjobs](../README.md) listings from the terminal — same data as the website, no browser needed.

## Install (locally, from source)

```bash
cd vjobs/cli
pip install -e .
```

This registers a `vjobs` command via pip's console-scripts mechanism.

## Usage

```bash
# Point it at your deployed API once you've deployed the backend
export VJOBS_API_URL=https://your-app.onrender.com

vjobs "python remote"
vjobs "react" --type contract --remote-only
vjobs "" --sort type --limit 30
```

Without `VJOBS_API_URL` set, it defaults to `http://localhost:8000` (a locally running backend).

## Publishing to PyPI (so `pip install vjobs-cli` works for anyone)

This step needs your own PyPI account and credentials, so it isn't something that can be done
on your behalf. Once you have a [PyPI account](https://pypi.org/account/register/) and an API token:

```bash
cd vjobs/cli
python -m pip install build twine
python -m build
python -m twine upload dist/*
```
