"""
MongoDB database configuration and setup for Mergington High School API
"""

from argon2 import PasswordHasher

# In-memory storage for development/testing when MongoDB is not available
_activities_store = {}
_teachers_store = {}

# Mock collection classes for API compatibility
class MockCollection:
    def __init__(self, store):
        self.store = store
    
    def find(self, query=None):
        if query is None:
            query = {}
        
        results = []
        for doc_id, doc in self.store.items():
            doc_copy = doc.copy()
            doc_copy['_id'] = doc_id
            
            # Apply query filters
            if self._matches_query(doc_copy, query):
                results.append(doc_copy)
        
        return results
    
    def find_one(self, query):
        for doc_id, doc in self.store.items():
            doc_copy = doc.copy()
            doc_copy['_id'] = doc_id
            
            if self._matches_query(doc_copy, query):
                return doc_copy
        return None
    
    def insert_one(self, doc):
        doc_id = doc.pop('_id')
        self.store[doc_id] = doc
        return type('Result', (), {'inserted_id': doc_id})()
    
    def update_one(self, query, update):
        for doc_id, doc in self.store.items():
            doc_copy = doc.copy()
            doc_copy['_id'] = doc_id
            
            if self._matches_query(doc_copy, query):
                if '$push' in update:
                    for field, value in update['$push'].items():
                        if field not in doc:
                            doc[field] = []
                        doc[field].append(value)
                if '$pull' in update:
                    for field, value in update['$pull'].items():
                        if field in doc and value in doc[field]:
                            doc[field].remove(value)
                return type('Result', (), {'modified_count': 1})()
        return type('Result', (), {'modified_count': 0})()
    
    def count_documents(self, query):
        count = 0
        for doc_id, doc in self.store.items():
            doc_copy = doc.copy()
            doc_copy['_id'] = doc_id
            if self._matches_query(doc_copy, query):
                count += 1
        return count
    
    def aggregate(self, pipeline):
        # Simple implementation for the days aggregation
        if len(pipeline) >= 2 and pipeline[0].get('$unwind') == '$schedule_details.days':
            days = set()
            for doc in self.store.values():
                if 'schedule_details' in doc and 'days' in doc['schedule_details']:
                    for day in doc['schedule_details']['days']:
                        days.add(day)
            return [{'_id': day} for day in sorted(days)]
        return []
    
    def _matches_query(self, doc, query):
        for field, condition in query.items():
            if field == '_id':
                if doc.get('_id') != condition:
                    return False
            elif field == 'schedule_details.days':
                if '$in' in condition:
                    doc_days = doc.get('schedule_details', {}).get('days', [])
                    if not any(day in doc_days for day in condition['$in']):
                        return False
            elif field == 'schedule_details.start_time':
                if '$gte' in condition:
                    doc_time = doc.get('schedule_details', {}).get('start_time')
                    if not doc_time or doc_time < condition['$gte']:
                        return False
            elif field == 'schedule_details.end_time':
                if '$lte' in condition:
                    doc_time = doc.get('schedule_details', {}).get('end_time')
                    if not doc_time or doc_time > condition['$lte']:
                        return False
            elif field == 'difficulty':
                if '$exists' in condition:
                    if condition['$exists'] and 'difficulty' not in doc:
                        return False
                    if not condition['$exists'] and 'difficulty' in doc:
                        return False
                elif doc.get('difficulty') != condition:
                    return False
            elif doc.get(field) != condition:
                return False
        return True

# Initialize collections
activities_collection = MockCollection(_activities_store)
teachers_collection = MockCollection(_teachers_store)

# Methods
def hash_password(password):
    """Hash password using Argon2"""
    ph = PasswordHasher()
    return ph.hash(password)

def init_database():
    """Initialize database if empty"""

    # Initialize activities if empty
    if activities_collection.count_documents({}) == 0:
        for name, details in initial_activities.items():
            activities_collection.insert_one({"_id": name, **details})
            
    # Initialize teacher accounts if empty
    if teachers_collection.count_documents({}) == 0:
        for teacher in initial_teachers:
            teachers_collection.insert_one({"_id": teacher["username"], **teacher})

