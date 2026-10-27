import os
from datetime import datetime
from urllib.parse import urlparse

from flask import (
    Flask, request, redirect, url_for, render_template_string,
    session, flash, abort
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-this-secret-key")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Render PostgreSQL: set DATABASE_URL in Environment.
# Local fallback: SQLite. For persistent production data, use PostgreSQL.
database_url = os.environ.get("DATABASE_URL", "sqlite:///teacherkit.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("RENDER", "") == "true"

db = SQLAlchemy(app)
csrf = CSRFProtect(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    lessons = db.relationship("LessonPlan", backref="owner", cascade="all, delete-orphan", lazy=True)


class LessonPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    subject = db.Column(db.String(120), nullable=False)
    grade = db.Column(db.String(80), nullable=False)
    topic = db.Column(db.String(180), nullable=False)
    duration = db.Column(db.String(40), nullable=False, default="50 เธเธฒเธ—เธต")
    objectives = db.Column(db.Text, nullable=False, default="")
    activities = db.Column(db.Text, nullable=False, default="")
    materials = db.Column(db.Text, nullable=False, default="")
    assessment = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


BASE_STYLE = r"""
:root{--navy:#172554;--blue:#3157d5;--pale:#eaf0ff;--ink:#202943;--muted:#68738c;--line:#e5e9f2;--bg:#f5f7fc;--green:#13845b;--red:#b42318}
*{box-sizing:border-box}body{margin:0;font-family:Tahoma,"Noto Sans Thai",sans-serif;background:var(--bg);color:var(--ink)}
header{background:linear-gradient(120deg,#172554,#3157d5);color:white;padding:22px max(20px,calc((100% - 1120px)/2));display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:11px}.logo{width:42px;height:42px;border-radius:13px;background:white;color:var(--blue);display:grid;place-items:center;font-weight:bold;font-size:23px}.brand h1{font-size:23px;margin:0}.brand p{font-size:12px;color:#dce5ff;margin:4px 0 0}
nav{display:flex;align-items:center;gap:8px;flex-wrap:wrap}nav a{color:white;text-decoration:none;padding:9px 12px;border-radius:9px;background:#ffffff1b;font-size:14px}
main{max-width:1120px;margin:28px auto;padding:0 20px 40px}.welcome{display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap;margin-bottom:20px}.welcome h2{margin:0 0 6px;font-size:26px}.welcome p,.muted{color:var(--muted);margin:0;line-height:1.6}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:15px}.layout{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.card,.stat{background:white;border:1px solid var(--line);border-radius:16px;padding:21px;box-shadow:0 4px 16px #1d2c5309}.stat .label{font-size:13px;color:var(--muted)}.stat .num{font-size:28px;font-weight:bold;margin-top:7px}
h3{margin:0 0 7px;font-size:19px}.sub{font-size:13px;color:var(--muted);margin:0 0 18px}
.field{margin-bottom:14px}label{display:block;font-size:14px;font-weight:bold;margin-bottom:7px}input,select,textarea{width:100%;font:inherit;padding:11px 12px;border:1px solid #d8deeb;border-radius:9px;background:white;color:var(--ink)}textarea{min-height:85px;resize:vertical}input:focus,textarea:focus,select:focus{outline:2px solid #3157d52b;border-color:var(--blue)}
button,.btn{display:inline-block;border:0;border-radius:9px;padding:11px 15px;font:inherit;font-weight:bold;cursor:pointer;text-decoration:none}.primary{background:var(--blue);color:white}.secondary{background:var(--pale);color:var(--blue)}.danger{background:#fff0f0;color:var(--red)}.actions{display:flex;gap:9px;flex-wrap:wrap;align-items:center}
.auth-wrap{max-width:480px;margin:35px auto}.auth-wrap .card{padding:28px}.auth-wrap h2{margin-top:0}.switch{text-align:center;margin-top:17px;color:var(--muted)}.switch a{color:var(--blue);font-weight:bold}
.flash{padding:12px 14px;border-radius:10px;margin-bottom:15px;background:#effaf5;color:#176747;border:1px solid #c9efdd}.flash.error{background:#fff2f0;color:#9f241b;border-color:#ffd7d1}
.lesson{border:1px solid var(--line);border-radius:12px;padding:16px;margin-top:12px;background:white}.lesson h4{margin:0 0 6px;font-size:17px}.lesson small{color:var(--muted)}.lesson p{white-space:pre-line;line-height:1.7}.tag{background:var(--pale);color:var(--blue);padding:4px 9px;border-radius:20px;font-size:12px}
.empty{text-align:center;padding:25px 10px;color:var(--muted)}footer{text-align:center;color:var(--muted);font-size:12px;padding:20px}
@media(max-width:760px){.grid,.layout{grid-template-columns:1fr}.welcome h2{font-size:22px}main{padding:0 13px 30px}.card{padding:17px}}
"""

HEADER = r"""
<header>
  <div class="brand"><div class="logo">T</div><div><h1>TeacherKit</h1><p>Smart Teaching Assistant ยท เธเธนเนเธเนเธงเธขเน€เธ•เธฃเธตเธขเธกเธเธฒเธฃเธชเธญเธ</p></div></div>
  <nav>
  {% if current_user %}
    <a href="{{ url_for('dashboard') }}">เธซเธเนเธฒเธซเธฅเธฑเธ</a>
    <a href="{{ url_for('new_plan') }}">เธชเธฃเนเธฒเธเนเธเธเธเธฒเธฃเธชเธญเธ</a>
    <a href="{{ url_for('logout') }}">เธญเธญเธเธเธฒเธเธฃเธฐเธเธ</a>
  {% else %}
    <a href="{{ url_for('login') }}">เน€เธเนเธฒเธชเธนเนเธฃเธฐเธเธ</a>
    <a href="{{ url_for('register') }}">เธชเธกเธฑเธเธฃเธชเธกเธฒเธเธดเธ</a>
  {% endif %}
  </nav>
</header>
"""

def render_page(title, body, **context):
    template = """<!doctype html><html lang="th"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{{ title }} | TeacherKit</title><style>""" + BASE_STYLE + """</style></head><body>""" + HEADER + """
    <main>
      {% with messages = get_flashed_messages(with_categories=true) %}
        {% for category, message in messages %}<div class="flash {{ 'error' if category == 'error' else '' }}">{{ message }}</div>{% endfor %}
      {% endwith %}
      """ + body + """
    </main><footer>TeacherKit ยท เธงเธฒเธเนเธเธเธเธฒเธฃเธชเธญเธเธญเธขเนเธฒเธเน€เธเนเธเธฃเธฐเธเธ</footer></body></html>"""
    return render_template_string(template, title=title, current_user=get_current_user(), **context)

def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)

def login_required(view):
    from functools import wraps
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not get_current_user():
            flash("เธเธฃเธธเธ“เธฒเน€เธเนเธฒเธชเธนเนเธฃเธฐเธเธเธเนเธญเธเนเธเนเธเธฒเธ", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

@app.route("/")
def index():
    if get_current_user():
        return redirect(url_for("dashboard"))
    body = r"""
    <section class="welcome"><div><h2>เน€เธ•เธฃเธตเธขเธกเธเธฒเธฃเธชเธญเธเนเธซเนเธเนเธฒเธขเธเธถเนเธเนเธเธ—เธตเนเน€เธ”เธตเธขเธง ๐“</h2>
    <p class="muted">เธชเธฃเนเธฒเธเนเธเธเธเธฒเธฃเธชเธญเธ เธเธฑเธ”เธเธดเธเธเธฃเธฃเธก เธงเธฒเธเนเธเธเธชเธทเนเธญ เนเธฅเธฐเธเธฑเธเธ—เธถเธเธเนเธญเธกเธนเธฅเนเธขเธเธ•เธฒเธกเธเธฑเธเธเธตเธเธนเนเนเธเน</p></div></section>
    <div class="grid">
      <div class="card"><h3>๐“ เนเธเธเธเธฒเธฃเธชเธญเธ</h3><p class="muted">เธเธฑเธเธ—เธถเธเธงเธดเธเธฒ เธฃเธฐเธ”เธฑเธเธเธฑเนเธ เธซเธฑเธงเธเนเธญ เนเธฅเธฐเธเธธเธ”เธเธฃเธฐเธชเธเธเนเธเธฒเธฃเน€เธฃเธตเธขเธเธฃเธนเน</p></div>
      <div class="card"><h3>๐ฏ เธเธดเธเธเธฃเธฃเธกเธเธฒเธฃเน€เธฃเธตเธขเธเธฃเธนเน</h3><p class="muted">เธงเธฒเธเธเธฑเนเธเธเธณเน€เธเนเธฒเธชเธนเนเธเธ—เน€เธฃเธตเธขเธ เธเธฑเนเธเธชเธญเธ เนเธฅเธฐเธเธฑเนเธเธชเธฃเธธเธ</p></div>
      <div class="card"><h3>๐” เธเธฑเธเธเธตเธชเนเธงเธเธ•เธฑเธง</h3><p class="muted">เธชเธกเธฑเธเธฃเธชเธกเธฒเธเธดเธเนเธฅเธฐเน€เธเนเธฒเธชเธนเนเธฃเธฐเธเธ เน€เธเธทเนเธญเธ”เธนเนเธเธเธเธญเธเธเธฑเธเธเธตเธ•เธฑเธงเน€เธญเธ</p></div>
    </div>
    <div class="card" style="margin-top:18px"><h3>เน€เธฃเธดเนเธกเธ•เนเธเนเธเนเธเธฒเธ TeacherKit</h3><p class="muted">เธชเธฃเนเธฒเธเธเธฑเธเธเธตเน€เธเธทเนเธญเธเธฑเธเธ—เธถเธเนเธฅเธฐเธเธฅเธฑเธเธกเธฒเธ”เธนเนเธเธเธเธฒเธฃเธชเธญเธเนเธ”เนเนเธเธ เธฒเธขเธซเธฅเธฑเธ</p>
    <div class="actions" style="margin-top:16px"><a class="btn primary" href="{{ url_for('register') }}">เธชเธกเธฑเธเธฃเธชเธกเธฒเธเธดเธเธเธฃเธต</a><a class="btn secondary" href="{{ url_for('login') }}">เธกเธตเธเธฑเธเธเธตเนเธฅเนเธง ยท เน€เธเนเธฒเธชเธนเนเธฃเธฐเธเธ</a></div></div>
    """
    return render_page("เธซเธเนเธฒเธซเธฅเธฑเธ", body)

@app.route("/register", methods=["GET", "POST"])
def register():
    if get_current_user():
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if not name or len(name) > 80:
            flash("เธเธฃเธธเธ“เธฒเธเธฃเธญเธเธเธทเนเธญเนเธกเนเน€เธเธดเธ 80 เธ•เธฑเธงเธญเธฑเธเธฉเธฃ", "error")
        elif not email or "@" not in email or len(email) > 160:
            flash("เธเธฃเธธเธ“เธฒเธเธฃเธญเธเธญเธตเน€เธกเธฅเนเธซเนเธ–เธนเธเธ•เนเธญเธ", "error")
        elif len(password) < 8:
            flash("เธฃเธซเธฑเธชเธเนเธฒเธเธ•เนเธญเธเธกเธตเธญเธขเนเธฒเธเธเนเธญเธข 8 เธ•เธฑเธงเธญเธฑเธเธฉเธฃ", "error")
        elif password != confirm:
            flash("เธฃเธซเธฑเธชเธเนเธฒเธเธ—เธฑเนเธเธชเธญเธเธเนเธญเธเนเธกเนเธ•เธฃเธเธเธฑเธ", "error")
        elif User.query.filter_by(email=email).first():
            flash("เธญเธตเน€เธกเธฅเธเธตเนเธกเธตเธเธฑเธเธเธตเนเธฅเนเธง เธเธฃเธธเธ“เธฒเน€เธเนเธฒเธชเธนเนเธฃเธฐเธเธ", "error")
        else:
            user = User(name=name, email=email, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            session.clear()
            session["user_id"] = user.id
            flash("เธชเธกเธฑเธเธฃเธชเธกเธฒเธเธดเธเธชเธณเน€เธฃเนเธ เธขเธดเธเธ”เธตเธ•เนเธญเธเธฃเธฑเธเธชเธนเน TeacherKit")
            return redirect(url_for("dashboard"))
    body = r"""
    <div class="auth-wrap"><div class="card"><h2>เธชเธฃเนเธฒเธเธเธฑเธเธเธต TeacherKit</h2><p class="sub">เธชเธกเธฑเธเธฃเธชเธกเธฒเธเธดเธเน€เธเธทเนเธญเธเธฑเธเธ—เธถเธเนเธเธเธเธฒเธฃเธชเธญเธเธเธญเธเธเธธเธ“</p>
    <form method="post">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <div class="field"><label>เธเธทเนเธญเธ—เธตเนเนเธเนเนเธชเธ”เธ</label><input name="name" required maxlength="80" autocomplete="name" value="{{ request.form.get('name','') }}"></div>
      <div class="field"><label>เธญเธตเน€เธกเธฅ</label><input type="email" name="email" required maxlength="160" autocomplete="email" value="{{ request.form.get('email','') }}"></div>
      <div class="field"><label>เธฃเธซเธฑเธชเธเนเธฒเธ (เธญเธขเนเธฒเธเธเนเธญเธข 8 เธ•เธฑเธงเธญเธฑเธเธฉเธฃ)</label><input type="password" name="password" required minlength="8" autocomplete="new-password"></div>
      <div class="field"><label>เธขเธทเธเธขเธฑเธเธฃเธซเธฑเธชเธเนเธฒเธ</label><input type="password" name="confirm" required minlength="8" autocomplete="new-password"></div>
      <button class="primary" type="submit" style="width:100%">เธชเธกเธฑเธเธฃเธชเธกเธฒเธเธดเธ</button>
    </form><div class="switch">เธกเธตเธเธฑเธเธเธตเนเธฅเนเธง? <a href="{{ url_for('login') }}">เน€เธเนเธฒเธชเธนเนเธฃเธฐเธเธ</a></div></div></div>
    """
    return render_page("เธชเธกเธฑเธเธฃเธชเธกเธฒเธเธดเธ", body)

@app.route("/login", methods=["GET", "POST"])
def login():
    if get_current_user():
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session["user_id"] = user.id
            flash("เน€เธเนเธฒเธชเธนเนเธฃเธฐเธเธเธชเธณเน€เธฃเนเธ")
            return redirect(url_for("dashboard"))
        flash("เธญเธตเน€เธกเธฅเธซเธฃเธทเธญเธฃเธซเธฑเธชเธเนเธฒเธเนเธกเนเธ–เธนเธเธ•เนเธญเธ", "error")
    body = r"""
    <div class="auth-wrap"><div class="card"><h2>เน€เธเนเธฒเธชเธนเนเธฃเธฐเธเธ</h2><p class="sub">เน€เธเนเธฒเธชเธนเนเธเธฑเธเธเธตเน€เธเธทเนเธญเธเธฑเธ”เธเธฒเธฃเนเธเธเธเธฒเธฃเธชเธญเธเธเธญเธเธเธธเธ“</p>
    <form method="post">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <div class="field"><label>เธญเธตเน€เธกเธฅ</label><input type="email" name="email" required autocomplete="email" value="{{ request.form.get('email','') }}"></div>
      <div class="field"><label>เธฃเธซเธฑเธชเธเนเธฒเธ</label><input type="password" name="password" required autocomplete="current-password"></div>
      <button class="primary" type="submit" style="width:100%">เน€เธเนเธฒเธชเธนเนเธฃเธฐเธเธ</button>
    </form><div class="switch">เธขเธฑเธเนเธกเนเธกเธตเธเธฑเธเธเธต? <a href="{{ url_for('register') }}">เธชเธกเธฑเธเธฃเธชเธกเธฒเธเธดเธ</a></div></div></div>
    """
    return render_page("เน€เธเนเธฒเธชเธนเนเธฃเธฐเธเธ", body)

@app.route("/logout")
def logout():
    session.clear()
    flash("เธญเธญเธเธเธฒเธเธฃเธฐเธเธเนเธฅเนเธง")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    plans = LessonPlan.query.filter_by(user_id=user.id).order_by(LessonPlan.created_at.desc()).all()
    body = r"""
    <section class="welcome"><div><h2>เธชเธงเธฑเธชเธ”เธต {{ current_user.name }} ๐‘</h2><p class="muted">เธเธทเนเธเธ—เธตเนเธเธฑเธ”เธเธฒเธฃเธเธฒเธฃเน€เธ•เธฃเธตเธขเธกเธเธฒเธฃเธชเธญเธเธเธญเธเธเธธเธ“</p></div>
    <a class="btn primary" href="{{ url_for('new_plan') }}">+ เธชเธฃเนเธฒเธเนเธเธเธเธฒเธฃเธชเธญเธ</a></section>
    <div class="grid" style="margin-bottom:20px">
      <div class="stat"><div class="label">เนเธเธเธเธฒเธฃเธชเธญเธเธ—เธฑเนเธเธซเธกเธ”</div><div class="num">{{ plans|length }}</div></div>
      <div class="stat"><div class="label">เธเธฑเธเธเธตเธเธนเนเนเธเน</div><div class="num" style="font-size:20px">เธขเธทเธเธขเธฑเธเธ”เนเธงเธขเธญเธตเน€เธกเธฅ</div></div>
      <div class="stat"><div class="label">เธเนเธญเธกเธนเธฅเธเธญเธเธเธธเธ“</div><div class="num" style="font-size:20px">เธชเนเธงเธเธ•เธฑเธง</div></div>
    </div>
    <div class="card"><h3>เนเธเธเธเธฒเธฃเธชเธญเธเธเธญเธเธเธฑเธ</h3><p class="sub">เธกเธตเน€เธเธตเธขเธเธเธฑเธเธเธตเธเธญเธเธเธธเธ“เน€เธ—เนเธฒเธเธฑเนเธเธ—เธตเนเน€เธซเนเธเนเธฅเธฐเธเธฑเธ”เธเธฒเธฃเนเธเธเน€เธซเธฅเนเธฒเธเธตเนเนเธ”เน</p>
    {% if plans %}
      {% for p in plans %}
      <div class="lesson"><h4>{{ p.topic }}</h4><small>{{ p.subject }} ยท {{ p.grade }} ยท {{ p.duration }} ยท {{ p.created_at.strftime('%d/%m/%Y') }}</small>
      <p><b>เธเธธเธ”เธเธฃเธฐเธชเธเธเน:</b> {{ p.objectives or 'เธขเธฑเธเนเธกเนเนเธ”เนเธฃเธฐเธเธธ' }}</p>
      <div class="actions"><a class="btn secondary" href="{{ url_for('view_plan', plan_id=p.id) }}">เน€เธเธดเธ”เนเธเธ</a>
      <form method="post" action="{{ url_for('delete_plan', plan_id=p.id) }}" onsubmit="return confirm('เธขเธทเธเธขเธฑเธเธฅเธเนเธเธเธเธตเนเธซเธฃเธทเธญเนเธกเน?')"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><button class="danger" type="submit">เธฅเธเนเธเธ</button></form></div></div>
      {% endfor %}
    {% else %}
      <div class="empty">เธขเธฑเธเนเธกเนเธกเธตเนเธเธเธเธฒเธฃเธชเธญเธ เธเธ” โ€เธชเธฃเนเธฒเธเนเธเธเธเธฒเธฃเธชเธญเธโ€ เน€เธเธทเนเธญเน€เธฃเธดเนเธกเธ•เนเธ</div>
    {% endif %}
    </div>
    """
    return render_page("เธซเธเนเธฒเธซเธฅเธฑเธเธเธญเธเธเธฑเธ", body, plans=plans)

@app.route("/plans/new", methods=["GET", "POST"])
@login_required
def new_plan():
    if request.method == "POST":
        required = ["subject", "grade", "topic"]
        values = {key: request.form.get(key, "").strip() for key in required}
        if any(not values[k] for k in required):
            flash("เธเธฃเธธเธ“เธฒเธเธฃเธญเธเธฃเธฒเธขเธงเธดเธเธฒ เธฃเธฐเธ”เธฑเธเธเธฑเนเธ เนเธฅเธฐเธซเธฑเธงเธเนเธญเธเธ—เน€เธฃเธตเธขเธ", "error")
        else:
            plan = LessonPlan(
                user_id=get_current_user().id,
                subject=values["subject"][:120],
                grade=values["grade"][:80],
                topic=values["topic"][:180],
                duration=request.form.get("duration", "50 เธเธฒเธ—เธต")[:40],
                objectives=request.form.get("objectives", "").strip(),
                activities=request.form.get("activities", "").strip(),
                materials=request.form.get("materials", "").strip(),
                assessment=request.form.get("assessment", "").strip()
            )
            db.session.add(plan)
            db.session.commit()
            flash("เธเธฑเธเธ—เธถเธเนเธเธเธเธฒเธฃเธชเธญเธเนเธฅเนเธง")
            return redirect(url_for("view_plan", plan_id=plan.id))
    body = r"""
    <div class="card"><h2 style="margin-top:0">เธชเธฃเนเธฒเธเนเธเธเธเธฒเธฃเธชเธญเธเนเธซเธกเน</h2><p class="sub">เธเธฃเธญเธเธเนเธญเธกเธนเธฅเน€เธเธทเนเธญเธเธฑเธเธ—เธถเธเนเธเธเธเธฒเธฃเธชเธญเธเนเธเธเธฑเธเธเธตเธเธญเธเธเธธเธ“</p>
    <form method="post">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <div class="layout">
        <div class="field"><label>เธฃเธฒเธขเธงเธดเธเธฒ *</label><input name="subject" required maxlength="120" placeholder="เน€เธเนเธ เธงเธดเธ—เธขเธฒเธเธฒเธฃเธเธณเธเธงเธ“" value="{{ request.form.get('subject','') }}"></div>
        <div class="field"><label>เธฃเธฐเธ”เธฑเธเธเธฑเนเธ *</label><input name="grade" required maxlength="80" placeholder="เน€เธเนเธ เธก.2" value="{{ request.form.get('grade','') }}"></div>
        <div class="field"><label>เธซเธฑเธงเธเนเธญเธเธ—เน€เธฃเธตเธขเธ *</label><input name="topic" required maxlength="180" placeholder="เน€เธเนเธ เธเธฒเธฃเธเธดเธ”เน€เธเธดเธเธ•เธฃเธฃเธเธฐ" value="{{ request.form.get('topic','') }}"></div>
        <div class="field"><label>เธฃเธฐเธขเธฐเน€เธงเธฅเธฒ</label><select name="duration">{% for d in ['50 เธเธฒเธ—เธต','60 เธเธฒเธ—เธต','90 เธเธฒเธ—เธต','100 เธเธฒเธ—เธต','120 เธเธฒเธ—เธต'] %}<option {% if request.form.get('duration','50 เธเธฒเธ—เธต')==d %}selected{% endif %}>{{ d }}</option>{% endfor %}</select></div>
      </div>
      <div class="field"><label>เธเธธเธ”เธเธฃเธฐเธชเธเธเนเธเธฒเธฃเน€เธฃเธตเธขเธเธฃเธนเน</label><textarea name="objectives" placeholder="เน€เธกเธทเนเธญเธเธเธเธ—เน€เธฃเธตเธขเธ เธเธนเนเน€เธฃเธตเธขเธเธเธฐเธชเธฒเธกเธฒเธฃเธ–...">{{ request.form.get('objectives','') }}</textarea></div>
      <div class="field"><label>เธเธดเธเธเธฃเธฃเธกเธเธฒเธฃเน€เธฃเธตเธขเธเธฃเธนเน / เธเธฑเนเธเธ•เธญเธเธเธฒเธฃเธชเธญเธ</label><textarea name="activities" placeholder="1. เธเธฑเนเธเธเธณเน€เธเนเธฒเธชเธนเนเธเธ—เน€เธฃเธตเธขเธ&#10;2. เธเธฑเนเธเธเธฑเธ”เธเธดเธเธเธฃเธฃเธก&#10;3. เธเธฑเนเธเธชเธฃเธธเธ">{{ request.form.get('activities','') }}</textarea></div>
      <div class="field"><label>เธชเธทเนเธญเนเธฅเธฐเธญเธธเธเธเธฃเธ“เน</label><textarea name="materials" placeholder="เน€เธเนเธ เธชเนเธฅเธ”เน เนเธเธเธฒเธ เธงเธดเธ”เธตเนเธญ เธญเธธเธเธเธฃเธ“เน">{{ request.form.get('materials','') }}</textarea></div>
      <div class="field"><label>เธเธฒเธฃเธงเธฑเธ”เนเธฅเธฐเธเธฃเธฐเน€เธกเธดเธเธเธฅ</label><textarea name="assessment" placeholder="เน€เธเนเธ เธ•เธฃเธงเธเนเธเธเธฒเธ เธชเธฑเธเน€เธเธ•เธเธฒเธฃเธ—เธณเธเธฒเธเธเธฅเธธเนเธก เนเธเธเธ—เธ”เธชเธญเธเธ—เนเธฒเธขเธเธ—">{{ request.form.get('assessment','') }}</textarea></div>
      <div class="actions"><button class="primary" type="submit">เธเธฑเธเธ—เธถเธเนเธเธเธเธฒเธฃเธชเธญเธ</button><a class="btn secondary" href="{{ url_for('dashboard') }}">เธขเธเน€เธฅเธดเธ</a></div>
    </form></div>
    """
    return render_page("เธชเธฃเนเธฒเธเนเธเธเธเธฒเธฃเธชเธญเธ", body)

@app.route("/plans/<int:plan_id>")
@login_required
def view_plan(plan_id):
    plan = LessonPlan.query.filter_by(id=plan_id, user_id=get_current_user().id).first_or_404()
    body = r"""
    <div class="card"><div class="welcome"><div><span class="tag">เนเธเธเธเธฒเธฃเธชเธญเธ</span><h2 style="margin-top:10px">{{ plan.topic }}</h2><p class="muted">{{ plan.subject }} ยท {{ plan.grade }} ยท {{ plan.duration }}</p></div><a class="btn secondary" href="{{ url_for('dashboard') }}">เธเธฅเธฑเธเธซเธเนเธฒเธซเธฅเธฑเธ</a></div>
    <div class="lesson"><h3>เธเธธเธ”เธเธฃเธฐเธชเธเธเนเธเธฒเธฃเน€เธฃเธตเธขเธเธฃเธนเน</h3><p>{{ plan.objectives or 'เธขเธฑเธเนเธกเนเนเธ”เนเธฃเธฐเธเธธ' }}</p></div>
    <div class="lesson"><h3>เธเธดเธเธเธฃเธฃเธกเธเธฒเธฃเน€เธฃเธตเธขเธเธฃเธนเน / เธเธฑเนเธเธ•เธญเธเธเธฒเธฃเธชเธญเธ</h3><p>{{ plan.activities or 'เธขเธฑเธเนเธกเนเนเธ”เนเธฃเธฐเธเธธ' }}</p></div>
    <div class="lesson"><h3>เธชเธทเนเธญเนเธฅเธฐเธญเธธเธเธเธฃเธ“เน</h3><p>{{ plan.materials or 'เธขเธฑเธเนเธกเนเนเธ”เนเธฃเธฐเธเธธ' }}</p></div>
    <div class="lesson"><h3>เธเธฒเธฃเธงเธฑเธ”เนเธฅเธฐเธเธฃเธฐเน€เธกเธดเธเธเธฅ</h3><p>{{ plan.assessment or 'เธขเธฑเธเนเธกเนเนเธ”เนเธฃเธฐเธเธธ' }}</p></div>
    <p class="muted">เธชเธฃเนเธฒเธเน€เธกเธทเนเธญ {{ plan.created_at.strftime('%d/%m/%Y %H:%M') }}</p>
    <button class="primary" onclick="window.print()">เธเธดเธกเธเน / เธเธฑเธเธ—เธถเธเน€เธเนเธ PDF</button></div>
    """
    return render_page("เธฃเธฒเธขเธฅเธฐเน€เธญเธตเธขเธ”เนเธเธ", body, plan=plan)

@app.route("/plans/<int:plan_id>/delete", methods=["POST"])
@login_required
def delete_plan(plan_id):
    plan = LessonPlan.query.filter_by(id=plan_id, user_id=get_current_user().id).first_or_404()
    db.session.delete(plan)
    db.session.commit()
    flash("เธฅเธเนเธเธเธเธฒเธฃเธชเธญเธเนเธฅเนเธง")
    return redirect(url_for("dashboard"))

@app.errorhandler(404)
def not_found(_error):
    return render_page("เนเธกเนเธเธเธซเธเนเธฒ", '<div class="card"><h2>เนเธกเนเธเธเธซเธเนเธฒเธ—เธตเนเธ•เนเธญเธเธเธฒเธฃ</h2><a class="btn primary" href="/">เธเธฅเธฑเธเธซเธเนเธฒเธซเธฅเธฑเธ</a></div>'), 404

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
