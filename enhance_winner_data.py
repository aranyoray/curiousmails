#!/usr/bin/env python3
"""
Enhance winner_emails.json with category data from projects.json
"""

import json

# Load both files
with open('data/projects.json', 'r') as f:
    projects = json.load(f)

with open('data/winner_emails.json', 'r') as f:
    winners = json.load(f)

# Create a lookup dictionary from projects by ID
projects_by_id = {str(p['id']): p for p in projects}

# Enhance winner data
for project_id, winner in winners.items():
    if project_id in projects_by_id:
        project = projects_by_id[project_id]

        # Add category if not present
        if 'category' not in winner:
            winner['category'] = project.get('category', '')

        # Add country if not present
        if 'country' not in winner:
            winner['country'] = project.get('country', '')

# Save enhanced data
with open('data/winner_emails.json', 'w') as f:
    json.dump(winners, f, indent=2)

print(f"Enhanced {len(winners)} winner records with category data")