# Initial database if empty
initial_activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Mondays and Fridays, 3:15 PM - 4:45 PM",
        "schedule_details": {
            "days": ["Monday", "Friday"],
            "start_time": "15:15",
            "end_time": "16:45"
        },
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 7:00 AM - 8:00 AM",
        "schedule_details": {
            "days": ["Tuesday", "Thursday"],
            "start_time": "07:00",
            "end_time": "08:00"
        },
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
        "difficulty": "Beginner"
    },
    "Morning Fitness": {
        "description": "Early morning physical training and exercises",
        "schedule": "Mondays, Wednesdays, Fridays, 6:30 AM - 7:45 AM",
        "schedule_details": {
            "days": ["Monday", "Wednesday", "Friday"],
            "start_time": "06:30",
            "end_time": "07:45"
        },
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 5:30 PM",
        "schedule_details": {
            "days": ["Tuesday", "Thursday"],
            "start_time": "15:30",
            "end_time": "17:30"
        },
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and compete in basketball tournaments",
        "schedule": "Wednesdays and Fridays, 3:15 PM - 5:00 PM",
        "schedule_details": {
            "days": ["Wednesday", "Friday"],
            "start_time": "15:15",
            "end_time": "17:00"
        },
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore various art techniques and create masterpieces",
        "schedule": "Thursdays, 3:15 PM - 5:00 PM",
        "schedule_details": {
            "days": ["Thursday"],
            "start_time": "15:15",
            "end_time": "17:00"
        },
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 3:30 PM - 5:30 PM",
        "schedule_details": {
            "days": ["Monday", "Wednesday"],
            "start_time": "15:30",
            "end_time": "17:30"
        },
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and prepare for math competitions",
        "schedule": "Tuesdays, 7:15 AM - 8:00 AM",
        "schedule_details": {
            "days": ["Tuesday"],
            "start_time": "07:15",
            "end_time": "08:00"
        },
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
        "difficulty": "Intermediate"
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 3:30 PM - 5:30 PM",
        "schedule_details": {
            "days": ["Friday"],
            "start_time": "15:30",
            "end_time": "17:30"
        },
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "amelia@mergington.edu"]
    },
    "Weekend Robotics Workshop": {
        "description": "Build and program robots in our state-of-the-art workshop",
        "schedule": "Saturdays, 10:00 AM - 2:00 PM",
        "schedule_details": {
            "days": ["Saturday"],
            "start_time": "10:00",
            "end_time": "14:00"
        },
        "max_participants": 15,
        "participants": ["ethan@mergington.edu", "oliver@mergington.edu"],
        "difficulty": "Advanced"
    },
    "Science Olympiad": {
        "description": "Weekend science competition preparation for regional and state events",
        "schedule": "Saturdays, 1:00 PM - 4:00 PM",
        "schedule_details": {
            "days": ["Saturday"],
            "start_time": "13:00",
            "end_time": "16:00"
        },
        "max_participants": 18,
        "participants": ["isabella@mergington.edu", "lucas@mergington.edu"],
        "difficulty": "Advanced"
    },
    "Sunday Chess Tournament": {
        "description": "Weekly tournament for serious chess players with rankings",
        "schedule": "Sundays, 2:00 PM - 5:00 PM",
        "schedule_details": {
            "days": ["Sunday"],
            "start_time": "14:00",
            "end_time": "17:00"
        },
        "max_participants": 16,
        "participants": ["william@mergington.edu", "jacob@mergington.edu"],
        "difficulty": "Intermediate"
    },
    "Manga Maniacs": {
        "description": "Explore the fantastic stories of the most interesting characters from Japanese Manga (graphic novels).",
        "schedule": "Tuesdays, 7:00 PM - 8:00 PM",
        "schedule_details": {
            "days": ["Tuesday"],
            "start_time": "19:00",
            "end_time": "20:00"
        },
        "max_participants": 15,
        "participants": []
    }
}

initial_teachers = [
    {
        "username": "mrodriguez",
        "display_name": "Ms. Rodriguez",
        "password": hash_password("art123"),
        "role": "teacher"
     },
    {
        "username": "mchen",
        "display_name": "Mr. Chen",
        "password": hash_password("chess456"),
        "role": "teacher"
    },
    {
        "username": "principal",
        "display_name": "Principal Martinez",
        "password": hash_password("admin789"),
        "role": "admin"
    }
]

