#!/usr/bin/env python3
"""
ISEF Project Scraper
Scrapes project data from abstracts.societyforscience.org
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
import re
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed

# Disable SSL warnings for retries
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_FILE = "data/projects.json"
PROGRESS_FILE = "data/progress.json"

def fetch_project(project_id):
    """Fetch a single project's data."""
    url = f"https://abstracts.societyforscience.org/Home/FullAbstract?projectId={project_id}"

    try:
        # Try with SSL verification first, then without
        try:
            response = requests.get(url, timeout=30)
        except requests.exceptions.SSLError:
            response = requests.get(url, timeout=30, verify=False)

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the main content area
        content = soup.find('div', class_='container')
        if not content:
            return None

        # Extract data using various methods
        project = {'id': project_id}

        # Find all text content
        text = content.get_text()

        # Check if it's a valid project page
        if "Project not found" in text or "Error" in text:
            return None

        # Extract title (usually in h2 or first heading after metadata)
        title_elem = content.find('h2')
        if title_elem:
            project['title'] = title_elem.get_text(strip=True)
        else:
            # Try finding title in different ways
            headings = content.find_all(['h1', 'h2', 'h3'])
            for h in headings:
                t = h.get_text(strip=True)
                if t and len(t) > 10 and "ISEF" not in t:
                    project['title'] = t
                    break

        # Extract metadata fields
        labels = content.find_all('strong')
        for label in labels:
            label_text = label.get_text(strip=True).lower()
            next_text = ""

            # Get text after the label
            next_sibling = label.next_sibling
            if next_sibling:
                if hasattr(next_sibling, 'get_text'):
                    next_text = next_sibling.get_text(strip=True)
                else:
                    next_text = str(next_sibling).strip()

            # Also check parent's text
            parent = label.parent
            if parent:
                full_text = parent.get_text()
                # Extract value after colon
                if ':' in full_text:
                    value = full_text.split(':', 1)[1].strip()
                    if value:
                        next_text = value.split('\n')[0].strip()

            if 'category' in label_text:
                project['category'] = next_text
            elif 'year' in label_text:
                project['year'] = next_text
            elif 'booth' in label_text:
                project['booth'] = next_text
            elif 'country' in label_text or 'location' in label_text:
                project['country'] = next_text

        # Extract abstract
        abstract_section = None
        for elem in content.find_all(['p', 'div']):
            prev = elem.find_previous(['strong', 'b'])
            if prev and 'abstract' in prev.get_text().lower():
                abstract_text = elem.get_text(strip=True)
                if len(abstract_text) > 100:
                    project['abstract'] = abstract_text
                    break

        # Alternative: find abstract by looking for long paragraphs
        if 'abstract' not in project:
            paragraphs = content.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 200:
                    project['abstract'] = text
                    break

        # Extract awards - look for "Awards Won:" section
        awards = []
        full_text = content.get_text()
        if 'Awards Won:' in full_text:
            awards_text = full_text.split('Awards Won:')[1].strip()
            # Get text until next section or end
            awards_text = awards_text.split('\n')[0].strip()
            if awards_text and len(awards_text) < 500:
                # Split multiple awards
                if ';' in awards_text:
                    awards = [a.strip() for a in awards_text.split(';') if a.strip()]
                elif awards_text:
                    awards = [awards_text]

        project['awards'] = awards

        # Only return if we have at least title and abstract
        if 'title' in project and 'abstract' in project:
            return project
        elif 'title' in project:
            # Return even without abstract
            return project

        return None

    except Exception as e:
        print(f"Error fetching project {project_id}: {e}")
        return None

def load_progress():
    """Load scraping progress."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'last_id': 8888, 'total_scraped': 0}

def save_progress(progress):
    """Save scraping progress."""
    os.makedirs('data', exist_ok=True)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

def load_projects():
    """Load existing projects."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_projects(projects):
    """Save projects to file."""
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(projects, f, indent=2)

def scrape_range(start_id, end_id, batch_size=100, delay=0.5):
    """Scrape a range of project IDs."""
    progress = load_progress()
    projects = load_projects()
    existing_ids = {p['id'] for p in projects}

    start_id = max(start_id, progress['last_id'] + 1)

    print(f"Starting scrape from ID {start_id} to {end_id}")
    print(f"Already have {len(projects)} projects")

    current_id = start_id
    batch_projects = []

    while current_id <= end_id:
        if current_id in existing_ids:
            current_id += 1
            continue

        project = fetch_project(current_id)
        if project:
            batch_projects.append(project)
            print(f"[{current_id}] Found: {project.get('title', 'Unknown')[:50]}...")
        else:
            if current_id % 100 == 0:
                print(f"[{current_id}] No project found")

        # Save every batch_size projects
        if len(batch_projects) >= batch_size:
            projects.extend(batch_projects)
            save_projects(projects)
            progress['last_id'] = current_id
            progress['total_scraped'] = len(projects)
            save_progress(progress)
            print(f"Saved {len(projects)} projects total")
            batch_projects = []

        current_id += 1
        time.sleep(delay)

    # Save remaining
    if batch_projects:
        projects.extend(batch_projects)
        save_projects(projects)
        progress['last_id'] = current_id - 1
        progress['total_scraped'] = len(projects)
        save_progress(progress)

    print(f"Scraping complete. Total projects: {len(projects)}")
    return projects

def scrape_parallel(start_id, end_id, max_workers=5, batch_size=100):
    """Scrape using multiple threads."""
    projects = load_projects()
    existing_ids = {p['id'] for p in projects}

    ids_to_scrape = [i for i in range(start_id, end_id + 1) if i not in existing_ids]
    print(f"Scraping {len(ids_to_scrape)} project IDs with {max_workers} workers")

    new_projects = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_id = {executor.submit(fetch_project, pid): pid for pid in ids_to_scrape}

        for i, future in enumerate(as_completed(future_to_id)):
            pid = future_to_id[future]
            try:
                project = future.result()
                if project:
                    new_projects.append(project)
                    print(f"[{len(new_projects)}] ID {pid}: {project.get('title', 'Unknown')[:40]}...")

                # Save periodically
                if len(new_projects) % batch_size == 0 and new_projects:
                    projects.extend(new_projects)
                    save_projects(projects)
                    print(f"Saved {len(projects)} projects")
                    new_projects = []

            except Exception as e:
                print(f"Error with ID {pid}: {e}")

    # Save remaining
    if new_projects:
        projects.extend(new_projects)
        save_projects(projects)

    print(f"Complete. Total: {len(projects)} projects")
    return projects

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 2:
        start = int(sys.argv[1])
        end = int(sys.argv[2])
    else:
        # Full range: 1-30000 to catch all years (2014-2025)
        # ~16,199 projects expected
        start = 1
        end = 30000

    # Use parallel scraping for speed
    scrape_parallel(start, end, max_workers=10, batch_size=50)
