from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from datetime import datetime
import uuid
from extensions import db  # Ensure `db` is correctly initialized
from flask_bcrypt import generate_password_hash, check_password_hash


bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Method to hash password
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    # Method to check password
    def check_password(self, password):
        
        return bcrypt.check_password_hash(self.password_hash, password)
    

class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to User
    user = db.relationship("User", backref=db.backref("expenses", lazy=True, cascade="all, delete"))

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "amount": self.amount,
            "category": self.category,
            "description": self.description,
            "date": self.date,
            "created_at": self.created_at
        }