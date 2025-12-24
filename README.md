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
- `data/projects.json` - Scraped project data
- `data/progress.json` - Scraper progress tracker

## Search Features

- Fuzzy matching for typos
- Partial word matching
- Multi-word queries
- Results ranked by relevance
