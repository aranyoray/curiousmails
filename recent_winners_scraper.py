#!/usr/bin/env python3
"""
Enhanced ISEF Winner Scraper - V3
Focuses on recent winners (2019+) likely still in undergrad/grad
Extracts: university, major, emails, skills/specializations
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import quote_plus

# University email formats
UNIVERSITY_EMAIL_FORMATS = {
    'Arizona State University': ['{first}.{last}@asu.edu', '{first}{last}@asu.edu'],
    'University of Arizona': ['{first}{last}@arizona.edu', '{first}.{last}@arizona.edu'],
    'Drexel University': ['{first}.{last}@drexel.edu', '{first}{last}@drexel.edu'],
    'MIT': ['{first}{last}@mit.edu', '{first}@mit.edu'],
    'Stanford': ['{first}{last}@stanford.edu', '{first}@stanford.edu'],
    'Harvard': ['{first}{last}@college.harvard.edu', '{first}@college.harvard.edu'],
    'Yale': ['{first}.{last}@yale.edu', '{first}{last}@yale.edu'],
    'Princeton': ['{first}{last}@princeton.edu', '{first}@princeton.edu'],
    'Caltech': ['{first}{last}@caltech.edu', '{first}@caltech.edu'],
    'UC Berkeley': ['{first}{last}@berkeley.edu', '{first}.{last}@berkeley.edu'],
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

def extract_skills_from_project(project_title, abstract, category):
    """Extract skills and specializations from ISEF project"""
    skills = set()

    # Common STEM skills keywords
    skill_keywords = {
        'machine learning', 'deep learning', 'neural networks', 'AI', 'artificial intelligence',
        'data analysis', 'statistics', 'biostatistics', 'computational biology',
        'programming', 'python', 'java', 'C++', 'matlab', 'R programming',
        'robotics', 'computer vision', 'image processing', 'signal processing',
        'molecular biology', 'genetics', 'biochemistry', 'cell biology',
        'organic chemistry', 'inorganic chemistry', 'analytical chemistry',
        'physics simulation', 'quantum mechanics', 'optics', 'astrophysics',
        'engineering design', 'mechanical engineering', 'electrical engineering',
        'biomedical engineering', 'environmental science', 'sustainability',
        'mathematical modeling', 'algorithm design', 'optimization',
        'web development', 'mobile development', 'app development',
        'research methodology', 'experimental design', 'data visualization'
    }

    text = f"{project_title} {abstract}".lower()

    # Extract matching skills
    for skill in skill_keywords:
        if skill in text:
            skills.add(skill.title())

    # Add category as a skill
    if category:
        skills.add(category)

    return list(skills)[:5]  # Limit to top 5

def search_linkedin_profile(first_name, last_name):
    """Search for LinkedIn profile and extract info"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    result = {
        'university': None,
        'major': None,
        'skills': [],
        'profile_url': None
    }

    # Search LinkedIn via Google
    query = f'"{first_name} {last_name}" site:linkedin.com/in'
    search_url = f"https://www.google.com/search?q={quote_plus(query)}"

    try:
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract LinkedIn URL
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if 'linkedin.com/in/' in href:
                    # Clean URL
                    match = re.search(r'(https://[a-z]+\.linkedin\.com/in/[^&]+)', href)
                    if match:
                        result['profile_url'] = match.group(1)
                        break

            # Look for university and major in snippet text
            text = soup.get_text()

            # Common university patterns in LinkedIn snippets
            uni_patterns = [
                r'([\w\s]+ University)',
                r'(MIT|Stanford|Harvard|Yale|Princeton|Caltech|Cornell|Columbia|Duke)',
                r'University of ([\w\s]+)',
            ]

            for pattern in uni_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result['university'] = match.group(0)
                    break

            # Look for major/field
            major_patterns = [
                r'studying ([\w\s]+) at',
                r'(Computer Science|Engineering|Biology|Chemistry|Physics|Mathematics) student',
                r'majoring in ([\w\s]+)',
            ]

            for pattern in major_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result['major'] = match.group(1)
                    break

    except Exception as e:
        print(f"    ✗ LinkedIn search error: {e}")

    return result

def extract_university_from_awards(awards):
    """Extract university from scholarship awards"""
    if not awards:
        return None

    for award in awards:
        if 'scholarship' in award.lower() or 'tuition' in award.lower():
            for uni_name in UNIVERSITY_EMAIL_FORMATS.keys():
                if uni_name.lower() in award.lower():
                    return uni_name

            if 'university' in award.lower():
                match = re.search(r'([A-Z][a-z]+ )*University( of [A-Z][a-z]+)?', award)
                if match:
                    return match.group(0)
    return None

