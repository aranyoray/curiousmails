# ISEF Project Database

A searchable database of Intel ISEF project abstracts with fuzzy search capabilities.

## Features

- Full-text fuzzy search (like Google) using Fuse.js
- Filter by year, category, and award status
- 16,199 ISEF projects (2014-2025)
- Click titles to view original abstracts

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Scrape project data

```bash
# Scrape all projects (takes several hours)
python scraper.py

# Or scrape a specific range
python scraper.py 8889 10000
```

The scraper saves progress, so you can stop and resume.

### 3. Run the webapp

```bash
# Simple HTTP server
python -m http.server 8000
```

Then open http://localhost:8000

## Files

- `index.html` - Main webapp with search interface
- `scraper.py` - Python scraper for ISEF abstracts
- `email_scraper.py` - Email finder for award winners
- `data/projects.json` - Scraped project data
- `data/progress.json` - Scraper progress tracker
- `data/winner_emails.json` - Emails of award winners

## Search Features

- Fuzzy matching for typos
- Partial word matching
- Multi-word queries
- Results ranked by relevance

## Email Scraper

The email scraper searches for contact information of ISEF award winners.

### Usage

```bash
# Search for emails of all award winners
python email_scraper.py

# Limit to first N winners (recommended for testing)
python email_scraper.py 10
```

### How it works

1. Filters projects for award winners only
2. Extracts student/finalist names from ISEF abstracts
3. Searches DuckDuckGo and Google for email addresses
4. Looks for LinkedIn profiles
5. Saves results to `data/winner_emails.json`

### Output Format

The script generates a JSON file with:
- Student name
- Project title and year
- Awards received
- Found email addresses
- LinkedIn profiles
- Search queries used

### Features

- Automatic resume: skips already processed winners
- Progress saving: saves every 10 projects
- Rate limiting: 3-second delay between searches
- Smart filtering: removes junk/invalid emails

### Notes

- Email discovery success varies by student
- Some students may have private/unlisted contact info
- Search engines may rate-limit frequent queries
- Results are best-effort and may not be complete
