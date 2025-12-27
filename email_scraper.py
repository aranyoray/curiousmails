#!/usr/bin/env python3
"""
Email Scraper for ISEF Award Winners
Searches for email addresses of award-winning project students
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os
from urllib.parse import quote_plus
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_FILE = "data/projects.json"
EMAILS_FILE = "data/winner_emails.json"

def extract_emails(text):
    """Extract email addresses from text using regex."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return list(set(re.findall(email_pattern, text)))

def search_google(query, num_results=10):
    """Search Google for a query and return results."""
    # Use Google Custom Search API alternative - scraping Google directly
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={num_results}"

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
        return ""
    except Exception as e:
        print(f"Error searching Google: {e}")
        return ""

def search_duckduckgo(query):
    """Search DuckDuckGo for a query and return results."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
        return ""
    except Exception as e:
        print(f"Error searching DuckDuckGo: {e}")
        return ""

def search_linkedin(name):
    """Search LinkedIn for a person and extract potential contact info."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    # Search LinkedIn via Google
    query = f"{name} site:linkedin.com"
    try:
        response = requests.get(f"https://www.google.com/search?q={quote_plus(query)}",
                              headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Extract LinkedIn URLs
            links = []
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if 'linkedin.com/in/' in href:
                    links.append(href)
            return links[:3]  # Return top 3 LinkedIn profiles
    except Exception as e:
        print(f"Error searching LinkedIn: {e}")

    return []

def find_email_for_person(name, project_title=None, year=None):
    """
    Search for email address of a person using various methods.

    Args:
        name: Person's name
        project_title: Optional project title for context
        year: Optional year for context

    Returns:
        Dictionary with found emails and sources
    """
    result = {
        'name': name,
        'emails': [],
        'linkedin_profiles': [],
        'search_queries_used': []
    }

    if not name or len(name) < 3:
        return result

    # Build search queries
    queries = [
        f'"{name}" email',
        f'"{name}" contact',
        f'"{name}" ISEF email',
    ]

    if project_title:
        queries.append(f'"{name}" "{project_title}" email')

    if year:
        queries.append(f'"{name}" ISEF {year} email')

    all_emails = []

    # Try each search query
    for query in queries[:3]:  # Limit to 3 queries to avoid rate limiting
        result['search_queries_used'].append(query)

        # Try DuckDuckGo first (less likely to block)
        print(f"  Searching: {query}")
        html = search_duckduckgo(query)

        if html:
            emails = extract_emails(html)
            all_emails.extend(emails)

            # Also check for common academic/professional domains
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()
            emails_in_text = extract_emails(text)
            all_emails.extend(emails_in_text)

        time.sleep(2)  # Be polite, don't hammer servers

    # Search LinkedIn
    linkedin_profiles = search_linkedin(name)
    result['linkedin_profiles'] = linkedin_profiles

    # Filter and deduplicate emails
    # Remove common junk emails
    filtered_emails = []
    junk_domains = ['example.com', 'test.com', 'google.com', 'facebook.com',
                    'twitter.com', 'instagram.com', 'youtube.com']

    for email in set(all_emails):
        email_lower = email.lower()
        domain = email_lower.split('@')[1] if '@' in email_lower else ''

        # Skip junk domains
        if any(junk in domain for junk in junk_domains):
            continue

        # Prefer .edu, .ac, or professional domains
        filtered_emails.append(email)

    result['emails'] = list(set(filtered_emails))

    return result

def scrape_winner_emails(limit=None, skip_existing=True):
    """
    Scrape emails for ISEF award winners.

    Args:
        limit: Maximum number of winners to process (None for all)
        skip_existing: Skip winners we've already processed
    """
    # Load projects
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found. Run scraper.py first.")
        return

    with open(DATA_FILE, 'r') as f:
        projects = json.load(f)

    # Load existing emails
    existing_emails = {}
    if skip_existing and os.path.exists(EMAILS_FILE):
        with open(EMAILS_FILE, 'r') as f:
            existing_emails = json.load(f)

    # Filter for award winners
    winners = [p for p in projects if p.get('awards') and len(p.get('awards', [])) > 0]

    print(f"Found {len(winners)} award-winning projects")

    if limit:
        winners = winners[:limit]
        print(f"Processing first {limit} winners")

    results = existing_emails.copy() if skip_existing else {}
    processed = 0

    for project in winners:
        project_id = str(project['id'])

        # Skip if already processed
        if skip_existing and project_id in results:
            continue

        # Try to get student name from project data
        # If not in data, we'll need to scrape it from the website
        student_name = project.get('student_name')

        if not student_name:
            # Scrape the project page to get student name
            print(f"\nProject {project_id}: Fetching student name...")
            url = f"https://abstracts.societyforscience.org/Home/FullAbstract?projectId={project_id}"
            try:
                response = requests.get(url, timeout=30, verify=False)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    content = soup.find('div', class_='container')
                    if content:
                        labels = content.find_all('strong')
                        for label in labels:
                            label_text = label.get_text(strip=True).lower()
                            if 'finalist' in label_text or 'student' in label_text:
                                # Use parent text approach
                                parent = label.parent
                                if parent and ':' in parent.get_text():
                                    full_text = parent.get_text()
                                    value = full_text.split(':', 1)[1].strip()
                                    student_name = value.split('\n')[0].strip()
                                    if student_name and len(student_name) < 100:
                                        break
                time.sleep(1)
            except Exception as e:
                print(f"  Error fetching student name: {e}")

        if not student_name:
            print(f"\nProject {project_id}: No student name found, skipping")
            continue

        print(f"\nProject {project_id}: {student_name}")
        print(f"  Title: {project.get('title', 'N/A')[:60]}...")
        print(f"  Awards: {', '.join(project.get('awards', []))[:80]}")

        # Search for email
        email_result = find_email_for_person(
            student_name,
            project.get('title'),
            project.get('year')
        )

        # Save result
        results[project_id] = {
            'student_name': student_name,
            'project_title': project.get('title'),
            'year': project.get('year'),
            'awards': project.get('awards', []),
            'emails': email_result['emails'],
            'linkedin_profiles': email_result['linkedin_profiles'],
            'search_queries': email_result['search_queries_used']
        }

        if email_result['emails']:
            print(f"  ✓ Found {len(email_result['emails'])} email(s): {', '.join(email_result['emails'])}")
        else:
            print(f"  ✗ No emails found")

        if email_result['linkedin_profiles']:
            print(f"  LinkedIn: {len(email_result['linkedin_profiles'])} profile(s) found")

        processed += 1

        # Save progress every 10 projects
        if processed % 10 == 0:
            with open(EMAILS_FILE, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n--- Saved progress: {processed} winners processed ---")

        # Rate limiting - be nice to servers
        time.sleep(3)

    # Final save
    with open(EMAILS_FILE, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n=== Complete ===")
    print(f"Processed: {processed} winners")
    print(f"Total results: {len(results)}")
    print(f"Results saved to: {EMAILS_FILE}")

    # Summary statistics
    with_emails = sum(1 for r in results.values() if r.get('emails'))
    print(f"Winners with emails found: {with_emails}/{len(results)}")

if __name__ == "__main__":
    import sys

    # Allow specifying limit from command line
    limit = None
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])

    scrape_winner_emails(limit=limit)
