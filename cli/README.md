# vjobs-cli

Search [Vjobs](../README.md) listings from the terminal — same data as the website, no browser needed.

## Install

One command, no PyPI account needed — installs straight from GitHub:

```bash
pip install "git+https://github.com/Viswakmca7/job-scout.git#subdirectory=cli"
```

This registers a `vjobs` command via pip's console-scripts mechanism. Requires Python 3.9+ and `git` on your PATH.

## Usage

```bash
vjobs "python remote"
vjobs "react" --type contract --remote-only
vjobs "" --sort type --limit 30
```

It talks to the public hosted instance by default — nothing else to configure. Point it at a
different deployment (e.g. your own local dev server) with:

```bash
export VJOBS_API_URL=http://localhost:8000
```

## Install from source (for local development on the CLI itself)

```bash
cd vjobs/cli
pip install -e .
```

## Publishing to PyPI (so `pip install vjobs-cli` works without the git URL)

This step needs your own PyPI account and credentials, so it isn't something that can be done
on your behalf. Once you have a [PyPI account](https://pypi.org/account/register/) and an API token:

```bash
cd vjobs/cli
python -m pip install build twine
python -m build
python -m twine upload dist/*
```
