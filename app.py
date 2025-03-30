from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from datetime import timedelta
from dotenv import load_dotenv
import os

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

    # ✅ Import models to ensure tables are created
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

    return app  # ✅ Ensure `app` is returned correctly!

# ✅ Run the application
if __name__ == '__main__':
    app = create_app()
    if app:  # ✅ Ensure app is not None before running
        port = int(os.environ.get("PORT", 5001))  
        app.run(debug=True, host='0.0.0.0', port=port)
    else:
        print("Error: create_app() returned None")
