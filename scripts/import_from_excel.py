"""
Import data from Excel file to JSON structure
"""
import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path
import re


def clean_date(date_str):
    """Convert various date formats to ISO format (YYYY-MM-DD)"""
    if pd.isna(date_str) or date_str == '?' or date_str == '':
        return None
    
    date_str = str(date_str).strip()
    
    # Already in good format
    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        return date_str
    
    # Handle "18 мая 2000" format
    months_ru = {
        'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
        'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
        'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12'
    }
    
    for month_ru, month_num in months_ru.items():
        if month_ru in date_str.lower():
            parts = date_str.split()
            day = parts[0] if parts[0].isdigit() else '01'
            year = parts[-1] if parts[-1].isdigit() else '2000'
            return f"{year}-{month_num}-{day.zfill(2)}"
    
    # Handle "2008 г." or "июнь 2000 г." format
    if 'г.' in date_str:
        date_str = date_str.replace('г.', '').strip()
        for month_ru, month_num in months_ru.items():
            if month_ru in date_str.lower():
                year = re.search(r'\d{4}', date_str)
                if year:
                    return f"{year.group()}-{month_num}-01"
        # Just year
        year = re.search(r'\d{4}', date_str)
        if year:
            return f"{year.group()}-01-01"
    
    # Handle just year
    if re.match(r'^\d{4}$', date_str):
        return f"{date_str}-01-01"
    
    # Can't parse - return as is
    return date_str


def generate_id(text, prefix=''):
    """Generate a simple ID from text"""
    if pd.isna(text):
        return None
    # Remove special characters and convert to lowercase
    clean = re.sub(r'[^\w\s-]', '', str(text).lower())
    clean = re.sub(r'[-\s]+', '_', clean)
    if prefix:
        return f"{prefix}_{clean[:50]}"
    return clean[:50]


def import_excel_data(excel_path, output_dir):
    """Import data from Excel file and create JSON structure"""
    
    # Read Excel
    df = pd.read_excel(excel_path)
    
    # Rename columns for easier access
    df.columns = ['department', 'subdepartment', 'position_title', 'person_name', 
                  'start_date', 'end_date'] + [f'extra_{i}' for i in range(len(df.columns) - 6)]
    
    # Remove header row
    df = df[1:].reset_index(drop=True)
    
    # Data structures
    positions = {}
    persons = {}
    position_counter = 1
    person_counter = 1
    
    current_department = None
    current_subdepartment = None
    
    # Process each row
    for idx, row in df.iterrows():
        # Update current department if present
        if pd.notna(row['department']) and row['department'].strip():
            current_department = row['department'].strip()
        
        # Update subdepartment if present
        if pd.notna(row['subdepartment']) and row['subdepartment'].strip():
            current_subdepartment = row['subdepartment'].strip()
        
        # Skip rows without position title
        if pd.isna(row['position_title']) or not row['position_title'].strip():
            continue
        
        position_title = row['position_title'].strip()
        
        # Create or get position ID
        position_key = f"{current_department}_{position_title}"
        
        if position_key not in positions:
            position_id = f"pos_{str(position_counter).zfill(3)}"
            positions[position_key] = {
                'id': position_id,
                'title': position_title,
                'department': current_department,
                'subdepartment': current_subdepartment if pd.notna(current_subdepartment) else None,
                'level': 'federal',  # Default
                'created_at': datetime.now().isoformat()
            }
            position_counter += 1
        else:
            position_id = positions[position_key]['id']
        
        # Process person if present
        if pd.notna(row['person_name']) and row['person_name'].strip():
            person_name = row['person_name'].strip()
            
            # Create or get person
            if person_name not in persons:
                person_id = f"person_{str(person_counter).zfill(3)}"
                persons[person_name] = {
                    'id': person_id,
                    'name': person_name,
                    'positions': []
                }
                person_counter += 1
            else:
                person_id = persons[person_name]['id']
            
            # Add position assignment
            start_date = clean_date(row['start_date'])
            end_date = clean_date(row['end_date'])
            
            position_assignment = {
                'position_id': position_id,
                'start_date': start_date,
                'end_date': end_date,
                'is_current': pd.isna(row['end_date'])
            }
            
            persons[person_name]['positions'].append(position_assignment)
    
    # Save to JSON files
    positions_file = os.path.join(output_dir, 'data', 'positions', 'positions.json')
    persons_file = os.path.join(output_dir, 'data', 'persons', 'persons.json')
    
    os.makedirs(os.path.dirname(positions_file), exist_ok=True)
    os.makedirs(os.path.dirname(persons_file), exist_ok=True)
    
    # Convert to lists
    positions_list = list(positions.values())
    persons_list = list(persons.values())
    
    # Save positions
    with open(positions_file, 'w', encoding='utf-8') as f:
        json.dump({'positions': positions_list}, f, ensure_ascii=False, indent=2)
    
    # Save persons
    with open(persons_file, 'w', encoding='utf-8') as f:
        json.dump({'persons': persons_list}, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Import complete!")
    print(f"   Positions: {len(positions_list)}")
    print(f"   Persons: {len(persons_list)}")
    print(f"   Files saved to: {output_dir}/data/")
    
    return positions_list, persons_list


if __name__ == '__main__':
    # Paths
    excel_path = '/mnt/user-data/uploads/список_гос_ведомств_и_корпораций__1_.xlsx'
    output_dir = '/home/claude/officials_tracker'
    
    # Import
    positions, persons = import_excel_data(excel_path, output_dir)
    
    # Show sample
    print("\n" + "="*80)
    print("Sample positions (first 3):")
    for pos in positions[:3]:
        print(f"  {pos['id']}: {pos['title']} ({pos['department']})")
    
    print("\nSample persons (first 3):")
    for person in persons[:3]:
        print(f"  {person['id']}: {person['name']}")
        for pos in person['positions']:
            print(f"    - {pos['position_id']}: {pos['start_date']} → {pos['end_date']}")
