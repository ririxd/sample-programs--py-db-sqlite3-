# Lab Tracker and Inventory Project

A Python desktop application for managing lab tracking workflows, user authentication, and experiment records using Tkinter, SQLite, and Python validation models.

## Features

- User registration and login with secure password hashing
- SQLite database for user and experiment data
- Tkinter-based user interface for lab workflow interaction
- Input validation using Pydantic schemas
- Activity logging for system events and login tracking
- Unit tests covering authentication and experiment validation

## Project Overview

This project contains a lab tracking application with:

- Authentication and login flow
- Experiment tracking controller logic
- Database initialization and schema setup
- Logging utilities
- GUI screens for login and tracker operations

## Tech Stack

- Python 3
- Tkinter
- SQLite
- Pydantic
- bcrypt

## Project Structure

- `Experimental Task/` - main application source code
- `Activity/` - supporting lab activity files
- `Supplementary Activity/` - additional task-related scripts
- `app_logging/` - application log outputs
- `tests/` - test files for the project

## Setup

1. Open a terminal in the project folder.
2. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

3. Activate the environment:

   On Windows PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

4. Install packages if needed:

   ```bash
   pip install bcrypt pydantic
   ```

## Run the Application

From the project root:

```bash
cd "Experimental Task"
python main.py
```

## Run Tests

```bash
python -m unittest discover -s "Experimental Task/tests"
```

## Notes

This repository was made out of academic experimetnts and may include multiple versions of the same lab activity in different folders. Users may use this repository as a start-up reference.
