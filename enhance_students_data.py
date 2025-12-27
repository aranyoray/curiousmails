#!/usr/bin/env python3
"""
Extract major from notes field and enhance student data
"""

import json
import re

def extract_major_from_notes(notes):
    """Extract major from notes field"""
    if not notes:
        return ''

    # Split by pipes
    parts = [p.strip() for p in notes.split('|')]

    # Major is usually after NetID and UPI, before date/location
    # Look for academic-sounding terms
    majors = []
    academic_keywords = [
        'Engineering', 'Science', 'Studies', 'Arts', 'Economics', 'Biology',
        'Chemistry', 'Physics', 'Mathematics', 'Computer', 'History',
        'Literature', 'Philosophy', 'Psychology', 'Sociology', 'Political',
        'Affairs', 'Business', 'Law', 'Medicine', 'Architecture', 'Music',
        'Theater', 'Film', 'Statistics', 'Anthropology', 'Linguistics',
        'Neuroscience', 'Molecular', 'Environmental', 'Biomedical',
        'Electrical', 'Mechanical', 'Chemical', 'Civil', 'Aerospace'
    ]

    for part in parts:
        # Skip residential college, NetID, UPI, dates, locations
        if any(skip in part for skip in ['Residential College:', 'NetID', 'UPI', '/', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug']):
            continue

        # Skip if it's a country/state code or zipcode
        if re.match(r'^[A-Z]{2}( \d{5})?$', part.strip()):
            continue

        # Skip if it looks like a location (contains comma or state)
        if ',' in part:
            continue

        # Check if it contains academic keywords
        for keyword in academic_keywords:
            if keyword in part:
                majors.append(part)
                break

    # Return first major found, or empty string
    return majors[0] if majors else ''

def main():
    """Enhance student data with extracted majors"""

    # Load student data
    with open('data/students.json', 'r') as f:
        students = json.load(f)

    print(f"Processing {len(students)} student records...")

    # Extract majors
    for student in students:
        major = extract_major_from_notes(student['notes'])
        student['major'] = major

    # Count majors
    major_counts = {}
    for student in students:
        major = student['major'] if student['major'] else 'Undeclared'
        major_counts[major] = major_counts.get(major, 0) + 1

    print(f"\nMajor distribution (top 20):")
    sorted_majors = sorted(major_counts.items(), key=lambda x: x[1], reverse=True)
    for major, count in sorted_majors[:20]:
        print(f"  {major}: {count}")

    # Save enhanced data
    with open('data/students.json', 'w') as f:
        json.dump(students, f, indent=2)

    print(f"\nEnhanced student data saved to data/students.json")

    # Print samples
    print(f"\nSample student records with majors:")
    for student in students[:5]:
        print(f"\n{student['first']} {student['last']} ({student['year']})")
        print(f"  Major: {student['major'] or 'Undeclared'}")
        print(f"  Email: {student['email']}")

if __name__ == '__main__':
    main()
