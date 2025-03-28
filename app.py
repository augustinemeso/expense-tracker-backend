from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from datetime import timedelta
from dotenv import load_dotenv
import os

# Import extensions
from extensions import db  # Ensure extensions.py correctly initializes `db`

# Load environment variables from .env file
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

    # ✅ Import models to ensure tables are created
    from models import User, Expense  # Imported after db.init_app(app)

    # ✅ Register routes
    @app.route('/register', methods=['POST'])
    def register():
        try:
            data = request.get_json()

            # Ensure required fields are provided
            if not all(key in data for key in ["email", "password"]):
                return jsonify({"error": "Email and password are required"}), 400

            # Check if user already exists
            if User.query.filter_by(email=data['email']).first():
                return jsonify({"error": "User already exists"}), 400

            # Hash the password
            hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

            # Create new user without username
            new_user = User(email=data['email'], password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            return jsonify({"message": "User registered successfully!"}), 201

        except Exception as e:
            return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

    @app.route('/login', methods=['POST'])
    def login():
        try:
            data = request.get_json()
            user = User.query.filter_by(email=data['email']).first()
            if user and bcrypt.check_password_hash(user.password, data['password']):
                access_token = create_access_token(identity=user.id)
                return jsonify({"access_token": access_token}), 200
            return jsonify({"error": "Invalid credentials"}), 401
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/expenses', methods=['POST'])
    @jwt_required()
    def add_expense():
        try:
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
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/expenses', methods=['GET'])
    @jwt_required()
    def get_expenses():
        try:
            user_id = get_jwt_identity()
            expenses = Expense.query.filter_by(user_id=user_id).all()
            return jsonify([
                {"id": e.id, "title": e.title, "amount": e.amount, "category": e.category, "date": e.date}
                for e in expenses
            ])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/expenses/<int:id>', methods=['PUT'])
    @jwt_required()
    def update_expense(id):
        try:
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
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/expenses/<int:id>', methods=['DELETE'])
    @jwt_required()
    def delete_expense(id):
        try:
            user_id = get_jwt_identity()
            expense = Expense.query.filter_by(id=id, user_id=user_id).first()
            if not expense:
                return jsonify({"error": "Expense not found"}), 404
            db.session.delete(expense)
            db.session.commit()
            return jsonify({"message": "Expense deleted successfully!"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app  # ✅ Now the app is returned AFTER configurations

# ✅ Ensure this runs only when executed directly
if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get("PORT", 5001))  
    app.run(debug=True, host='0.0.0.0', port=port)
