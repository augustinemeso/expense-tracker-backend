from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from datetime import timedelta
from dotenv import load_dotenv
import os
import uuid

# Import extensions
from extensions import db  # Ensure `db` is initialized in `extensions.py`

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)

    # ✅ Configure Flask settings
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')  # Change in production
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

    # ✅ Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    bcrypt = Bcrypt(app)
    jwt = JWTManager(app)
    CORS(app)

    # ✅ Import models
    from models import User, Expense  # Imported after db.init_app(app)

    # ✅ Register routes inside create_app()
    @app.route("/register", methods=["POST"])
    def register():
        data = request.json
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")

        if not name or not email or not password:
            return jsonify({"error": "All fields are required"}), 400

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409

        # Create new user
        new_user = User(name=name, email=email)
        new_user.set_password(password)

        # Save to database
        db.session.add(new_user)
        db.session.commit()

        # Generate JWT token
        access_token = create_access_token(identity={"id": str(new_user.id), "email": new_user.email})

        return jsonify({"message": "User registered successfully", "token": access_token}), 201

    @app.route("/login", methods=["POST"])
    def login():
        data = request.json
        email = data.get("email")
        password = data.get("password")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            access_token = create_access_token(identity={"id": str(user.id), "email": user.email})
            return jsonify({"token": access_token}), 200
        else:
            return jsonify({"message": "Invalid credentials"}), 401

    # ✅ Add Expense Route
    @app.route("/expenses", methods=["POST"])
    @jwt_required()
    def add_expense():
        data = request.json
        user_id = get_jwt_identity()["id"]

        amount = float(data.get("amount")) if data.get("amount") else data.get("amount")
        category = data.get("category")
        description = data.get("description", "")
        date = data.get("date")

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

    # ✅ Get All Expenses Route
    @app.route("/expenses", methods=["GET"])
    @jwt_required()
    def get_expenses():
        user_id = get_jwt_identity()["id"]
        expenses = Expense.query.filter_by(user_id=user_id).order_by(Expense.date.desc()).all()
        return jsonify([expense.to_dict() for expense in expenses]), 200

    # ✅ Update Expense Route
    @app.route("/expenses/<uuid:expense_id>", methods=["PUT"])
    @jwt_required()
    def update_expense(expense_id):
        user_id = get_jwt_identity()["id"]
        expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first()

        if not expense:
            return jsonify({"error": "Expense not found"}), 404

        data = request.json
        expense.amount = data.get("amount", expense.amount)
        expense.category = data.get("category", expense.category)
        expense.description = data.get("description", expense.description)
        expense.date = data.get("date", expense.date)

        db.session.commit()
        return jsonify({"message": "Expense updated successfully", "expense": expense.to_dict()}), 200

    return app  # ✅ Ensure `app` is returned correctly!

# ✅ Run the application
if __name__ == '__main__':
    app = create_app()
    if app:  # ✅ Ensure app is not None before running
        port = int(os.environ.get("PORT", 5001))  
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        print("Error: create_app() returned None")
