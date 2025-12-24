#!/usr/bin/env python3
"""
ISEF Project Categorizer
- Assigns primary category based on booth ID prefix
- Uses keyword-based NLP for cross-listings
- Maps old categories to new ones
"""

import json
import os
import re

DATA_FILE = "data/projects.json"
OUTPUT_FILE = "data/projects_categorized.json"

# Booth ID prefix to category mapping
BOOTH_TO_CATEGORY = {
    'ANIM': 'Animal Sciences',
    'BEHA': 'Behavioral & Social Sciences',
    'BICM': 'Biomedical & Health Sciences',
    'BITS': 'Biochemistry',
    'CBIO': 'Computational Biology & Bioinformatics',
    'CELL': 'Cellular & Molecular Biology',
    'CHEM': 'Chemistry',
    'COMP': 'Computational Science',
    'EAEV': 'Earth & Environmental Sciences',
    'ENEV': 'Environmental Engineering',
    'ENER': 'Energy: Sustainable Materials & Design',
    'ENSI': 'Engineering Technology: Statics & Dynamics',
    'ENBM': 'Biomedical Engineering',
    'ENMC': 'Engineering: Materials & Chemical',
    'ENMT': 'Engineering: Mechanical',
    'EBED': 'Embedded Systems',
    'MATH': 'Mathematics',
    'MCRO': 'Microbiology',
    'PHYS': 'Physics',
    'ROBT': 'Robotics & Intelligent Machines',
    'SOFT': 'Software Systems',
    'PLNT': 'Plant Sciences',
    # Old/legacy codes
    'MEHE': 'Biomedical & Health Sciences',
    'MEDH': 'Biomedical & Health Sciences',
    'ENSC': 'Earth & Environmental Sciences',
    'CSE': 'Software Systems',
    'CS': 'Software Systems',
    'EEM': 'Engineering: Mechanical',
    'ENGR': 'Engineering: Mechanical',
    'PHYA': 'Physics',
    'ENTE': 'Energy: Sustainable Materials & Design',
    'ET': 'Energy: Sustainable Materials & Design',
    'BOT': 'Plant Sciences',
    'ZOOL': 'Animal Sciences',
    'BSS': 'Behavioral & Social Sciences',
    'EAPS': 'Earth & Environmental Sciences',
    'ENMA': 'Environmental Engineering',
}

