# Airbnb End-to-End Automation
**Python Playwright + Django + PostgreSQL**

---

## Quick Start (4 commands)

```bash
cd airbnb_automation
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt && playwright install chromium
python manage.py migrate && python manage.py run_airbnb_automation
```

---

## Overview

Automates a full real-user journey on https://www.airbnb.com/

| Step | What it does |
|---|---|
| 01 | Open Airbnb, clear storage, dismiss popups, type random country |
| 02 | Verify suggestion dropdown, icons, relevance, click one |
| 03 | Navigate 3–8 months in calendar, select check-in & check-out |
| 04 | Open guest picker, add 2–5 guests, click Search |
| 05 | Verify results page, validate URL params, scrape listings |
| 06 | Open random listing, capture title / subtitle / gallery images |

All results saved to PostgreSQL. Screenshots saved to `screenshots/`.

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Django 4.2 | ORM, Admin, Management Command |
| Playwright 1.42+ | Browser automation |
| psycopg2-binary | PostgreSQL driver |
| python-dotenv | `.env` configuration |

---

## Project Structure

```
airbnb_automation/
├── airbnb_automation/
│   ├── settings.py         ← reads from .env
│   └── urls.py
├── automation/
│   ├── models.py           ← 5 DB tables
│   ├── admin.py            ← Django Admin
│   ├── services/
│   │   ├── browser_service.py      ← Playwright wrapper
│   │   └── database_service.py     ← All DB writes
│   ├── steps/
│   │   ├── step01_landing.py
│   │   ├── step02_suggestion.py
│   │   ├── step03_datepicker.py
│   │   ├── step04_guestpicker.py
│   │   ├── step05_results.py
│   │   └── step06_details.py
│   └── management/commands/
│       └── run_airbnb_automation.py   ← ENTRY POINT
├── screenshots/            ← auto-created
├── .env                    ← DB credentials
├── requirements.txt
└── manage.py
```

---

## Installation

### 1. Navigate to project folder
```bash
cd airbnb_automation
# Verify: ls should show manage.py and requirements.txt
```

### 2. Create virtual environment
```bash
python3 -m venv venv
```

### 3. Activate it
```bash
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
```

### 4. Install packages
```bash
pip install -r requirements.txt
```

### 5. Install Playwright browser (one time only)
```bash
playwright install chromium
```

---

## Environment Configuration

Edit `.env` if your DB credentials differ:

```env
DB_NAME=mydb
DB_USER=ali
DB_PASSWORD=1234
DB_HOST=localhost
DB_PORT=5432
AIRBNB_URL=https://www.airbnb.com/
SCREENSHOT_DIR=screenshots
```

---

## Database Setup

```bash
# Start PostgreSQL Docker container
docker start <your-container-name>
docker ps     # verify it shows as Up

# Create all tables
python manage.py migrate

# Create admin user (for admin panel)
python manage.py createsuperuser
```

---

## Running the Automation

```bash
# Default — visible browser
python manage.py run_airbnb_automation

# Headless (no window)
python manage.py run_airbnb_automation --headless

# Mobile emulation — iPhone 14 Pro (Bonus)
python manage.py run_airbnb_automation --mobile

# Mobile + Headless
python manage.py run_airbnb_automation --mobile --headless
```

---

## Django Admin Panel

```bash
python manage.py runserver
# Open: http://127.0.0.1:8000/admin/
```

| Table | Data |
|---|---|
| Test Results | All step results with pass/fail + comment |
| Listings | Scraped titles, prices, images |
| Suggestions | Search autocomplete items |
| Network Logs | HTTP requests captured |
| Console Logs | Browser console messages |

---


