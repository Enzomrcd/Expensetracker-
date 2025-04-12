import os
import logging
import uuid
from flask import Flask
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "expense-tracker-secret-key")

# Get environment variables for Google OAuth
has_google_oauth = os.environ.get("GOOGLE_OAUTH_CLIENT_ID") and os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")

# Create a Mock DB for development
class MockDB:
    def __init__(self):
        self.collections = {}
        logging.warning("Using MockDB - this is only for development")
    
    def collection(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name)
        return self.collections[name]

class MockCollection:
    def __init__(self, name):
        self.name = name
        self.documents = {}
    
    def document(self, doc_id):
        if doc_id not in self.documents:
            self.documents[doc_id] = MockDocument(doc_id)
        return self.documents[doc_id]
    
    def where(self, field, op, value):
        # No need to implement actual filtering for the demo
        # Just return self to allow chaining
        return self
    
    def order_by(self, field, direction='asc'):
        return self
    
    def limit(self, limit_value):
        return self
    
    def stream(self):
        # Return only documents that exist
        return [doc for doc in self.documents.values() if doc.exists]
    
    def add(self, data):
        doc_id = str(uuid.uuid4())
        doc = self.document(doc_id)
        doc.set(data)
        return doc

class MockDocument:
    def __init__(self, id):
        self.id = id
        self._data = {}
        self.exists = False
    
    def get(self):
        return self
    
    def set(self, data):
        self._data = data
        self.exists = True
        return True
    
    def update(self, data):
        self._data.update(data)
        return True
    
    def delete(self):
        self._data = {}
        self.exists = False
        return True
    
    def to_dict(self):
        return self._data

# Set up database
db = MockDB()
logging.warning("Using mock database for development. Data will be stored in memory only.")

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "index"

from models import User

@login_manager.user_loader
def load_user(user_id):
    # Check if user_id is the demo user
    from flask import session
    if user_id == "demo-user-id" and session.get('is_demo'):
        logging.info("Loading demo user for development (user_id: %s)", user_id)
        user = User(
            uid="demo-user-id",
            email="demo@example.com", 
            display_name="Demo User"
        )
        return user
    
    # Regular user flow
    if db:
        try:
            user_doc = db.collection('users').document(user_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                user = User(
                    uid=user_id,
                    email=user_data.get('email', ''),
                    display_name=user_data.get('displayName', '')
                )
                return user
        except Exception as e:
            logging.error(f"Error loading user: {e}")
    return None

# Email User Authentication Helper Functions
def get_user_by_email(email):
    """Get a user by email from the database"""
    users_collection = db.collection('users')
    # Since we can't query by field in our mock DB, we need to iterate
    for user_doc in users_collection.stream():
        user_data = user_doc.to_dict()
        if user_data.get('email') == email:
            user_data['id'] = user_doc.id
            return user_data
    return None

def create_user(email, password, display_name=None):
    """Create a new user in the database"""
    # Generate a unique ID for the user
    uid = f"email-user-{email.replace('@', '-').replace('.', '-')}"
    
    # Use the name part of the email if no display name provided
    if not display_name:
        display_name = email.split('@')[0]
    
    # Hash the password for security
    password_hash = generate_password_hash(password)
    
    # Store the user in the database
    db.collection('users').document(uid).set({
        'email': email,
        'displayName': display_name,
        'passwordHash': password_hash,
        'createdAt': None  # In a real app, use a proper datetime
    })
    
    return uid

def verify_password(stored_hash, password):
    """Verify a password against its hash"""
    return check_password_hash(stored_hash, password)

# Import Google OAuth Blueprint if credentials are available
if has_google_oauth:
    try:
        from google_auth import google_auth
        app.register_blueprint(google_auth)
        logging.info("Google OAuth blueprint registered")
    except Exception as e:
        logging.error(f"Error registering Google OAuth blueprint: {e}")

# Import routes after initializing app and login_manager to avoid circular imports
from routes import *