# Keywords for each category (for cross-listing detection)
CATEGORY_KEYWORDS = {
    'Animal Sciences': [
        'animal', 'mammal', 'bird', 'fish', 'insect', 'reptile', 'amphibian',
        'veterinary', 'livestock', 'wildlife', 'zoo', 'pet', 'canine', 'feline',
        'rodent', 'mouse', 'rat', 'monkey', 'primate', 'behavior', 'ecology',
        'predator', 'prey', 'migration', 'habitat', 'species', 'population'
    ],
    'Behavioral & Social Sciences': [
        'psychology', 'behavior', 'cognitive', 'social', 'memory', 'learning',
        'perception', 'emotion', 'stress', 'anxiety', 'depression', 'mental health',
        'survey', 'questionnaire', 'interview', 'demographic', 'economic',
        'education', 'decision', 'bias', 'attitude', 'personality', 'motivation'
    ],
    'Biomedical & Health Sciences': [
        'disease', 'patient', 'clinical', 'diagnosis', 'treatment', 'therapy',
        'medical', 'health', 'hospital', 'symptom', 'drug', 'pharmaceutical',
        'pathology', 'epidemiology', 'public health', 'nutrition', 'diet',
        'obesity', 'diabetes', 'cardiovascular', 'hypertension', 'inflammation'
    ],
    'Biochemistry': [
        'enzyme', 'protein', 'amino acid', 'metabolism', 'biochemical',
        'molecular weight', 'purification', 'assay', 'kinetics', 'substrate',
        'inhibitor', 'catalyst', 'reaction', 'pathway', 'synthesis', 'degradation',
        'lipid', 'carbohydrate', 'nucleotide', 'cofactor', 'vitamin'
    ],
    'Computational Biology & Bioinformatics': [
        'bioinformatics', 'genomics', 'proteomics', 'sequence', 'alignment',
        'phylogenetic', 'gene expression', 'microarray', 'rna-seq', 'chip-seq',
        'database', 'pipeline', 'algorithm', 'prediction', 'modeling',
        'network', 'systems biology', 'omics', 'annotation', 'variant'
    ],
    'Cellular & Molecular Biology': [
        'cell', 'cellular', 'molecular', 'gene', 'dna', 'rna', 'protein',
        'expression', 'transcription', 'translation', 'mutation', 'genome',
        'chromosome', 'nucleus', 'mitochondria', 'membrane', 'receptor',
        'signaling', 'apoptosis', 'proliferation', 'differentiation', 'stem cell'
    ],
    'Chemistry': [
        'chemical', 'reaction', 'synthesis', 'compound', 'molecule', 'element',
        'acid', 'base', 'ph', 'solution', 'concentration', 'titration',
        'spectroscopy', 'chromatography', 'organic', 'inorganic', 'analytical',
        'polymer', 'catalyst', 'oxidation', 'reduction', 'bonding'
    ],
    'Computational Science': [
        'algorithm', 'simulation', 'model', 'computer', 'software', 'code',
        'programming', 'data', 'analysis', 'machine learning', 'artificial intelligence',
        'neural network', 'deep learning', 'optimization', 'parallel', 'gpu',
        'numerical', 'computational', 'visualization', 'big data'
    ],
    'Earth & Environmental Sciences': [
        'environment', 'ecology', 'ecosystem', 'climate', 'weather', 'atmosphere',
        'ocean', 'marine', 'aquatic', 'water', 'soil', 'geology', 'mineral',
        'earthquake', 'volcano', 'fossil', 'biodiversity', 'conservation',
        'pollution', 'contamination', 'sustainability', 'carbon', 'greenhouse'
    ],
    'Environmental Engineering': [
        'water treatment', 'wastewater', 'filtration', 'purification', 'remediation',
        'pollution control', 'air quality', 'emissions', 'waste management',
        'recycling', 'sustainable', 'renewable', 'green', 'environmental',
        'bioremediation', 'phytoremediation', 'desalination', 'sewage'
    ],
    'Energy: Sustainable Materials & Design': [
        'energy', 'solar', 'wind', 'renewable', 'battery', 'fuel cell',
        'photovoltaic', 'turbine', 'power', 'electricity', 'efficiency',
        'storage', 'biofuel', 'hydrogen', 'sustainable', 'green energy',
        'thermal', 'heat', 'insulation', 'led', 'lighting'
    ],
    'Engineering Technology: Statics & Dynamics': [
        'structure', 'bridge', 'building', 'load', 'stress', 'strain',
        'force', 'tension', 'compression', 'beam', 'truss', 'foundation',
        'stability', 'vibration', 'dynamics', 'mechanics', 'construction',
        'civil engineering', 'architectural', 'design'
    ],
    'Biomedical Engineering': [
        'prosthetic', 'implant', 'medical device', 'biomaterial', 'tissue engineering',
        'rehabilitation', 'assistive', 'diagnostic device', 'biosensor', 'imaging',
        'mri', 'ultrasound', 'ecg', 'eeg', 'bionic', 'orthopedic', 'surgical',
        'wearable', 'health monitor', 'drug delivery'
    ],
    'Engineering: Materials & Chemical': [
        'material', 'nanoparticle', 'nanomaterial', 'composite', 'polymer',
        'ceramic', 'metal', 'alloy', 'coating', 'surface', 'corrosion',
        'strength', 'durability', 'thermal', 'electrical', 'optical',
        'characterization', 'synthesis', 'fabrication', 'processing'
    ],
    'Engineering: Mechanical': [
        'mechanical', 'machine', 'robot', 'motor', 'gear', 'pump', 'valve',
        'actuator', 'mechanism', 'automation', 'cad', '3d print', 'manufacturing',
        'design', 'prototype', 'testing', 'aerodynamic', 'fluid', 'thermal',
        'vehicle', 'drone', 'aircraft'
    ],
    'Embedded Systems': [
        'embedded', 'microcontroller', 'arduino', 'raspberry pi', 'sensor',
        'iot', 'internet of things', 'wireless', 'bluetooth', 'wifi',
        'real-time', 'firmware', 'hardware', 'circuit', 'pcb', 'gpio',
        'actuator', 'control system', 'monitoring', 'automation'
    ],
    'Mathematics': [
        'mathematical', 'equation', 'theorem', 'proof', 'algorithm', 'optimization',
        'statistics', 'probability', 'regression', 'correlation', 'analysis',
        'graph theory', 'number theory', 'geometry', 'topology', 'algebra',
        'calculus', 'differential', 'integral', 'matrix', 'vector'
    ],
    'Microbiology': [
        'bacteria', 'virus', 'fungus', 'yeast', 'microbe', 'microbial',
        'antibiotic', 'antimicrobial', 'infection', 'pathogen', 'culture',
        'colony', 'growth', 'fermentation', 'biofilm', 'probiotic',
        'gut microbiome', 'e. coli', 'salmonella', 'staphylococcus'
    ],
    'Physics': [
        'physics', 'quantum', 'particle', 'wave', 'frequency', 'wavelength',
        'electromagnetic', 'magnetic', 'electric', 'voltage', 'current',
        'resistance', 'capacitor', 'inductor', 'optics', 'lens', 'laser',
        'radiation', 'nuclear', 'thermodynamics', 'entropy', 'momentum'
    ],
    'Robotics & Intelligent Machines': [
        'robot', 'robotic', 'autonomous', 'navigation', 'path planning',
        'computer vision', 'object detection', 'tracking', 'lidar', 'slam',
        'manipulator', 'gripper', 'locomotion', 'humanoid', 'swarm',
        'artificial intelligence', 'machine learning', 'control'
    ],
    'Software Systems': [
        'software', 'app', 'application', 'website', 'web', 'mobile',
        'database', 'api', 'framework', 'programming', 'code', 'algorithm',
        'user interface', 'ux', 'cloud', 'security', 'encryption',
        'network', 'server', 'client', 'browser', 'operating system'
    ],
    'Plant Sciences': [
        'plant', 'seed', 'germination', 'growth', 'root', 'stem', 'leaf',
        'flower', 'fruit', 'photosynthesis', 'chlorophyll', 'fertilizer',
        'soil', 'irrigation', 'agriculture', 'crop', 'harvest', 'yield',
        'hydroponics', 'aquaponics', 'greenhouse', 'botanical'
    ],
}

