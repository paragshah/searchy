## Project Overview

This project is a bookmarking/link management app called Searchy. Stack: Python backend, SQLite database, HTML/CSS/JavaScript frontend with Jinja2 templates. Always run the app and verify changes work before committing.

## Database Operations

When modifying or deleting data in SQLite databases (or any persistent store not tracked by git), ALWAYS warn the user about irreversibility before executing. Offer to create a backup first.

## Frontend / UI

When making UI/styling changes, use minimal, subtle styling by default. Avoid broad CSS selectors that could affect unrelated elements. Show the user before committing if the change is visual.

## Git Workflow

Always initialize git and make an initial commit before starting work on a new project. Commit after each completed feature, not in bulk.
