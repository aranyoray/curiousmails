#!/usr/bin/env python3
"""
Parse HTML student data from .docx files and convert to structured JSON
"""

import json
import re
from docx import Document
from bs4 import BeautifulSoup

def extract_html_from_docx(filename):
    """Extract all text (HTML) from a .docx file"""
    doc = Document(filename)
    full_text = []

    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text.strip())

    return ' '.join(full_text)

def parse_student_from_html(student_html):
    """Parse a single student's data from HTML"""
    soup = BeautifulSoup(student_html, 'html.parser')

    student = {
        'uni': 'Yale',  # All are Yale students
        'year': '',
        'first': '',
        'last': '',
        'major': '',
        'email': '',
        'notes': ''
    }

    # Extract name
    name_elem = soup.find('h3', class_='peoplegrid_name__h8uVB')
    if name_elem:
        name_text = name_elem.get_text(strip=True)
        # Format: "Last, First"
        if ',' in name_text:
            parts = name_text.split(',', 1)
            student['last'] = parts[0].strip()
            student['first'] = parts[1].strip() if len(parts) > 1 else ''
        else:
            student['last'] = name_text

    # Extract email
    email_link = soup.find('a', href=re.compile(r'^mailto:'))
    if email_link:
        student['email'] = email_link.get_text(strip=True)

    # Extract graduation year - find span after graduation cap icon
    grad_divs = soup.find_all('div', title='Graduation Year')
    for div in grad_divs:
        span = div.find('span')
        if span:
            student['year'] = span.get_text(strip=True)
            break

    # Extract residential college (can be major/notes)
    college_divs = soup.find_all('div', title='Residential College')
    for div in college_divs:
        span = div.find('span')
        if span:
            college = span.get_text(strip=True)
            student['notes'] = f"Residential College: {college}"
            break

    # Extract NetID and UPI
    buttons = soup.find_all('button', class_='chip_chip__dJvnn')
    extras = []
    for button in buttons:
        text = button.get_text(strip=True)
        if text:
            extras.append(text)

    if extras:
        if student['notes']:
            student['notes'] += ' | ' + ' | '.join(extras)
        else:
            student['notes'] = ' | '.join(extras)

    return student

def process_docx_file(filename):
    """Process a single .docx file and extract all student data"""
    print(f"\n=== Processing {filename} ===")

    html_content = extract_html_from_docx(filename)

    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all student entries
    students = []
    student_divs = soup.find_all('div', class_='peoplegrid_person__AF9Sl')

    print(f"Found {len(student_divs)} student records")

    for student_div in student_divs:
        try:
            student = parse_student_from_html(str(student_div))
            if student['last'] and student['email']:  # Valid student record
                student['source_file'] = filename
                students.append(student)
        except Exception as e:
            print(f"Error parsing student: {e}")

    print(f"Successfully parsed {len(students)} students")

    return students

def main():
    """Extract data from all .docx files"""
    docx_files = ['grad.docx', '2026.docx', '2027.docx', '2028.docx', '2029.docx']

    all_students = []

    for filename in docx_files:
        try:
            students = process_docx_file(filename)
            all_students.extend(students)
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n=== Summary ===")
    print(f"Total students extracted: {len(all_students)}")

    # Sort by year and last name
    all_students.sort(key=lambda x: (x['year'], x['last']))

    # Save to JSON
    output_file = 'data/students.json'
    with open(output_file, 'w') as f:
        json.dump(all_students, f, indent=2)

    print(f"Saved to {output_file}")

    # Print statistics
    year_counts = {}
    for student in all_students:
        year = student['year']
        year_counts[year] = year_counts.get(year, 0) + 1

    print(f"\nStudents by graduation year:")
    for year in sorted(year_counts.keys()):
        print(f"  {year}: {year_counts[year]}")

    # Print sample
    if all_students:
        print(f"\nSample student records:")
        for i, student in enumerate(all_students[:3]):
            print(f"\n{i+1}. {student['first']} {student['last']}")
            print(f"   Email: {student['email']}")
            print(f"   Year: {student['year']}")
            print(f"   Notes: {student['notes'][:80]}...")

    return all_students

if __name__ == '__main__':
    main()