def extract_booth_prefix(booth_id):
    """Extract category prefix from booth ID like EBED001T -> EBED"""
    if not booth_id:
        return None
    prefix = ''
    for char in booth_id:
        if char.isalpha():
            prefix += char
        else:
            break
    return prefix if prefix else None

def get_primary_category(project):
    """Get primary category from booth ID"""
    booth = project.get('booth', '')
    prefix = extract_booth_prefix(booth)
    if prefix and prefix in BOOTH_TO_CATEGORY:
        return BOOTH_TO_CATEGORY[prefix]
    # Fall back to existing category if it matches a valid one
    existing = project.get('category', '')
    # Normalize some known variations
    category_map = {
        'Biomedical and Health Sciences': 'Biomedical & Health Sciences',
        'Robotics and Intelligent Machines': 'Robotics & Intelligent Machines',
        'Computational Biology and Bioinformatics': 'Computational Biology & Bioinformatics',
        'Energy: Sustainable Materials and Design': 'Energy: Sustainable Materials & Design',
        'Materials Science': 'Engineering: Materials & Chemical',
        'Translational Medical Science': 'Biomedical & Health Sciences',
        'Systems Software': 'Software Systems',
        'Energy: Chemical': 'Energy: Sustainable Materials & Design',
        'Energy: Physical': 'Energy: Sustainable Materials & Design',
        'Physics and Astronomy': 'Physics',
        'Earth and Environmental Sciences': 'Earth & Environmental Sciences',
        'Cellular and Molecular Biology': 'Cellular & Molecular Biology',
        'Engineering Mechanics': 'Engineering: Mechanical',
        'Technology Enhances the Arts': 'Software Systems',
    }
    if existing in category_map:
        return category_map[existing]
    return existing if existing else 'Other'

