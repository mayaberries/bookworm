---
name: add-setting
description: Add a configuration value to bookworm's Settings (environment variable BOOKWORM_*), or decide that it belongs in a catalogue's record instead. Use for "make the timeout configurable", "add a proxy", "how many catalogues at once?", "we need an API key for X".
---

# Add a setting

Adapted from the `add-setting` skill shared by Vetted, Sinapsis, Kalens and Xolo. Bookworm is an app, so **it reads the environment**: one `Settings` (`src/bookworm/shared/config.py`, pydantic-settings, prefix `BOOKWORM_`, optional `.env`), read through `get_settings()`.

## 0. Setting or record?

| It's about… | Goes in | Example |
|---|---|---|
| how bookworm behaves everywhere | `Settings` | `http_timeout_seconds`, `max_concurrent_catalogues`, `browser_headless`, `data_dir` |
| one catalogue | its record in `data/catalogues/` | `base_url`, `min_seconds_between_requests`, `automation`, an adapter's `options` |
| one library | its record in `data/libraries/` | `catalogue_location` |
| a secret for one catalogue (an API key) | an environment variable **named in that catalogue's adapter options** (`api_key_env: NAUTILO_API_KEY`), read by the gateway | never in a record file, never committed |

If it's per catalogue, stop here and use `add-catalogue`. The secret case doesn't exist yet: when the first one appears, decide how the gateway hands it to the adapter (through `AdapterContext`, never `os.environ` inside an adapter) and record it in `docs/DECISIONS.md`.

## 1. The field

```python
http_timeout_seconds: float = Field(default=20.0, gt=0)
```

- **A default that works from a fresh clone**, so nothing needs an `.env` to run. Exception: secrets have no default.
- **Typed and constrained** (`gt=0`, `ge=1`, `Path`, `HttpUrl`), so a bad value fails at startup naming the variable, not deep inside a lookup.
- **A comment or `description`** saying what it changes and when you'd touch it.
- **Changing a default changes behaviour for everyone** who doesn't set it: say so in the PR.

## 2. Reading it

- **Only entry points read settings**: the CLI and the modules' builders (`open_lookup_service(settings)`, `build_directory_service(settings.data_dir)`). They pass plain values down.
- **Services, repositories and adapters never call `get_settings()`.** They're given what they need, so tests build them with any values without touching the environment.
- Tests build `Settings(...)` directly (the `settings` fixture). When a test must go through the CLI, set `BOOKWORM_*` with `monkeypatch` and clear `get_settings.cache_clear()` around the call.

## 3. Failure modes

If a setting points at something outside (a proxy, a cache directory), say what happens when it's unreachable: a lookup must still answer with per-catalogue `failed` outcomes, not crash. Add a test for that case.

## Checklist

- [ ] It's really global; per-catalogue values are in records
- [ ] Typed, constrained, defaulted (unless a secret), documented
- [ ] Read only at entry points and passed down
- [ ] Failure mode decided and tested if it points outside
