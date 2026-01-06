import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from functools import wraps

from admin_data import admin_data_bp
from data_sims import data_sims_bp
from data_pemeriksaan import pemeriksaan_bp
from upload import upload_bp

app = Flask(__name__)

# =====================
# KONFIGURASI
# =====================
app.secret_key = os.getenv("SECRET_KEY", "DEV_SECRET_KEY_LOCALHOST_2026")

# =====================
# USER DATA (HASH SUDAH FIX)
# =====================
USERS = {
    "admin": {
        "password": "scrypt:32768:8:1$K5jRepHKgFbsQpB8$e29dac6806a56083d7d5855a689642a4df52ba448350b5b0526f677b8e81d4398ce05fb83ba2f970b5d5b88796c43079905c851e28494556e76ffb137aabf78a",
        "role": "admin"
    },
    "user": {
        "password": "scrypt:32768:8:1$WDSyYciRPEiKFabp$befc9a65b0d768c0734e86029d5c2f628e5a52268a125c0d1b3b82e37a202d489d6bc594a6bef4ef7f08e906a4f149a7ce75d62de582eca7c599a20a63c204ae",
        "role": "user"
    }
}

# =====================
# LOGIN REQUIRED
# =====================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Silakan login terlebih dahulu", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

# =====================
# LOGIN
# =====================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = USERS.get(username)

        if user and check_password_hash(user["password"], password):
            session["user"] = username
            session["role"] = user["role"]
            return redirect(url_for("home"))

        flash("Username atau password salah", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")

# =====================
# LOGOUT
# =====================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =====================
# HOME
# =====================
@app.route("/")
@login_required
def home():
    return render_template("index.html")

# =====================
# REGISTER BLUEPRINT
# =====================
app.register_blueprint(data_sims_bp)
app.register_blueprint(pemeriksaan_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(admin_data_bp)
