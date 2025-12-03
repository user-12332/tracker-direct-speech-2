"""
Storage layer for officials tracker
Supports local files and Google Drive with file locking
"""
import json
import os
from pathlib import Path
from typing import List, Optional, Dict
from filelock import FileLock, Timeout
import time

from .models import Position, Person, Mention, PositionAssignment


class StorageManager:
    """Manages data storage with file locking for concurrent access"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.data_path = self.base_path / 'data'
        self.positions_path = self.data_path / 'positions'
        self.persons_path = self.data_path / 'persons'
        self.mentions_path = self.data_path / 'mentions'
        self.locks_path = self.base_path / '.locks'
        
        # Create directories
        self.positions_path.mkdir(parents=True, exist_ok=True)
        self.persons_path.mkdir(parents=True, exist_ok=True)
        self.mentions_path.mkdir(parents=True, exist_ok=True)
        self.locks_path.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.positions_file = self.positions_path / 'positions.json'
        self.persons_file = self.persons_path / 'persons.json'
    
    def _get_lock(self, lock_name: str, timeout: int = 10):
        """Get a file lock"""
        lock_path = self.locks_path / f'{lock_name}.lock'
        return FileLock(str(lock_path), timeout=timeout)
    
    # ==================== POSITIONS ====================
    
    def load_positions(self) -> List[Position]:
        """Load all positions"""
        with self._get_lock('positions'):
            if not self.positions_file.exists():
                return []
            
            with open(self.positions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Position.from_dict(p) for p in data.get('positions', [])]
    
    def save_positions(self, positions: List[Position]):
        """Save all positions"""
        with self._get_lock('positions'):
            data = {'positions': [p.to_dict() for p in positions]}
            with open(self.positions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_position(self, position: Position):
        """Add a new position"""
        positions = self.load_positions()
        positions.append(position)
        self.save_positions(positions)
    
    def get_position(self, position_id: str) -> Optional[Position]:
        """Get a position by ID"""
        positions = self.load_positions()
        for pos in positions:
            if pos.id == position_id:
                return pos
        return None
    
    def update_position(self, position: Position):
        """Update an existing position"""
        positions = self.load_positions()
        for i, pos in enumerate(positions):
            if pos.id == position.id:
                positions[i] = position
                self.save_positions(positions)
                return True
        return False
    
    # ==================== PERSONS ====================
    
    def load_persons(self) -> List[Person]:
        """Load all persons"""
        with self._get_lock('persons'):
            if not self.persons_file.exists():
                return []
            
            with open(self.persons_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Person.from_dict(p) for p in data.get('persons', [])]
    
    def save_persons(self, persons: List[Person]):
        """Save all persons"""
        with self._get_lock('persons'):
            data = {'persons': [p.to_dict() for p in persons]}
            with open(self.persons_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_person(self, person: Person):
        """Add a new person"""
        persons = self.load_persons()
        persons.append(person)
        self.save_persons(persons)
    
    def get_person(self, person_id: str) -> Optional[Person]:
        """Get a person by ID"""
        persons = self.load_persons()
        for person in persons:
            if person.id == person_id:
                return person
        return None
    
    def update_person(self, person: Person):
        """Update an existing person"""
        persons = self.load_persons()
        for i, p in enumerate(persons):
            if p.id == person.id:
                persons[i] = person
                self.save_persons(persons)
                return True
        return False
    
    def get_persons_by_position(self, position_id: str, current_only: bool = False) -> List[Person]:
        """Get all persons who held/hold a specific position"""
        persons = self.load_persons()
        result = []
        for person in persons:
            for pos_assignment in person.positions:
                if pos_assignment.position_id == position_id:
                    if not current_only or pos_assignment.is_current:
                        result.append(person)
                        break
        return result
    
    # ==================== MENTIONS ====================
    
    def _get_person_mentions_dir(self, person_id: str) -> Path:
        """Get the directory for a person's mentions"""
        person_dir = self.mentions_path / person_id
        person_dir.mkdir(exist_ok=True)
        return person_dir
    
    def save_mention(self, mention: Mention):
        """Save a mention"""
        with self._get_lock(f'mentions_{mention.person_id}'):
            person_dir = self._get_person_mentions_dir(mention.person_id)
            filename = mention.get_filename()
            file_path = person_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(mention.to_dict(), f, ensure_ascii=False, indent=2)
    
    def load_mentions(self, person_id: str) -> List[Mention]:
        """Load all mentions for a person"""
        person_dir = self._get_person_mentions_dir(person_id)
        
        if not person_dir.exists():
            return []
        
        mentions = []
        for file_path in person_dir.glob('*.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    mentions.append(Mention.from_dict(data))
            except Exception as e:
                print(f"Warning: Could not load {file_path}: {e}")
        
        # Sort by date (newest first)
        mentions.sort(key=lambda m: m.date if m.date else '', reverse=True)
        return mentions
    
    def get_mention(self, person_id: str, mention_id: str) -> Optional[Mention]:
        """Get a specific mention"""
        mentions = self.load_mentions(person_id)
        for mention in mentions:
            if mention.id == mention_id:
                return mention
        return None
    
    def get_all_mentions(self, limit: Optional[int] = None) -> List[Mention]:
        """Get all mentions across all persons"""
        all_mentions = []
        
        if not self.mentions_path.exists():
            return []
        
        for person_dir in self.mentions_path.iterdir():
            if person_dir.is_dir():
                person_id = person_dir.name
                mentions = self.load_mentions(person_id)
                all_mentions.extend(mentions)
        
        # Sort by date (newest first)
        all_mentions.sort(key=lambda m: m.date if m.date else '', reverse=True)
        
        if limit:
            return all_mentions[:limit]
        return all_mentions
    
    # ==================== UTILITY ====================
    
    def get_next_person_id(self) -> str:
        """Get the next available person ID"""
        persons = self.load_persons()
        if not persons:
            return 'person_001'
        
        # Find max ID
        max_num = 0
        for person in persons:
            if person.id.startswith('person_'):
                try:
                    num = int(person.id.split('_')[1])
                    max_num = max(max_num, num)
                except:
                    pass
        
        return f'person_{str(max_num + 1).zfill(3)}'
    
    def get_next_position_id(self) -> str:
        """Get the next available position ID"""
        positions = self.load_positions()
        if not positions:
            return 'pos_001'
        
        # Find max ID
        max_num = 0
        for pos in positions:
            if pos.id.startswith('pos_'):
                try:
                    num = int(pos.id.split('_')[1])
                    max_num = max(max_num, num)
                except:
                    pass
        
        return f'pos_{str(max_num + 1).zfill(3)}'
    
    def get_stats(self) -> Dict:
        """Get statistics about the data"""
        positions = self.load_positions()
        persons = self.load_persons()
        
        active_positions = sum(1 for p in positions if p.is_active)
        current_officials = sum(1 for p in persons if p.get_current_position() is not None)
        
        total_mentions = 0
        if self.mentions_path.exists():
            for person_dir in self.mentions_path.iterdir():
                if person_dir.is_dir():
                    total_mentions += len(list(person_dir.glob('*.json')))
        
        return {
            'total_positions': len(positions),
            'active_positions': active_positions,
            'total_persons': len(persons),
            'current_officials': current_officials,
            'total_mentions': total_mentions
        }
    
    # ==================== DEPARTMENT MANAGEMENT ====================
    
    def load_departments(self) -> List:
        """Load all departments"""
        from src.core.models import Department
        
        dept_file = self.data_path / 'departments.json'
        if not dept_file.exists():
            return []
        
        with self._get_lock('departments'):
            with open(dept_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Department.from_dict(d) for d in data.get('departments', [])]
    
    def save_departments(self, departments: List):
        """Save all departments"""
        dept_file = self.data_path / 'departments.json'
        dept_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {'departments': [d.to_dict() for d in departments]}
        
        with self._get_lock('departments'):
            with open(dept_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_department(self, name: str):
        """Get department by name"""
        departments = self.load_departments()
        for dept in departments:
            if dept.name == name:
                return dept
        return None
    
    def update_department(self, department):
        """Update a department"""
        departments = self.load_departments()
        for i, d in enumerate(departments):
            if d.name == department.name:
                departments[i] = department
                break
        else:
            departments.append(department)
        
        self.save_departments(departments)
    
    def get_or_create_department(self, name: str, level: str = 'federal'):
        """Get existing department or create new one"""
        from src.core.models import Department
        
        dept = self.get_department(name)
        if dept:
            return dept
        
        # Create new
        departments = self.load_departments()
        dept_id = f"dept_{str(len(departments) + 1).zfill(3)}"
        dept = Department(id=dept_id, name=name, level=level)
        departments.append(dept)
        self.save_departments(departments)
        return dept
    
    # ==================== SUBDEPARTMENT MANAGEMENT ====================
    
    def load_subdepartments(self) -> List:
        """Load all subdepartments"""
        from src.core.models import Subdepartment
        
        subdept_file = self.data_path / 'subdepartments.json'
        if not subdept_file.exists():
            return []
        
        with self._get_lock('subdepartments'):
            with open(subdept_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Subdepartment.from_dict(d) for d in data.get('subdepartments', [])]
    
    def save_subdepartments(self, subdepartments: List):
        """Save all subdepartments"""
        subdept_file = self.data_path / 'subdepartments.json'
        subdept_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = {'subdepartments': [d.to_dict() for d in subdepartments]}
        
        with self._get_lock('subdepartments'):
            with open(subdept_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_subdepartment(self, name: str, department_name: str):
        """Get subdepartment by name and parent department"""
        subdepartments = self.load_subdepartments()
        for subdept in subdepartments:
            if subdept.name == name and subdept.department_name == department_name:
                return subdept
        return None
    
    def update_subdepartment(self, subdepartment):
        """Update a subdepartment"""
        subdepartments = self.load_subdepartments()
        for i, s in enumerate(subdepartments):
            if s.name == subdepartment.name and s.department_name == subdepartment.department_name:
                subdepartments[i] = subdepartment
                break
        else:
            subdepartments.append(subdepartment)
        
        self.save_subdepartments(subdepartments)
    
    def get_or_create_subdepartment(self, name: str, department_name: str):
        """Get existing subdepartment or create new one"""
        from src.core.models import Subdepartment
        
        subdept = self.get_subdepartment(name, department_name)
        if subdept:
            return subdept
        
        # Create new
        subdepartments = self.load_subdepartments()
        subdept_id = f"subdept_{str(len(subdepartments) + 1).zfill(3)}"
        subdept = Subdepartment(id=subdept_id, name=name, department_name=department_name)
        subdepartments.append(subdept)
        self.save_subdepartments(subdepartments)
        return subdept

