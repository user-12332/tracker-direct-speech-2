"""
Data models for the officials tracker
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, List
from datetime import datetime
import json


@dataclass
class Department:
    """Represents a government department/ministry"""
    id: str
    name: str
    level: str = 'federal'
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    deactivated_at: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class Subdepartment:
    """Represents a subdepartment within a department"""
    id: str
    name: str
    department_name: str  # Parent department name
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    deactivated_at: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class Position:
    """Represents a government position"""
    id: str
    title: str
    department: str
    subdepartment: Optional[str] = None
    level: str = 'federal'
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_active: bool = True
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class PositionAssignment:
    """Represents a person's assignment to a position"""
    position_id: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = True
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class Person:
    """Represents a person (official)"""
    id: str
    name: str
    positions: List[PositionAssignment] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self):
        data = asdict(self)
        data['positions'] = [pos for pos in data['positions']]
        return data
    
    @classmethod
    def from_dict(cls, data):
        positions = [PositionAssignment.from_dict(p) for p in data.get('positions', [])]
        return cls(
            id=data['id'],
            name=data['name'],
            positions=positions,
            created_at=data.get('created_at', datetime.now().isoformat())
        )
    
    def get_current_position(self):
        """Get the current position (if any)"""
        for pos in self.positions:
            if pos.is_current:
                return pos
        return None
    
    def add_position(self, position_id: str, start_date: str, end_date: Optional[str] = None):
        """Add a new position assignment"""
        assignment = PositionAssignment(
            position_id=position_id,
            start_date=start_date,
            end_date=end_date,
            is_current=(end_date is None)
        )
        self.positions.append(assignment)


@dataclass
class Mention:
    """Represents a media mention or direct speech"""
    id: str
    person_id: str
    date: str
    source: str
    url: Optional[str] = None
    title: Optional[str] = None
    text: str = ''
    tags: List[str] = field(default_factory=list)
    collection_method: str = 'manual'
    collected_by: str = 'user'
    collected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    approved: bool = True
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)
    
    def get_filename(self):
        """Generate filename for this mention"""
        # Format: YYYY-MM-DD_source_id.json
        date_part = self.date.replace('-', '')[:8] if self.date else 'nodate'
        source_part = self.source.replace(' ', '_')[:20].lower()
        return f"{date_part}_{source_part}_{self.id}.json"


def generate_mention_id(person_id: str, date: str) -> str:
    """Generate a unique mention ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"mention_{person_id}_{timestamp}"


def generate_person_id(counter: int) -> str:
    """Generate a person ID"""
    return f"person_{str(counter).zfill(3)}"


def generate_position_id(counter: int) -> str:
    """Generate a position ID"""
    return f"pos_{str(counter).zfill(3)}"
