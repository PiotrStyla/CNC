import os
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get("FLASK_SECRET_KEY") or "a secret key"
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

with app.app_context():
    import models
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))

@app.after_request
def add_header(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net 'unsafe-inline'; style-src 'self' https://cdn.replit.com https://cdn.jsdelivr.net 'unsafe-inline'; img-src 'self' data:; font-src 'self' https://cdn.jsdelivr.net;"
    return response

from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
