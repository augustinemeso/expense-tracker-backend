from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import datetime
import os

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/expense_tracker_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this in production
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret'  # Change this in production

# Initialize Extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Expense Model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], email=data['email'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully!"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify({"access_token": access_token}), 200
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/expenses', methods=['POST'])
@jwt_required()
def add_expense():
    user_id = get_jwt_identity()
    data = request.get_json()
    new_expense = Expense(
        title=data['title'],
        amount=data['amount'],
        category=data['category'],
        user_id=user_id
    )
    db.session.add(new_expense)
    db.session.commit()
    return jsonify({"message": "Expense added successfully!"}), 201

@app.route('/expenses', methods=['GET'])
@jwt_required()
def get_expenses():
    user_id = get_jwt_identity()
    expenses = Expense.query.filter_by(user_id=user_id).all()
    return jsonify([{"id": e.id, "title": e.title, "amount": e.amount, "category": e.category, "date": e.date} for e in expenses])

@app.route('/expenses/<int:id>', methods=['PUT'])
@jwt_required()
def update_expense(id):
    user_id = get_jwt_identity()
    expense = Expense.query.filter_by(id=id, user_id=user_id).first()
    if not expense:
        return jsonify({"error": "Expense not found"}), 404
    data = request.get_json()
    expense.title = data.get('title', expense.title)
    expense.amount = data.get('amount', expense.amount)
    expense.category = data.get('category', expense.category)
    db.session.commit()
    return jsonify({"message": "Expense updated successfully!"})

@app.route('/expenses/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_expense(id):
    user_id = get_jwt_identity()
    expense = Expense.query.filter_by(id=id, user_id=user_id).first()
    if not expense:
        return jsonify({"error": "Expense not found"}), 404
    db.session.delete(expense)
    db.session.commit()
    return jsonify({"message": "Expense deleted successfully!"})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created
    app.run(debug=True)
