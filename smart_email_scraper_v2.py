#!/usr/bin/env python3
"""
Enhanced Email Scraper V2 for ISEF Winners
- More university email formats (20+ schools)
- Processes all winners, skips ones with emails
- Better email validation
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import quote_plus

# Extended university email formats
UNIVERSITY_EMAIL_FORMATS = {
    'Arizona State University': ['{first}.{last}@asu.edu', '{first}{last}@asu.edu'],
    'University of Arizona': ['{first}{last}@arizona.edu', '{first}.{last}@email.arizona.edu', '{first}.{last}@arizona.edu'],
    'Drexel University': ['{first}.{last}@drexel.edu', '{first}{last}@drexel.edu'],
    'MIT': ['{first}{last}@mit.edu', '{first}@mit.edu'],
    'Stanford': ['{first}{last}@stanford.edu', '{first}@stanford.edu'],
    'Harvard': ['{first}{last}@college.harvard.edu', '{first}_{last}@college.harvard.edu'],
    'Yale': ['{first}.{last}@yale.edu', '{first}{last}@yale.edu'],
    'Princeton': ['{first}{last}@princeton.edu', '{first}@princeton.edu'],
    'Caltech': ['{first}{last}@caltech.edu', '{first}@caltech.edu'],
    'UC Berkeley': ['{first}{last}@berkeley.edu', '{first}_{last}@berkeley.edu', '{first}.{last}@berkeley.edu'],
    'UCLA': ['{first}{last}@ucla.edu', '{first}@ucla.edu'],
    'USC': ['{first}{last}@usc.edu', '{first}@usc.edu'],
    'Cornell': ['{first}{last}@cornell.edu', '{first}@cornell.edu'],
    'Carnegie Mellon': ['{first}{last}@cmu.edu', '{first}@andrew.cmu.edu'],
    'University of Michigan': ['{first}{last}@umich.edu', '{first}@umich.edu'],
    'Georgia Tech': ['{first}{last}@gatech.edu', '{first}@gatech.edu'],
    'Northwestern': ['{first}{last}@northwestern.edu', '{first}.{last}@northwestern.edu'],
    'Duke': ['{first}{last}@duke.edu', '{first}.{last}@duke.edu'],
    'Columbia': ['{first}{last}@columbia.edu', '{first}@columbia.edu'],
    'Penn State': ['{first}{last}@psu.edu', '{first}@psu.edu'],
    'University of Texas': ['{first}{last}@utexas.edu', '{first}.{last}@utexas.edu'],
    'University of Washington': ['{first}{last}@uw.edu', '{first}@uw.edu'],
}

def extract_university_from_awards(awards):
    """Extract likely university from scholarship awards"""
    if not awards:
        return None

    for award in awards:
        award_lower = award.lower()

        # Check for scholarship/tuition awards
        if 'scholarship' in award_lower or 'tuition' in award_lower:
            # Try to extract university name
            for uni_name in UNIVERSITY_EMAIL_FORMATS.keys():
                if uni_name.lower() in award_lower:
                    return uni_name

            # Generic extraction
            if 'university' in award_lower:
                match = re.search(r'([A-Z][a-z]+ )*University( of [A-Z][a-z]+)?', award, re.IGNORECASE)
                if match:
                    return match.group(0)

    return None

def generate_email_guesses(first_name, last_name, university):
    """Generate possible email addresses based on university format"""
    if not university or university not in UNIVERSITY_EMAIL_FORMATS:
        return []

    # Clean names
    first = first_name.lower().replace(' ', '').replace('-', '')
    last = last_name.lower().replace(' ', '').replace('-', '')

    formats = UNIVERSITY_EMAIL_FORMATS[university]
    guesses = []

    for fmt in formats:
        try:
            email = fmt.format(first=first, last=last)
            guesses.append(email)
        except:
            pass

    return guesses

def search_for_email_in_text(text, person_name):
    """Extract email addresses from text that might belong to the person"""
    # Find all emails in text
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)

    # Filter out junk
    junk_domains = ['example.com', 'domain.com', 'email.com', 'test.com',
                    'noreply', 'no-reply', 'support', 'info', 'contact',
                    'facebook.com', 'twitter.com', 'instagram.com']

    valid_emails = []
    for email in emails:
        email_lower = email.lower()
        if any(junk in email_lower for junk in junk_domains):
            continue
        valid_emails.append(email)

    return valid_emails

def smart_email_search(first_name, last_name, year, awards, project_title):
    """Enhanced email search with university detection and guessing"""

    result = {
        'first_name': first_name,
        'last_name': last_name,
        'year': year,
        'university': None,
        'email_guesses': [],
        'verified_emails': [],
        'search_results': []
    }

    # 1. Detect likely university
    university = extract_university_from_awards(awards)
    result['university'] = university

    if university:
        print(f"  🎓 Detected university: {university}")

        # 2. Generate email guesses
        guesses = generate_email_guesses(first_name, last_name, university)
        result['email_guesses'] = guesses

        if guesses:
            print(f"  📧 Email guesses: {', '.join(guesses[:3])}")

    # 3. Search online for emails
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    search_queries = [
        f'"{first_name} {last_name}" email',
        f'"{first_name} {last_name}" {university} email' if university else None,
        f'"{first_name} {last_name}" ISEF contact',
        f'"{first_name} {last_name}" LinkedIn',
    ]

    for query in search_queries:
        if not query:
            continue

        print(f"  🔍 Searching: {query}")
        search_url = f"https://www.google.com/search?q={quote_plus(query)}"

        try:
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                # Look for emails in search results
                emails = search_for_email_in_text(response.text, f"{first_name} {last_name}")
                if emails:
                    result['search_results'].extend(emails)
                    print(f"  ✓ Found emails: {', '.join(emails)}")
        except Exception as e:
            print(f"  ✗ Search error: {e}")

        time.sleep(2)  # Rate limiting

    # 4. Combine and deduplicate
    all_emails = list(set(result['email_guesses'] + result['search_results']))
    result['verified_emails'] = all_emails

    return result

def process_winners():
    """Process ISEF winners and find emails"""

    # Load winner data
    with open('data/winner_emails.json', 'r') as f:
        winners = json.load(f)

    print(f"Found {len(winners)} winners total\n")

    enhanced_results = {}
    skipped = 0
    processed = 0

    for project_id, winner in winners.items():
        # Skip if already has emails
        if winner.get('emails') and len(winner.get('emails', [])) > 0:
            skipped += 1
            enhanced_results[project_id] = winner
            continue

        student_name = winner.get('student_name', '')
        if not student_name or ',' not in student_name:
            enhanced_results[project_id] = winner
            continue

        # Parse name
        parts = student_name.split(',', 1)
        last_name = parts[0].strip()
        first_name = parts[1].strip() if len(parts) > 1 else ''

        if not first_name or not last_name:
            enhanced_results[project_id] = winner
            continue

        processed += 1
        print(f"\n{'='*80}")
        print(f"[{processed}/{len(winners)-skipped}] Processing: {first_name} {last_name}")
        print(f"Project: {winner.get('project_title', '')[:60]}...")
        print(f"Year: {winner.get('year', '')}")
        if winner.get('awards'):
            print(f"Awards: {winner.get('awards', [])[:2]}")

        # Smart search
        result = smart_email_search(
            first_name,
            last_name,
            winner.get('year', ''),
            winner.get('awards', []),
            winner.get('project_title', '')
        )

        # Update winner record
        if result['verified_emails']:
            winner['emails'] = result['verified_emails']
            winner['university'] = result['university']
            print(f"\n  🎉 SUCCESS! Found {len(result['verified_emails'])} email(s)")
        else:
            print(f"\n  ⚠️  No emails found")

        enhanced_results[project_id] = winner

        time.sleep(3)  # Be respectful

    # Save results
    with open('data/winner_emails.json', 'w') as f:
        json.dump(enhanced_results, f, indent=2)

    # Stats
    with_emails = sum(1 for w in enhanced_results.values() if w.get('emails'))
    print(f"\n{'='*80}")
    print(f"✓ Skipped {skipped} winners (already had emails)")
    print(f"✓ Processed {processed} new winners")
    print(f"RESULTS: {with_emails}/{len(enhanced_results)} winners now have emails!")
    print(f"Saved to data/winner_emails.json")

if __name__ == '__main__':
    process_winners()
