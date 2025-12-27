#!/usr/bin/env python3
"""
Generate formatted table data from winner_emails.json
Extracts university, major, and formats data for the winners table
"""

import json
import re

def parse_name(name_str):
    """Parse 'Last, First' format into separate fields"""
    if not name_str or ',' not in name_str:
        return '', name_str or ''

    parts = name_str.split(',', 1)
    return parts[0].strip(), parts[1].strip()

def extract_university(awards):
    """Extract university name from awards"""
    if not awards:
        return ''

    for award in awards:
        # Look for university patterns
        patterns = [
            r'([\w\s]+University(?: of [\w\s]+)?)',
            r'([\w\s]+Institute(?: of [\w\s]+)?)',
            r'([\w\s]+College)',
            r'(MIT|Stanford|Harvard|Yale|Princeton|Cornell|Columbia|Penn State|UC Berkeley|UCLA|USC|Caltech|Carnegie Mellon)'
        ]

        for pattern in patterns:
            match = re.search(pattern, award, re.IGNORECASE)
            if match:
                uni = match.group(1).strip()
                # Clean up common prefixes
                uni = re.sub(r'^(The |A )', '', uni)
                return uni

    return ''

def load_and_format_data():
    """Load winner emails and format for table"""

    with open('data/winner_emails.json', 'r') as f:
        data = json.load(f)

    formatted_winners = []

    for project_id, winner in data.items():
        last_name, first_name = parse_name(winner.get('student_name', ''))
        uni = extract_university(winner.get('awards', []))
        year = winner.get('year', '')

        # Try to get category from project data
        category = winner.get('category', '')

        # Get email
        emails = winner.get('emails', [])
        email = emails[0] if emails else ''

        # Format notes from awards
        awards = winner.get('awards', [])
        notes = '; '.join(awards) if awards else ''

        formatted_winners.append({
            'uni': uni,
            'year': year,
            'first': first_name,
            'last': last_name,
            'major': category,
            'email': email,
            'notes': notes,
            'project_title': winner.get('project_title', ''),
            'linkedin': winner.get('linkedin_profiles', [])
        })

    return formatted_winners

def print_table(winners):
    """Print winners in tab-separated table format"""
    # Print header
    print("Uni\tYear\tFirst\tLast\tMajor\tEmail\tNotes")
    print("-" * 120)

    # Print each winner
    for w in winners:
        # Truncate notes if too long
        notes = w['notes'][:100] + '...' if len(w['notes']) > 100 else w['notes']

        print(f"{w['uni']}\t{w['year']}\t{w['first']}\t{w['last']}\t{w['major']}\t{w['email']}\t{notes}")

    print("-" * 120)
    print(f"\nTotal winners: {len(winners)}")
    print(f"With emails: {sum(1 for w in winners if w['email'])}")

if __name__ == '__main__':
    winners = load_and_format_data()
    print_table(winners)
