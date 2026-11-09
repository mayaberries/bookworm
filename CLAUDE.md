# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Early stage: the repository currently contains only a README. No language, build system, test framework, or dependencies have been chosen yet. Update this file with real commands (build, lint, test, running a single test) and architecture notes once they exist.

## Purpose

Bookworm crawls and queries online library catalogues to determine whether a given book is available at a given library. Planned techniques include browser automation (Playwright), direct API calls, and other scraping methods, chosen per library depending on how its catalogue is exposed.

## Initial scope: Mexico City

- Map every library in Mexico City.
- Build a database with one record per library holding everything needed to interact with it programmatically (e.g. catalogue URL, catalogue system/vendor, access method such as API vs. browser automation, and any query specifics).
- Catalogue lookups should be driven by that per-library data, so supporting a new library mostly means adding a database entry and, where needed, an adapter for its catalogue system.
