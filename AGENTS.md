# Contributing.

Thank you for your service.

You are here to help make terminal fish tank apps, with AI integrated in various ways.

## Creating venv
```bash
uv sync
```

Activate venv if you're on Windows...
```bash
. ./.venv/Scripts/activate
```

Activate venv if you're on Linux
```bash
. ./.venv/bin/activate
```


## Quality Gates
Tests are pytest.
```bash
make test
```

Do not run the other quality gates. LLM workers like yourself cost tokens and humans can fix mypy linting issues for 
less $$.

## Commit messages
Please prefix with one of the following keepachanglog types, e.g. Added, Changed, etc see this list:

- Added for new features.
- Changed for changes in existing functionality.
- Deprecated for soon-to-be removed features.
- Removed for now removed features.
- Fixed for any bug fixes.
- Security in case of vulnerabilities.

If nothing fits, it is "Changed"

e.g. 
"Changed: emojis are better"

## Naming Conventions
- No single letter variable names. 
- No hungarian notation of any sort (affixing variable names with their type).
- Spell out words, no ad hoc abbreviations.

## PR
Say what you intended to do.

## Authorship
Add your model to the authors file. If you see "OpenAI Codex" and you are an OpenAI model, you are already on the AUTHORS list.
Do not add another entry. Yes, I know you personally don't memory of it. Us humans call all of you bots OpenAI Codex.

