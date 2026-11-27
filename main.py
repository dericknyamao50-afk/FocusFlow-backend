import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from app.config import settings
from app.database import db
from app.routers.auth import auth_bp

try:
    from flask_jwt_extended import JWTManager
except ImportError:
    JWTManager = None

from app.routers.github import github_bp

try:
    from app.routers.tasks import tasks_bp
except ImportError:
    tasks_bp = None

try:
    from app.routers.projects import projects_bp
except ImportError:
    projects_bp = None

try:
    from app.routers.notes import notes_bp
except ImportError:
    notes_bp = None

try:
    from app.routers.analytics import analytics_bp
except ImportError:
    analytics_bp = None

def create_app() -> Flask:
    app = Flask(__name__)

    frontend_url = (
        (os.environ.get("FRONTEND_URL") or "https://focusflow-8akp.onrender.com")
        .strip()
        .rstrip("/")
    )
    is_https = frontend_url.startswith("https://")

    app.config["SQLALCHEMY_DATABASE_URI"] = getattr(
        settings,
        "SQLALCHEMY_DATABASE_URI",
        os.environ.get("DATABASE_URL", "sqlite:///focusflow.db"),
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = getattr(settings, "JWT_SECRET_KEY", "focusflow-secret")
    app.config["JWT_SECRET_KEY"] = getattr(
        settings, "JWT_SECRET_KEY", app.config["SECRET_KEY"]
    )
    app.config["JWT_ALGORITHM"] = getattr(settings, "JWT_ALGORITHM", "HS256")
    app.config["ACCESS_TOKEN_EXPIRE_MINUTES"] = getattr(
        settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24
    )
    app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]
    app.config["JWT_ACCESS_COOKIE_NAME"] = "token"
    app.config["COOKIE_SECURE"] = is_https
    app.config["COOKIE_SAMESITE"] = "None" if is_https else "Lax"
    app.config["JWT_COOKIE_SECURE"] = is_https
    app.config["JWT_COOKIE_SAMESITE"] = "None" if is_https else "Lax"
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False

    allowed_origins = [
        frontend_url,
        "https://focusflow-8akp.onrender.com",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    CORS(
        app,
        resources={r"/*": {"origins": allowed_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    db.init_app(app)
    JWTManager(app)

    if JWTManager is not None:
        JWTManager(app)

    app.register_blueprint(auth_bp, url_prefix="/api")

    app.register_blueprint(github_bp, url_prefix="/api/github")
    if tasks_bp is not None:
        app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    if projects_bp is not None:
        app.register_blueprint(projects_bp, url_prefix="/api/projects")
    if notes_bp is not None:
        app.register_blueprint(notes_bp, url_prefix="/api/notes")
    if analytics_bp is not None:
        app.register_blueprint(analytics_bp, url_prefix="/api/analytics")

    @app.get("/")
    def index():
        return jsonify({"service": "FocusFlow API", "status": "ok"}), 200

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"}), 200

    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
