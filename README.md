# Airbnb End-to-End Automation

Airbnb UI automation framework built with Python, Playwright, Django, and PostgreSQL.

Repository: `https://github.com/Ali-Haidar-159/airbnb_automation`

## Features

- Full 6-step Airbnb user journey automation.
- Structured verification logging (`should be ..., found ...`) for each test case.
- Data persistence to PostgreSQL for:
- `testing` (test results)
- `listing_data` (listing cards and detail updates)
- `suggestion_data` (autocomplete suggestions)
- `network_logs` (captured requests)
- `console_logs` (captured browser console logs)
- Run modes:
- Desktop visible browser
- Desktop headless
- Mobile emulation (iPhone 14 Pro)
- Mobile emulation headless

## End-to-End Flow

1. Landing, popup dismissal, destination input.
2. Auto-suggestion checks and random selection.
3. Date picker navigation and date selection.
4. Guest picker interaction and search submit.
5. Results page validation and listing scraping.
6. Random listing details page verification and gallery extraction.

## Tech Stack

- Python 3.10+ (tested with Python 3.12)
- Django 4.2.x
- Playwright 1.42+
- PostgreSQL
- psycopg2-binary
- python-dotenv

## Project Structure

```text
airbnb_automation/
├── airbnb_automation/
│   ├── settings.py
│   └── urls.py
├── automation/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── migrations/
│   ├── services/
│   │   ├── browser_service.py
│   │   └── database_service.py
│   ├── steps/
│   │   ├── step01_landing.py
│   │   ├── step02_suggestion.py
│   │   ├── step03_datepicker.py
│   │   ├── step04_guestpicker.py
│   │   ├── step05_results.py
│   │   └── step06_details.py
│   └── management/commands/
│       └── run_airbnb_automation.py
├── requirements.txt
└── manage.py
```

## Prerequisites

- Git
- Python 3.10+
- PostgreSQL server (local or Docker)
- Chromium dependencies for Playwright (Linux users may need additional system packages)

## Clone the Repository

```bash
git clone https://github.com/Ali-Haidar-159/airbnb_automation.git
cd airbnb_automation
```

## Installation

1. Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

For Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

2. Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. Install Playwright browser

```bash
playwright install chromium
```

## Environment Variables

Create `.env` at the project root:

```env
DB_NAME=mydb
DB_USER=ali
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=5432
AIRBNB_URL=https://www.airbnb.com/
SCREENSHOT_DIR=screenshots
```

Notes:

- `SCREENSHOT_DIR` is currently retained for compatibility with settings; screenshot capture is disabled in current code.
- If `.env` is not present, `settings.py` falls back to default values shown above.

## Database Setup

### Option A: Local PostgreSQL

1. Create database and user (example):

```sql
CREATE DATABASE mydb;
CREATE USER ali WITH PASSWORD '1234';
GRANT ALL PRIVILEGES ON DATABASE mydb TO ali;
```

2. Ensure `.env` values match your DB credentials.

### Option B: Docker PostgreSQL

```bash
docker run --name airbnb-pg \
  -e POSTGRES_DB=mydb \
  -e POSTGRES_USER=ali \
  -e POSTGRES_PASSWORD=1234 \
  -p 5432:5432 \
  -d postgres:16
```

## Migrations

Run migrations after DB is ready:

```bash
python manage.py makemigrations
python manage.py migrate
```

If you only want this app:

```bash
python manage.py migrate automation
```

## Run the Automation

Default (visible desktop browser):

```bash
python manage.py run_airbnb_automation
```

Other modes:

```bash
python manage.py run_airbnb_automation --headless
python manage.py run_airbnb_automation --mobile

```

## Run Django Server and Admin

Create admin user:

```bash
python manage.py createsuperuser
```

Start server:

```bash
python manage.py runserver
```

Open admin panel:

- `http://127.0.0.1:8000/admin/`

## Database Tables

- `testing`: high-level pass/fail results for each automation check.
- `listing_data`: scraped listing cards and details updates.
- `suggestion_data`: autocomplete suggestion text with search query.
- `network_logs`: request method/url/status/resource type.
- `console_logs`: browser console entries by level.

