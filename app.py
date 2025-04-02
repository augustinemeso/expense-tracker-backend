from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from datetime import timedelta, datetime
from dotenv import load_dotenv
import os
import uuid

from extensions import db
from models import User, Expense

load_dotenv()

def create_app():
    app = Flask(__name__)

    # Set up app configurations
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    bcrypt = Bcrypt(app)
    jwt = JWTManager(app)
    CORS(app)

    # Register user
    @app.route("/register", methods=["POST"])
    def register():
        data = request.json
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")

        if not name or not email or not password:
            return jsonify({"error": "All fields are required"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409

        new_user = User(name=name, email=email)
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            access_token = create_access_token(identity={"id": str(new_user.id), "email": new_user.email})
            return jsonify({"message": "User registered successfully", "token": access_token}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    
    @app.route("/login", methods=["POST"])
    def login():
        data = request.json
        email = data.get("email")
        password = data.get("password")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            access_token = create_access_token(identity=str(new_user.id))  # Use only the 'id' as the subject

            return jsonify({"token": access_token}), 200
        else:
            return jsonify({"message": "Invalid credentials"}), 401

    
    @app.route("/expenses", methods=["POST"])
    @jwt_required()
    def add_expense():
        data = request.json
        user_id = get_jwt_identity()["id"]

        try:
            amount = float(data.get("amount"))
            category = data.get("category")
            description = data.get("description", "")
            date = datetime.strptime(data.get("date"), "%Y-%m-%d").date()

            if not amount or not category or not date:
                return jsonify({"error": "Amount, category, and date are required"}), 400

            new_expense = Expense(
                id=uuid.uuid4(),
                user_id=user_id,
                amount=amount,
                category=category,
                description=description,
                date=date
            )

            db.session.add(new_expense)
            db.session.commit()
            
            return jsonify({"message": "Expense added successfully", "expense": new_expense.to_dict()}), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    
    @app.route("/expenses", methods=["GET"])
    @jwt_required()
    def get_expenses():
        user_id = get_jwt_identity()["id"]
        expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).all()
        return jsonify([expense.to_dict() for expense in expenses]), 200

    return app

if __name__ == '__main__':
    app = create_app()
    if app:
        port = int(os.environ.get("PORT", 5001))
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        print("Error: create_app() returned None")
