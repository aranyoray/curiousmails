#!/usr/bin/env python3
"""
Enhance existing winners with major and skills data
Uses the winner_emails.json we already have with names
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import quote_plus

def extract_skills_from_project(project_title, abstract, category):
    """Extract 4-5 skills from ISEF project"""
    skills = set()

    skill_keywords = {
        'Machine Learning': ['machine learning', 'ML', 'neural network', 'deep learning'],
        'Data Analysis': ['data analysis', 'statistics', 'data science', 'analytics'],
        'Programming': ['programming', 'coding', 'python', 'java', 'C++'],
        'AI': ['artificial intelligence', 'AI', 'computer vision', 'NLP'],
        'Robotics': ['robotics', 'robot', 'autonomous'],
        'Biochemistry': ['biochemistry', 'molecular', 'protein', 'enzyme'],
        'Chemistry': ['chemistry', 'chemical', 'synthesis', 'compound'],
        'Biology': ['biology', 'biological', 'cell', 'DNA', 'genetic'],
        'Physics': ['physics', 'quantum', 'optics', 'mechanics'],
        'Engineering': ['engineering', 'design', 'prototype', 'system'],
        'Environmental Science': ['environmental', 'climate', 'sustainability', 'ecosystem'],
        'Biomedical': ['biomedical', 'medical', 'health', 'disease'],
        'Research': ['research', 'experiment', 'study', 'investigation'],
        'Algorithm Design': ['algorithm', 'optimization', 'computational'],
        'Web Development': ['web', 'app', 'software development'],
    }

    text = f"{project_title} {abstract}".lower()

    for skill_name, keywords in skill_keywords.items():
        if any(kw in text for kw in keywords):
            skills.add(skill_name)

    # Add category
    if category:
        skills.add(category)

    return sorted(list(skills))[:5]

def search_linkedin_for_major(first_name, last_name, current_year=2025):
    """Search LinkedIn snippet for major/field"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    result = {
        'university': None,
        'major': None,
        'graduation_year': None
    }

    query = f'"{first_name} {last_name}" linkedin student'
    search_url = f"https://www.google.com/search?q={quote_plus(query)}"

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            text = response.text

            # Look for graduation year (2025-2029 means undergrad/grad)
            year_match = re.search(r"'(202[5-9])", text)
            if year_match:
                result['graduation_year'] = year_match.group(1)

            # Look for major
            major_patterns = [
                r'studying ([\w\s]+) at',
                r'(Computer Science|Engineering|Biology|Chemistry|Physics|Mathematics|Biomedical Engineering|Mechanical Engineering|Electrical Engineering|Chemical Engineering) student',
                r'majoring in ([\w\s&]+)',
                r'(\w+ Engineering) major',
            ]

            for pattern in major_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result['major'] = match.group(1).strip()
                    break

            # Look for university
            uni_patterns = [
                r'at (MIT|Stanford|Harvard|Yale|Princeton|Caltech|Cornell|Columbia|Duke)',
                r'at ([\w\s]+ University)',
                r'University of ([\w\s]+)',
            ]

            for pattern in uni_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    uni = match.group(0).replace('at ', '').strip()
                    result['university'] = uni
                    break

    except Exception as e:
        print(f"    LinkedIn error: {e}")

    return result

def enhance_winners():
    """Enhance existing winners with major and skills"""

    # Load existing winners
    with open('data/winner_emails.json', 'r') as f:
        winners = json.load(f)

    # Load projects for abstracts
    with open('data/projects.json', 'r') as f:
        projects = json.load(f)

    projects_by_id = {str(p['id']): p for p in projects}

    print(f"Enhancing {len(winners)} winners with major and skills data\n")

    enhanced = 0

    for project_id, winner in winners.items():
        print(f"\n{'='*80}")
        print(f"Project {project_id}: {winner.get('student_name', 'Unknown')}")
        print(f"Year: {winner.get('year')}")

        # Get project data
        project = projects_by_id.get(project_id, {})

        # Extract skills from project
        skills = extract_skills_from_project(
            winner.get('project_title', ''),
            project.get('abstract', ''),
            project.get('category', '')
        )

        print(f"  🔧 Skills extracted: {', '.join(skills)}")

        # Get major from LinkedIn if we have a name
        major = None
        linkedin_uni = None

        if winner.get('student_name') and ',' in winner['student_name']:
            parts = winner['student_name'].split(',', 1)
            last_name = parts[0].strip()
            first_name = parts[1].strip().split()[0] if parts[1].strip() else ''

            if first_name and last_name:
                print(f"  🔍 Searching LinkedIn for {first_name} {last_name}...")
                linkedin_data = search_linkedin_for_major(first_name, last_name)

                if linkedin_data.get('major'):
                    major = linkedin_data['major']
                    print(f"  📚 Found major: {major}")

                if linkedin_data.get('university'):
                    linkedin_uni = linkedin_data['university']
                    print(f"  🎓 Found university: {linkedin_uni}")

                if linkedin_data.get('graduation_year'):
                    print(f"  🎓 Graduation year: {linkedin_data['graduation_year']}")

        # Update winner record
        winner['skills'] = ', '.join(skills) if skills else ''
        winner['major'] = major or project.get('category', '')

        # Update university if found on LinkedIn
        if linkedin_uni and not winner.get('university'):
            winner['university'] = linkedin_uni

        if skills or major:
            enhanced += 1

        time.sleep(2)  # Rate limiting

    # Save
    with open('data/winner_emails.json', 'w') as f:
        json.dump(winners, f, indent=2)

    print(f"\n{'='*80}")
    print(f"✅ Enhanced {enhanced}/{len(winners)} winners")
    print(f"   Added skills and major information")
    print(f"   Saved to data/winner_emails.json")

if __name__ == '__main__':
    enhance_winners()
