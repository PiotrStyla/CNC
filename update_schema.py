from app import app, db
from models import User, Order

def update_schema():
    with app.app_context():
        # Drop existing tables
        db.drop_all()
        
        # Create tables with the new schema
        db.create_all()
        
        print("Database schema updated successfully.")

if __name__ == "__main__":
    update_schema()