def generate_email_guesses(first_name, last_name, university):
    """Generate email guesses"""
    if not university or university not in UNIVERSITY_EMAIL_FORMATS:
        return []

    first = first_name.lower().replace(' ', '').replace('-', '')
    last = last_name.lower().replace(' ', '').replace('-', '')

    guesses = []
    for fmt in UNIVERSITY_EMAIL_FORMATS[university]:
        try:
            guesses.append(fmt.format(first=first, last=last))
        except:
            pass

    return guesses

def process_recent_winners():
    """Process recent ISEF winners (2019+)"""

    # Load projects database
    with open('data/projects.json', 'r') as f:
        projects = json.load(f)

    # Filter for recent award winners (2019+)
    recent_winners = [p for p in projects
                     if p.get('awards') and len(p.get('awards', [])) > 0
                     and int(p.get('year', '0')) >= 2019]

    print(f"Found {len(recent_winners)} recent award winners (2019+)")
    print("These students are likely still in undergrad/grad school\n")

    results = []

    # Process first 50 winners
    for i, project in enumerate(recent_winners[:50], 1):
        # Extract name from ISEF abstract page
        project_id = project.get('id')

        print(f"\n{'='*80}")
        print(f"[{i}/50] Project ID: {project_id}")
        print(f"Title: {project.get('title', '')[:60]}...")
        print(f"Year: {project.get('year')}")
        print(f"Category: {project.get('category', 'Unknown')}")

        # Try to fetch student name from ISEF page
        try:
            url = f"https://abstracts.societyforscience.org/Home/FullAbstract?projectId={project_id}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Look for "Finalist Names:" section
                finalist_section = soup.find(text=re.compile('Finalist Names?:', re.IGNORECASE))
                student_name = None

                if finalist_section:
                    parent = finalist_section.find_parent()
                    if parent:
                        # Get text after the label
                        name_text = parent.get_text()
                        match = re.search(r'Finalist Names?:\s*(.+)', name_text, re.IGNORECASE)
                        if match:
                            student_name = match.group(1).strip().split('\n')[0]

                if not student_name:
                    print("  ⚠️  Could not extract student name")
                    continue

                print(f"  👤 Student: {student_name}")

                # Parse name
                if ',' in student_name:
                    parts = student_name.split(',', 1)
                    last_name = parts[0].strip()
                    first_name = parts[1].strip().split()[0] if parts[1].strip() else ''
                else:
                    name_parts = student_name.split()
                    first_name = name_parts[0] if name_parts else ''
                    last_name = name_parts[-1] if len(name_parts) > 1 else ''

                if not first_name or not last_name:
                    print("  ⚠️  Could not parse name")
                    continue

                # Extract skills from project
                skills = extract_skills_from_project(
                    project.get('title', ''),
                    project.get('abstract', ''),
                    project.get('category', '')
                )

                print(f"  🔧 Skills from project: {', '.join(skills[:3])}...")

                # Search LinkedIn
                print(f"  🔍 Searching LinkedIn for {first_name} {last_name}...")
                linkedin_data = search_linkedin_profile(first_name, last_name)

                # Detect university
                university = linkedin_data.get('university') or extract_university_from_awards(project.get('awards', []))

                if university:
                    print(f"  🎓 University: {university}")

                if linkedin_data.get('major'):
                    print(f"  📚 Major: {linkedin_data['major']}")

                # Generate email guesses
                emails = []
                if university:
                    emails = generate_email_guesses(first_name, last_name, university)
                    if emails:
                        print(f"  📧 Email guesses: {emails[0]}")

                # Combine skills
                all_skills = list(set(skills + linkedin_data.get('skills', [])))[:5]

                # Build result
                result = {
                    'project_id': project_id,
                    'name': student_name,
                    'first_name': first_name,
                    'last_name': last_name,
                    'year': project.get('year'),
                    'university': university or '',
                    'major': linkedin_data.get('major') or project.get('category', ''),
                    'emails': emails,
                    'skills': all_skills,
                    'linkedin': linkedin_data.get('profile_url', ''),
                    'project_title': project.get('title', ''),
                    'awards': project.get('awards', [])
                }

                results.append(result)

                if university and emails:
                    print(f"  ✅ SUCCESS! Found university + emails")
                elif university:
                    print(f"  ✓ Found university (no email)")
                else:
                    print(f"  ⚠️  No university found")

        except Exception as e:
            print(f"  ✗ Error: {e}")

        time.sleep(3)  # Rate limiting

    # Save results
    output_file = 'data/recent_winners_enhanced.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    # Stats
    with_uni = sum(1 for r in results if r['university'])
    with_emails = sum(1 for r in results if r['emails'])
    with_major = sum(1 for r in results if r['major'])

    print(f"\n{'='*80}")
    print(f"✅ COMPLETE!")
    print(f"   Processed: {len(results)} winners")
    print(f"   With university: {with_uni}/{len(results)}")
    print(f"   With emails: {with_emails}/{len(results)}")
    print(f"   With major: {with_major}/{len(results)}")
    print(f"   Saved to: {output_file}")

if __name__ == '__main__':
    process_recent_winners()
