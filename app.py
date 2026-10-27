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
    duration = db.Column(db.String(40), nullable=False, default="50 นาที")
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
  <div class="brand"><div class="logo">T</div><div><h1>TeacherKit</h1><p>Smart Teaching Assistant · ผู้ช่วยเตรียมการสอน</p></div></div>
  <nav>
  {% if current_user %}
    <a href="{{ url_for('dashboard') }}">หน้าหลัก</a>
    <a href="{{ url_for('new_plan') }}">สร้างแผนการสอน</a>
    <a href="{{ url_for('logout') }}">ออกจากระบบ</a>
  {% else %}
    <a href="{{ url_for('login') }}">เข้าสู่ระบบ</a>
    <a href="{{ url_for('register') }}">สมัครสมาชิก</a>
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
    </main><footer>TeacherKit · วางแผนการสอนอย่างเป็นระบบ</footer></body></html>"""
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
            flash("กรุณาเข้าสู่ระบบก่อนใช้งาน", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

@app.route("/")
def index():
    if get_current_user():
        return redirect(url_for("dashboard"))
    body = r"""
    <section class="welcome"><div><h2>เตรียมการสอนให้ง่ายขึ้นในที่เดียว 📚</h2>
    <p class="muted">สร้างแผนการสอน จัดกิจกรรม วางแผนสื่อ และบันทึกข้อมูลแยกตามบัญชีผู้ใช้</p></div></section>
    <div class="grid">
      <div class="card"><h3>📝 แผนการสอน</h3><p class="muted">บันทึกวิชา ระดับชั้น หัวข้อ และจุดประสงค์การเรียนรู้</p></div>
      <div class="card"><h3>🎯 กิจกรรมการเรียนรู้</h3><p class="muted">วางขั้นนำเข้าสู่บทเรียน ขั้นสอน และขั้นสรุป</p></div>
      <div class="card"><h3>🔐 บัญชีส่วนตัว</h3><p class="muted">สมัครสมาชิกและเข้าสู่ระบบ เพื่อดูแผนของบัญชีตัวเอง</p></div>
    </div>
    <div class="card" style="margin-top:18px"><h3>เริ่มต้นใช้งาน TeacherKit</h3><p class="muted">สร้างบัญชีเพื่อบันทึกและกลับมาดูแผนการสอนได้ในภายหลัง</p>
    <div class="actions" style="margin-top:16px"><a class="btn primary" href="{{ url_for('register') }}">สมัครสมาชิกฟรี</a><a class="btn secondary" href="{{ url_for('login') }}">มีบัญชีแล้ว · เข้าสู่ระบบ</a></div></div>
    """
    return render_page("หน้าหลัก", body)

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
            flash("กรุณากรอกชื่อไม่เกิน 80 ตัวอักษร", "error")
        elif not email or "@" not in email or len(email) > 160:
            flash("กรุณากรอกอีเมลให้ถูกต้อง", "error")
        elif len(password) < 8:
            flash("รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร", "error")
        elif password != confirm:
            flash("รหัสผ่านทั้งสองช่องไม่ตรงกัน", "error")
        elif User.query.filter_by(email=email).first():
            flash("อีเมลนี้มีบัญชีแล้ว กรุณาเข้าสู่ระบบ", "error")
        else:
            user = User(name=name, email=email, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            session.clear()
            session["user_id"] = user.id
            flash("สมัครสมาชิกสำเร็จ ยินดีต้อนรับสู่ TeacherKit")
            return redirect(url_for("dashboard"))
    body = r"""
    <div class="auth-wrap"><div class="card"><h2>สร้างบัญชี TeacherKit</h2><p class="sub">สมัครสมาชิกเพื่อบันทึกแผนการสอนของคุณ</p>
    <form method="post">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <div class="field"><label>ชื่อที่ใช้แสดง</label><input name="name" required maxlength="80" autocomplete="name" value="{{ request.form.get('name','') }}"></div>
      <div class="field"><label>อีเมล</label><input type="email" name="email" required maxlength="160" autocomplete="email" value="{{ request.form.get('email','') }}"></div>
      <div class="field"><label>รหัสผ่าน (อย่างน้อย 8 ตัวอักษร)</label><input type="password" name="password" required minlength="8" autocomplete="new-password"></div>
      <div class="field"><label>ยืนยันรหัสผ่าน</label><input type="password" name="confirm" required minlength="8" autocomplete="new-password"></div>
      <button class="primary" type="submit" style="width:100%">สมัครสมาชิก</button>
    </form><div class="switch">มีบัญชีแล้ว? <a href="{{ url_for('login') }}">เข้าสู่ระบบ</a></div></div></div>
    """
    return render_page("สมัครสมาชิก", body)

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
            flash("เข้าสู่ระบบสำเร็จ")
            return redirect(url_for("dashboard"))
        flash("อีเมลหรือรหัสผ่านไม่ถูกต้อง", "error")
    body = r"""
    <div class="auth-wrap"><div class="card"><h2>เข้าสู่ระบบ</h2><p class="sub">เข้าสู่บัญชีเพื่อจัดการแผนการสอนของคุณ</p>
    <form method="post">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <div class="field"><label>อีเมล</label><input type="email" name="email" required autocomplete="email" value="{{ request.form.get('email','') }}"></div>
      <div class="field"><label>รหัสผ่าน</label><input type="password" name="password" required autocomplete="current-password"></div>
      <button class="primary" type="submit" style="width:100%">เข้าสู่ระบบ</button>
    </form><div class="switch">ยังไม่มีบัญชี? <a href="{{ url_for('register') }}">สมัครสมาชิก</a></div></div></div>
    """
    return render_page("เข้าสู่ระบบ", body)

@app.route("/logout")
def logout():
    session.clear()
    flash("ออกจากระบบแล้ว")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    plans = LessonPlan.query.filter_by(user_id=user.id).order_by(LessonPlan.created_at.desc()).all()
    body = r"""
    <section class="welcome"><div><h2>สวัสดี {{ current_user.name }} 👋</h2><p class="muted">พื้นที่จัดการการเตรียมการสอนของคุณ</p></div>
    <a class="btn primary" href="{{ url_for('new_plan') }}">+ สร้างแผนการสอน</a></section>
    <div class="grid" style="margin-bottom:20px">
      <div class="stat"><div class="label">แผนการสอนทั้งหมด</div><div class="num">{{ plans|length }}</div></div>
      <div class="stat"><div class="label">บัญชีผู้ใช้</div><div class="num" style="font-size:20px">ยืนยันด้วยอีเมล</div></div>
      <div class="stat"><div class="label">ข้อมูลของคุณ</div><div class="num" style="font-size:20px">ส่วนตัว</div></div>
    </div>
    <div class="card"><h3>แผนการสอนของฉัน</h3><p class="sub">มีเพียงบัญชีของคุณเท่านั้นที่เห็นและจัดการแผนเหล่านี้ได้</p>
    {% if plans %}
      {% for p in plans %}
      <div class="lesson"><h4>{{ p.topic }}</h4><small>{{ p.subject }} · {{ p.grade }} · {{ p.duration }} · {{ p.created_at.strftime('%d/%m/%Y') }}</small>
      <p><b>จุดประสงค์:</b> {{ p.objectives or 'ยังไม่ได้ระบุ' }}</p>
      <div class="actions"><a class="btn secondary" href="{{ url_for('view_plan', plan_id=p.id) }}">เปิดแผน</a>
      <form method="post" action="{{ url_for('delete_plan', plan_id=p.id) }}" onsubmit="return confirm('ยืนยันลบแผนนี้หรือไม่?')"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><button class="danger" type="submit">ลบแผน</button></form></div></div>
      {% endfor %}
    {% else %}
      <div class="empty">ยังไม่มีแผนการสอน กด “สร้างแผนการสอน” เพื่อเริ่มต้น</div>
    {% endif %}
    </div>
    """
    return render_page("หน้าหลักของฉัน", body, plans=plans)

@app.route("/plans/new", methods=["GET", "POST"])
@login_required
def new_plan():
    if request.method == "POST":
        required = ["subject", "grade", "topic"]
        values = {key: request.form.get(key, "").strip() for key in required}
        if any(not values[k] for k in required):
            flash("กรุณากรอกรายวิชา ระดับชั้น และหัวข้อบทเรียน", "error")
        else:
            plan = LessonPlan(
                user_id=get_current_user().id,
                subject=values["subject"][:120],
                grade=values["grade"][:80],
                topic=values["topic"][:180],
                duration=request.form.get("duration", "50 นาที")[:40],
                objectives=request.form.get("objectives", "").strip(),
                activities=request.form.get("activities", "").strip(),
                materials=request.form.get("materials", "").strip(),
                assessment=request.form.get("assessment", "").strip()
            )
            db.session.add(plan)
            db.session.commit()
            flash("บันทึกแผนการสอนแล้ว")
            return redirect(url_for("view_plan", plan_id=plan.id))
    body = r"""
    <div class="card"><h2 style="margin-top:0">สร้างแผนการสอนใหม่</h2><p class="sub">กรอกข้อมูลเพื่อบันทึกแผนการสอนในบัญชีของคุณ</p>
    <form method="post">
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
      <div class="layout">
        <div class="field"><label>รายวิชา *</label><input name="subject" required maxlength="120" placeholder="เช่น วิทยาการคำนวณ" value="{{ request.form.get('subject','') }}"></div>
        <div class="field"><label>ระดับชั้น *</label><input name="grade" required maxlength="80" placeholder="เช่น ม.2" value="{{ request.form.get('grade','') }}"></div>
        <div class="field"><label>หัวข้อบทเรียน *</label><input name="topic" required maxlength="180" placeholder="เช่น การคิดเชิงตรรกะ" value="{{ request.form.get('topic','') }}"></div>
        <div class="field"><label>ระยะเวลา</label><select name="duration">{% for d in ['50 นาที','60 นาที','90 นาที','100 นาที','120 นาที'] %}<option {% if request.form.get('duration','50 นาที')==d %}selected{% endif %}>{{ d }}</option>{% endfor %}</select></div>
      </div>
      <div class="field"><label>จุดประสงค์การเรียนรู้</label><textarea name="objectives" placeholder="เมื่อจบบทเรียน ผู้เรียนจะสามารถ...">{{ request.form.get('objectives','') }}</textarea></div>
      <div class="field"><label>กิจกรรมการเรียนรู้ / ขั้นตอนการสอน</label><textarea name="activities" placeholder="1. ขั้นนำเข้าสู่บทเรียน&#10;2. ขั้นจัดกิจกรรม&#10;3. ขั้นสรุป">{{ request.form.get('activities','') }}</textarea></div>
      <div class="field"><label>สื่อและอุปกรณ์</label><textarea name="materials" placeholder="เช่น สไลด์ ใบงาน วิดีโอ อุปกรณ์">{{ request.form.get('materials','') }}</textarea></div>
      <div class="field"><label>การวัดและประเมินผล</label><textarea name="assessment" placeholder="เช่น ตรวจใบงาน สังเกตการทำงานกลุ่ม แบบทดสอบท้ายบท">{{ request.form.get('assessment','') }}</textarea></div>
      <div class="actions"><button class="primary" type="submit">บันทึกแผนการสอน</button><a class="btn secondary" href="{{ url_for('dashboard') }}">ยกเลิก</a></div>
    </form></div>
    """
    return render_page("สร้างแผนการสอน", body)

@app.route("/plans/<int:plan_id>")
@login_required
def view_plan(plan_id):
    plan = LessonPlan.query.filter_by(id=plan_id, user_id=get_current_user().id).first_or_404()
    body = r"""
    <div class="card"><div class="welcome"><div><span class="tag">แผนการสอน</span><h2 style="margin-top:10px">{{ plan.topic }}</h2><p class="muted">{{ plan.subject }} · {{ plan.grade }} · {{ plan.duration }}</p></div><a class="btn secondary" href="{{ url_for('dashboard') }}">กลับหน้าหลัก</a></div>
    <div class="lesson"><h3>จุดประสงค์การเรียนรู้</h3><p>{{ plan.objectives or 'ยังไม่ได้ระบุ' }}</p></div>
    <div class="lesson"><h3>กิจกรรมการเรียนรู้ / ขั้นตอนการสอน</h3><p>{{ plan.activities or 'ยังไม่ได้ระบุ' }}</p></div>
    <div class="lesson"><h3>สื่อและอุปกรณ์</h3><p>{{ plan.materials or 'ยังไม่ได้ระบุ' }}</p></div>
    <div class="lesson"><h3>การวัดและประเมินผล</h3><p>{{ plan.assessment or 'ยังไม่ได้ระบุ' }}</p></div>
    <p class="muted">สร้างเมื่อ {{ plan.created_at.strftime('%d/%m/%Y %H:%M') }}</p>
    <button class="primary" onclick="window.print()">พิมพ์ / บันทึกเป็น PDF</button></div>
    """
    return render_page("รายละเอียดแผน", body, plan=plan)

@app.route("/plans/<int:plan_id>/delete", methods=["POST"])
@login_required
def delete_plan(plan_id):
    plan = LessonPlan.query.filter_by(id=plan_id, user_id=get_current_user().id).first_or_404()
    db.session.delete(plan)
    db.session.commit()
    flash("ลบแผนการสอนแล้ว")
    return redirect(url_for("dashboard"))

@app.errorhandler(404)
def not_found(_error):
    return render_page("ไม่พบหน้า", '<div class="card"><h2>ไม่พบหน้าที่ต้องการ</h2><a class="btn primary" href="/">กลับหน้าหลัก</a></div>'), 404

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
