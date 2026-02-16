from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from agent.orchestrator import AgentOrchestrator

app = Flask(__name__)
app.config["SECRET_KEY"] = "supersecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

agent = AgentOrchestrator()

# ----------------------
# Database Model
# ----------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
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
    data = request.get_json()
    conversation_id = data.get("conversation_id")
    message = data.get("message")

    reply = agent.handle_message(conversation_id, message)

    return jsonify({"reply": reply})

# ----------------------
# Register
# ----------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        user = User(username=username, password=hashed_pw)
        db.session.add(user)
        db.session.commit()

        flash("Account created! Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")

# ----------------------
# Login
# ----------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials")

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

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)
