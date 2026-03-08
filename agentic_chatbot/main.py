# main.py
import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin,
    login_user, login_required,
    logout_user, current_user
)
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import IntegrityError

from llm.client import LLMClient
from agent.orchestrator import AgentOrchestrator
#from agent.scheduler import start_scheduler  # make sure this exists
from engine.scheduler import start_scheduler
from models.db import db
from engine.worker import worker_loop
import threading


# ----------------------
# App Config
# ----------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "supersecretkey")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///users.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
start_scheduler(app)

db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# LLM + Agent
llm_client = LLMClient()
agent = AgentOrchestrator(llm_client)


# ----------------------
# Database Model
# ----------------------
class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    # Legacy warning is fine for now; can be upgraded later to db.session.get(User, id)
    return User.query.get(int(user_id))


# ----------------------
# Routes
# ----------------------
@app.route("/")
@login_required
def home():
    return render_template("index.html", username=current_user.username)


@app.route("/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json(silent=True) or {}
    conversation_id = data.get("conversation_id") or str(current_user.id) or "default"
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({"type": "error", "reply": "Message cannot be empty."}), 400

    try:
        result = agent.handle_message(conversation_id, message)

        # If agent returns plain string
        if isinstance(result, str):
            return jsonify({"type": "message", "reply": result})

        # If agent returns dict (structured)
        if isinstance(result, dict):
            result.setdefault("type", "message")
            result.setdefault("reply", "")
            return jsonify(result)

        return jsonify({"type": "error", "reply": "Invalid agent response type."}), 500

    except Exception as e:
        return jsonify({"type": "error", "reply": f"Agent crashed: {e}"}), 500


# ----------------------
# Register
# ----------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()

        if not username or not password:
            flash("Username and password are required.")
            return redirect(url_for("register"))

        # Pre-check to avoid IntegrityError where possible
        if User.query.filter_by(username=username).first():
            flash("Username already exists. Try another one.")
            return redirect(url_for("register"))

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(username=username, password=hashed_pw)

        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Username already exists. Try another one.")
            return redirect(url_for("register"))

        flash("Account created! Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")


# ----------------------
# Login
# ----------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_url = request.args.get("next")
            return redirect(next_url or url_for("home"))

        flash("Invalid credentials")
        return redirect(url_for("login"))

    return render_template("login.html")


# ----------------------
# Logout
# ----------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# ----------------------
# Boot
# ----------------------
if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    # Start worker thread
    threading.Thread(
        target=worker_loop,
        args=(app,),
        daemon=True
    ).start()

    app.run(debug=True, use_reloader=False, port=8000)