"""
Add a test mention to verify the system works
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.storage import StorageManager
from src.core.models import Mention, generate_mention_id
from datetime import datetime
import config

def add_test_mention():
    """Add a test mention for the first person in the database"""
    
    storage = StorageManager(config.BASE_PATH)
    
    # Get first person
    persons = storage.load_persons()
    if not persons:
        print("❌ No persons found. Import data first.")
        return
    
    person = persons[0]
    print(f"Adding test mention for: {person.name} ({person.id})")
    
    # Create test mention
    mention_id = generate_mention_id(person.id, str(datetime.now().date()))
    
    mention = Mention(
        id=mention_id,
        person_id=person.id,
        date=str(datetime.now().date()),
        source="Тестовый источник",
        url="https://example.com/test-article",
        title="Тестовая статья о чиновнике",
        text="Это тестовое упоминание. Здесь должен быть текст статьи или цитата из новостей.",
        tags=["тест", "пример"],
        collection_method="manual",
        collected_by="test_script"
    )
    
    # Save
    storage.save_mention(mention)
    print(f"✅ Test mention added!")
    print(f"   ID: {mention_id}")
    print(f"   File: {mention.get_filename()}")
    
    # Verify
    mentions = storage.load_mentions(person.id)
    print(f"\n📊 Total mentions for {person.name}: {len(mentions)}")

if __name__ == '__main__':
    add_test_mention()