def find_cross_listings(project, primary_category):
    """Find additional categories based on keyword matching"""
    text = ((project.get('title', '') + ' ' + project.get('abstract', '')).lower())

    cross_listings = set()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if category == primary_category:
            continue

        # Count keyword matches
        matches = sum(1 for kw in keywords if kw in text)

        # Threshold: need at least 2 keyword matches for cross-listing
        # Or 1 match if it's a very specific/rare keyword
        if matches >= 2:
            cross_listings.add(category)
        elif matches == 1:
            # Check for specific strong indicators
            strong_keywords = {
                'Plant Sciences': ['photosynthesis', 'germination', 'chlorophyll', 'hydroponics'],
                'Microbiology': ['bacteria', 'virus', 'antibiotic', 'pathogen', 'biofilm'],
                'Robotics & Intelligent Machines': ['robot', 'robotic', 'autonomous navigation'],
                'Embedded Systems': ['arduino', 'raspberry pi', 'microcontroller', 'iot'],
                'Biomedical Engineering': ['prosthetic', 'implant', 'medical device', 'biosensor'],
                'Environmental Engineering': ['wastewater', 'water treatment', 'bioremediation'],
            }
            if category in strong_keywords:
                for strong_kw in strong_keywords[category]:
                    if strong_kw in text:
                        cross_listings.add(category)
                        break

    return list(cross_listings)

def main():
    # Load projects
    print("Loading projects...")
    with open(DATA_FILE, 'r') as f:
        projects = json.load(f)

    print(f"Loaded {len(projects)} projects")

    # Process each project
    print("\nCategorizing projects...")

    for i, project in enumerate(projects):
        # Get primary category from booth ID
        primary = get_primary_category(project)
        project['primary_category'] = primary

        # Find cross-listings using keyword NLP
        cross_listings = find_cross_listings(project, primary)

        # Combine into categories list (primary first, then cross-listings)
        project['categories'] = [primary] + sorted(cross_listings)

        if (i + 1) % 1000 == 0:
            print(f"Processed {i + 1}/{len(projects)} projects...")

    # Stats
    print("\n" + "="*50)
    print("CATEGORIZATION COMPLETE")
    print("="*50)

    # Primary category distribution
    primary_counts = {}
    for p in projects:
        cat = p['primary_category']
        primary_counts[cat] = primary_counts.get(cat, 0) + 1

    print("\nPrimary category distribution:")
    for cat, count in sorted(primary_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"  {cat}: {count}")

    # Cross-listing stats
    multi_cat = sum(1 for p in projects if len(p['categories']) > 1)
    avg_cats = sum(len(p['categories']) for p in projects) / len(projects)
    max_cats = max(len(p['categories']) for p in projects)

    print(f"\nCross-listing statistics:")
    print(f"  Projects with multiple categories: {multi_cat} ({multi_cat*100/len(projects):.1f}%)")
    print(f"  Average categories per project: {avg_cats:.2f}")
    print(f"  Maximum categories on single project: {max_cats}")

    # Distribution of number of categories
    cat_dist = {}
    for p in projects:
        n = len(p['categories'])
        cat_dist[n] = cat_dist.get(n, 0) + 1

    print(f"\n  Distribution by number of categories:")
    for n in sorted(cat_dist.keys()):
        print(f"    {n} categories: {cat_dist[n]} projects")

    # Save output
    print(f"\nSaving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(projects, f, indent=2)

    # Also update the main projects.json with categories
    print(f"Updating {DATA_FILE} with categories...")
    with open(DATA_FILE, 'w') as f:
        json.dump(projects, f, indent=2)

    print("\nDone!")

if __name__ == "__main__":
    main()
