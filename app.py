import os
from datetime import datetime, date
from functools import wraps

from flask import Flask, request, redirect, url_for, render_template_string, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-change-this-secret-key')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('RENDER', '').lower() == 'true'

database_url = os.environ.get('DATABASE_URL', 'sqlite:///teacherkit.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
elif database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
# psycopg[binary] is installed in requirements.txt for Render PostgreSQL.
app.config['SQLALCHEMY_DATABASE_URI'] = database_url

db = SQLAlchemy(app)
csrf = CSRFProtect(app)


# Keep the original User and LessonPlan table names/columns intact so existing data remains available.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    lessons = db.relationship('LessonPlan', backref='owner', cascade='all, delete-orphan', lazy=True)


class LessonPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    subject = db.Column(db.String(120), nullable=False)
    grade = db.Column(db.String(80), nullable=False)
    topic = db.Column(db.String(180), nullable=False)
    duration = db.Column(db.String(40), nullable=False, default='50 นาที')
    objectives = db.Column(db.Text, nullable=False, default='')
    activities = db.Column(db.Text, nullable=False, default='')
    materials = db.Column(db.Text, nullable=False, default='')
    assessment = db.Column(db.Text, nullable=False, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    subject = db.Column(db.String(120), nullable=False, default='')
    grade = db.Column(db.String(80), nullable=False, default='')
    questions = db.Column(db.Text, nullable=False, default='')
    answer_key = db.Column(db.Text, nullable=False, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class TeachingTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='ยังไม่เสร็จ')
    notes = db.Column(db.Text, nullable=False, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


STYLE = r'''
:root{--navy:#172554;--blue:#3157d5;--pale:#eaf0ff;--ink:#202943;--muted:#68738c;--line:#e5e9f2;--bg:#f5f7fc;--green:#13845b;--red:#b42318}
*{box-sizing:border-box}body{margin:0;font-family:Tahoma,"Noto Sans Thai",sans-serif;background:var(--bg);color:var(--ink)}
header{background:linear-gradient(120deg,#172554,#3157d5);color:white;padding:20px max(18px,calc((100% - 1160px)/2));display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap}.brand{display:flex;align-items:center;gap:11px}.logo{width:42px;height:42px;border-radius:13px;background:white;color:var(--blue);display:grid;place-items:center;font-weight:bold;font-size:23px}.brand h1{font-size:23px;margin:0}.brand p{font-size:12px;color:#dce5ff;margin:4px 0 0}nav{display:flex;gap:7px;flex-wrap:wrap}nav a{color:white;text-decoration:none;padding:9px 11px;border-radius:9px;background:#ffffff1b;font-size:13px}
main{max-width:1160px;margin:26px auto;padding:0 20px 40px}.welcome{display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap;margin-bottom:20px}.welcome h2{margin:0 0 6px;font-size:26px}.muted,.welcome p{color:var(--muted);margin:0;line-height:1.65}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.layout{display:grid;grid-template-columns:1fr 1fr;gap:16px}.card,.stat{background:white;border:1px solid var(--line);border-radius:16px;padding:20px;box-shadow:0 4px 16px #1d2c5309}.stat .label{font-size:13px;color:var(--muted)}.stat .num{font-size:28px;font-weight:bold;margin-top:7px}h2{line-height:1.35}h3{margin:0 0 7px;font-size:19px}.sub{font-size:13px;color:var(--muted);margin:0 0 17px}.field{margin-bottom:14px}label{display:block;font-size:14px;font-weight:bold;margin-bottom:7px}input,select,textarea{width:100%;font:inherit;padding:11px 12px;border:1px solid #d8deeb;border-radius:9px;background:white;color:var(--ink)}textarea{min-height:100px;resize:vertical}input:focus,textarea:focus,select:focus{outline:2px solid #3157d52b;border-color:var(--blue)}button,.btn{display:inline-block;border:0;border-radius:9px;padding:11px 14px;font:inherit;font-weight:bold;cursor:pointer;text-decoration:none}.primary{background:var(--blue);color:white}.secondary{background:var(--pale);color:var(--blue)}.danger{background:#fff0f0;color:var(--red)}.actions{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.flash{padding:12px 14px;border-radius:10px;margin-bottom:14px;background:#effaf5;color:#176747;border:1px solid #c9efdd}.flash.error{background:#fff2f0;color:#9f241b;border-color:#ffd7d1}.lesson{border:1px solid var(--line);border-radius:12px;padding:16px;margin-top:12px;background:white}.lesson h4{margin:0 0 6px;font-size:17px}.lesson small{color:var(--muted)}.lesson p{white-space:pre-line;line-height:1.7}.tag{display:inline-block;background:var(--pale);color:var(--blue);padding:4px 9px;border-radius:20px;font-size:12px}.empty{text-align:center;padding:25px 10px;color:var(--muted)}.tile{display:block;color:inherit;text-decoration:none;transition:transform .15s,border-color .15s}.tile:hover{transform:translateY(-2px);border-color:#aabaf7}.tile .emoji{font-size:25px;margin-bottom:10px}.tile p{color:var(--muted);line-height:1.6;margin-bottom:0}.split{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}.inline-form{display:inline}.small{font-size:12px;color:var(--muted)}footer{text-align:center;color:var(--muted);font-size:12px;padding:20px}
@media(max-width:760px){.grid,.layout{grid-template-columns:1fr}.welcome h2{font-size:22px}main{padding:0 13px 30px}.card{padding:16px}header{padding:16px}nav a{font-size:12px}}
@media print{header,footer,.no-print,button,.btn{display:none!important}body{background:white;color:#111}main{max-width:none;margin:0;padding:0}.card,.lesson{box-shadow:none;border:0;padding:8px}.print-title{display:block}}
'''

HEADER = r'''<header><div class="brand"><div class="logo">T</div><div><h1>TeacherKit</h1><p>Smart Teaching Assistant · ผู้ช่วยเตรียมการสอน</p></div></div><nav>{% if current_user %}<a href="{{ url_for('dashboard') }}">หน้าหลัก</a><a href="{{ url_for('new_plan') }}">สร้างแผน</a><a href="{{ url_for('quiz_list') }}">แบบทดสอบ</a><a href="{{ url_for('calendar') }}">ปฏิทิน/งาน</a><a href="{{ url_for('ai_studio') }}">AI Studio</a><a href="{{ url_for('logout') }}">ออกจากระบบ</a>{% else %}<a href="{{ url_for('login') }}">เข้าสู่ระบบ</a><a href="{{ url_for('register') }}">สมัครสมาชิก</a>{% endif %}</nav></header>'''


def current_user():
    uid = session.get('user_id')
    return db.session.get(User, uid) if uid else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash('กรุณาเข้าสู่ระบบก่อนใช้งาน', 'error')
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped


def page(title, body, **ctx):
    template = '<!doctype html><html lang="th"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{ title }} | TeacherKit</title><style>' + STYLE + '</style></head><body>' + HEADER + '<main>{% with messages=get_flashed_messages(with_categories=true) %}{% for category,message in messages %}<div class="flash {{ "error" if category=="error" else "" }}">{{ message }}</div>{% endfor %}{% endwith %}' + body + '</main><footer>TeacherKit · วางแผนการสอนอย่างเป็นระบบ</footer></body></html>'
    return render_template_string(template, title=title, current_user=current_user(), **ctx)


def owned_plan(plan_id):
    return LessonPlan.query.filter_by(id=plan_id, user_id=current_user().id).first_or_404()


def build_free_draft(kind, subject, grade, topic, duration):
    """Generate an editable teaching scaffold locally; no external AI/API calls."""
    subject = subject or 'ยังไม่ระบุวิชา'
    grade = grade or 'ปรับตามระดับชั้น'
    if kind == 'quiz':
        questions = [
            f'1. อธิบายความหมายของ “{topic}” ด้วยคำพูดของตนเอง',
            f'2. ยกตัวอย่าง {topic} ที่พบได้ในชีวิตประจำวัน 1 ตัวอย่าง พร้อมอธิบาย',
            f'3. ข้อใดเป็นลักษณะสำคัญของ {topic}? (ครูเติมตัวเลือกให้ตรงกับเนื้อหาที่สอน)',
            f'4. สถานการณ์ใดแสดงการนำ {topic} ไปใช้ได้เหมาะสมที่สุด? (ครูเติมสถานการณ์และตัวเลือก)',
            f'5. เปรียบเทียบ {topic} กับแนวคิดที่เกี่ยวข้อง 1 ประเด็น',
            f'6. อ่านตัวอย่าง/ข้อมูลเกี่ยวกับ {topic} แล้วตอบคำถาม (ครูเพิ่มข้อมูลประกอบ)',
            f'7. วิเคราะห์ข้อผิดพลาดที่อาจเกิดขึ้นเมื่อเรียนเรื่อง {topic}',
            f'8. สรุปสิ่งที่ได้เรียนรู้เกี่ยวกับ {topic} และเสนอวิธีนำไปใช้ 1 วิธี',
        ]
        return (f'ร่างแบบทดสอบ: {topic}\nวิชา: {subject} | ระดับชั้น: {grade}\n\n' + '\n\n'.join(questions) + '\n\nหมายเหตุ: นี่คือแม่แบบคำถาม ไม่ใช่ข้อสอบที่สร้างด้วย AI โปรดเติมตัวเลือก/ข้อมูลประกอบและตรวจความถูกต้องให้ตรงกับบทเรียนก่อนใช้'), None
    return (f'ร่างแผนการจัดการเรียนรู้\nวิชา: {subject}\nระดับชั้น: {grade}\nหัวข้อ: {topic}\nเวลา: {duration or "50 นาที"}\n\n'
            f'1. จุดประสงค์การเรียนรู้\n- ผู้เรียนอธิบายแนวคิดสำคัญของเรื่อง {topic} ได้\n- ผู้เรียนยกตัวอย่างหรือประยุกต์ใช้ความรู้เรื่อง {topic} ได้\n- ผู้เรียนสื่อสารสิ่งที่เรียนรู้และสะท้อนผลการเรียนรู้ได้\n\n'
            '2. ขั้นนำเข้าสู่บทเรียน (ประมาณ 5 นาที)\n- ครูตั้งคำถามกระตุ้นความคิดหรือยกสถานการณ์ใกล้ตัวที่เชื่อมโยงกับหัวข้อ\n- ให้ผู้เรียนแลกเปลี่ยนความรู้เดิม\n\n'
            '3. ขั้นกิจกรรมการเรียนรู้\n- ครูอธิบายแนวคิดสำคัญพร้อมตัวอย่างที่เหมาะกับวัย\n- ผู้เรียนทำงานเดี่ยว/คู่/กลุ่มเพื่อสำรวจ วิเคราะห์ หรือแก้โจทย์เกี่ยวกับหัวข้อ\n- ให้ผู้เรียนอธิบายเหตุผลและแลกเปลี่ยนคำตอบ ครูให้ข้อเสนอแนะ\n\n'
            '4. ขั้นสรุป (ประมาณ 5 นาที)\n- ผู้เรียนสรุปประเด็นสำคัญด้วยแผนผังความคิดหรือบัตรออกจากห้อง\n- ครูทบทวนความเข้าใจและแก้ความเข้าใจคลาดเคลื่อน\n\n'
            '5. สื่อและอุปกรณ์\n- หนังสือ/เอกสารประกอบบทเรียน\n- ใบงานหรือบัตรคำถามเกี่ยวกับหัวข้อ\n- กระดานหรืออุปกรณ์นำเสนอที่มีอยู่\n\n'
            '6. การวัดและประเมินผล\n- ตรวจคำตอบจากใบงานหรือภาระงาน\n- สังเกตการมีส่วนร่วมและการอธิบายเหตุผล\n- ใช้คำถามสั้นท้ายคาบเพื่อตรวจความเข้าใจ\n\n'
            'หมายเหตุ: นี่คือแม่แบบช่วยวางแผน ไม่ใช่เนื้อหาที่สร้างโดย AI โปรดปรับกิจกรรม เวลา และเกณฑ์ประเมินให้ตรงกับตัวชี้วัดและบริบทของห้องเรียน'), None


@app.route('/')
def index():
    if current_user():
        return redirect(url_for('dashboard'))
    body = r'''<section class="welcome"><div><h2>เตรียมการสอนให้ง่ายขึ้นในที่เดียว 📚</h2><p>วางแผนบทเรียน สร้างแบบทดสอบ ติดตามงาน และใช้ AI ช่วยร่างเนื้อหา</p></div><div class="actions"><a class="btn primary" href="{{ url_for('register') }}">เริ่มใช้งานฟรี</a><a class="btn secondary" href="{{ url_for('login') }}">เข้าสู่ระบบ</a></div></section><div class="grid"><div class="card"><div class="emoji">📝</div><h3>Smart Lesson Planner</h3><p class="muted">สร้างแผนด้วยแม่แบบกิจกรรมที่นำไปปรับใช้ได้</p></div><div class="card"><div class="emoji">🎯</div><h3>Quiz & Worksheet</h3><p class="muted">สร้างข้อสอบพร้อมเฉลยและหน้าพิมพ์</p></div><div class="card"><div class="emoji">✨</div><h3>AI Studio</h3><p class="muted">สร้างร่างจากแม่แบบฟรี ไม่ใช้ API ภายนอก</p></div></div>'''
    return page('ยินดีต้อนรับ', body)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user(): return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip(); email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', ''); confirm = request.form.get('confirm', '')
        if not name or len(name) > 80: flash('กรุณากรอกชื่อไม่เกิน 80 ตัวอักษร', 'error')
        elif not email or '@' not in email or len(email) > 160: flash('กรุณากรอกอีเมลให้ถูกต้อง', 'error')
        elif len(password) < 8: flash('รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร', 'error')
        elif password != confirm: flash('รหัสผ่านทั้งสองช่องไม่ตรงกัน', 'error')
        elif User.query.filter_by(email=email).first(): flash('อีเมลนี้มีบัญชีแล้ว กรุณาเข้าสู่ระบบ', 'error')
        else:
            user = User(name=name, email=email, password_hash=generate_password_hash(password)); db.session.add(user); db.session.commit()
            session.clear(); session['user_id'] = user.id; return redirect(url_for('dashboard'))
    body = r'''<div class="card" style="max-width:500px;margin:auto"><h2>สร้างบัญชี TeacherKit</h2><form method="post"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><div class="field"><label>ชื่อที่แสดง</label><input name="name" required maxlength="80" value="{{ request.form.get('name','') }}"></div><div class="field"><label>อีเมล</label><input type="email" name="email" required value="{{ request.form.get('email','') }}"></div><div class="field"><label>รหัสผ่าน (อย่างน้อย 8 ตัวอักษร)</label><input type="password" name="password" minlength="8" required></div><div class="field"><label>ยืนยันรหัสผ่าน</label><input type="password" name="confirm" minlength="8" required></div><button class="primary">สมัครสมาชิก</button></form></div>'''
    return page('สมัครสมาชิก', body)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user(): return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower(); password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear(); session['user_id'] = user.id; return redirect(url_for('dashboard'))
        flash('อีเมลหรือรหัสผ่านไม่ถูกต้อง', 'error')
    body = r'''<div class="card" style="max-width:500px;margin:auto"><h2>เข้าสู่ระบบ</h2><form method="post"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><div class="field"><label>อีเมล</label><input type="email" name="email" required autocomplete="email"></div><div class="field"><label>รหัสผ่าน</label><input type="password" name="password" required autocomplete="current-password"></div><button class="primary">เข้าสู่ระบบ</button></form><p class="sub" style="margin-top:15px">ยังไม่มีบัญชี? <a href="{{ url_for('register') }}">สมัครสมาชิก</a></p></div>'''
    return page('เข้าสู่ระบบ', body)


@app.route('/logout')
def logout():
    session.clear(); flash('ออกจากระบบแล้ว'); return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user()
    plans = LessonPlan.query.filter_by(user_id=user.id).order_by(LessonPlan.created_at.desc()).limit(5).all()
    plan_count = LessonPlan.query.filter_by(user_id=user.id).count()
    quiz_count = Quiz.query.filter_by(user_id=user.id).count()
    open_tasks = TeachingTask.query.filter_by(user_id=user.id, status='ยังไม่เสร็จ').count()
    upcoming = TeachingTask.query.filter_by(user_id=user.id).order_by(TeachingTask.due_date.asc()).limit(4).all()
    body = r'''<section class="welcome"><div><h2>สวัสดี {{ current_user.name }} 👋</h2><p>วันนี้เตรียมการสอนได้เป็นระบบขึ้นอีกนิด</p></div><a class="btn primary" href="{{ url_for('new_plan') }}">＋ สร้างแผนการสอน</a></section><div class="grid" style="margin-bottom:16px"><div class="stat"><div class="label">แผนการสอน</div><div class="num">{{ plan_count }}</div></div><div class="stat"><div class="label">แบบทดสอบ</div><div class="num">{{ quiz_count }}</div></div><div class="stat"><div class="label">งานที่ยังไม่เสร็จ</div><div class="num">{{ open_tasks }}</div></div></div><div class="grid" style="margin-bottom:18px"><a class="card tile" href="{{ url_for('new_plan') }}"><div class="emoji">📝</div><h3>Smart Lesson Planner</h3><p>สร้างแผนจากแม่แบบกิจกรรม</p></a><a class="card tile" href="{{ url_for('quiz_new') }}"><div class="emoji">🎯</div><h3>สร้างแบบทดสอบ</h3><p>บันทึกข้อสอบและเฉลย</p></a><a class="card tile" href="{{ url_for('ai_studio') }}"><div class="emoji">✨</div><h3>Teaching Studio</h3><p>สร้างร่างจากแม่แบบฟรี</p></a><a class="card tile" href="{{ url_for('search_plans') }}"><div class="emoji">🔎</div><h3>ค้นหาแผน</h3><p>ค้นหาและคัดลอกแผนเก่า</p></a><a class="card tile" href="{{ url_for('calendar') }}"><div class="emoji">🗓️</div><h3>ปฏิทินและงาน</h3><p>ติดตามกำหนดส่ง</p></a><a class="card tile" href="{{ url_for('quiz_list') }}"><div class="emoji">📚</div><h3>คลังแบบทดสอบ</h3><p>เปิดดูและพิมพ์ใบงาน</p></a></div><div class="layout"><div class="card"><div class="split"><h3>แผนล่าสุด</h3><a href="{{ url_for('search_plans') }}">ดูทั้งหมด</a></div>{% if plans %}{% for p in plans %}<div class="lesson"><h4>{{ p.topic }}</h4><small>{{ p.subject }} · {{ p.grade }}</small><div class="actions" style="margin-top:10px"><a class="btn secondary" href="{{ url_for('view_plan',plan_id=p.id) }}">เปิดแผน</a></div></div>{% endfor %}{% else %}<div class="empty">ยังไม่มีแผนการสอน เริ่มสร้างแผนแรกได้เลย</div>{% endif %}</div><div class="card"><h3>งานที่ต้องติดตาม</h3>{% if upcoming %}{% for t in upcoming %}<div class="lesson"><b>{{ t.title }}</b><p class="small">กำหนดส่ง: {{ t.due_date.strftime('%d/%m/%Y') if t.due_date else 'ยังไม่กำหนด' }} · {{ t.status }}</p></div>{% endfor %}{% else %}<div class="empty">ยังไม่มีงานที่ต้องติดตาม</div>{% endif %}<a class="btn secondary" href="{{ url_for('calendar') }}">จัดการงานทั้งหมด</a></div></div>'''
    return page('Dashboard', body, plans=plans, plan_count=plan_count, quiz_count=quiz_count, open_tasks=open_tasks, upcoming=upcoming)


@app.route('/plans/new', methods=['GET', 'POST'])
@login_required
def new_plan():
    templates = {
        '5E': '1. กระตุ้นความสนใจ (Engage) – ตั้งคำถามหรือสถานการณ์ใกล้ตัว\n2. สำรวจค้นหา (Explore) – ให้ผู้เรียนทดลอง/สืบค้นเป็นกลุ่ม\n3. อธิบาย (Explain) – ผู้เรียนอธิบายสิ่งที่ค้นพบ ครูเติมแนวคิดสำคัญ\n4. ขยายความรู้ (Elaborate) – ประยุกต์ใช้กับโจทย์ใหม่\n5. ประเมินผล (Evaluate) – Exit ticket หรือแบบทดสอบสั้น',
        'active': '1. ตั้งคำถามชวนคิดและแจ้งเป้าหมาย\n2. ผู้เรียนลงมือทำงานเดี่ยว/คู่/กลุ่ม\n3. แลกเปลี่ยนคำตอบและให้เหตุผล\n4. ครูสรุปแนวคิดและแก้ความเข้าใจคลาดเคลื่อน\n5. ประเมินความเข้าใจท้ายคาบ',
        'project': '1. นำเสนอโจทย์หรือปัญหาจริง\n2. วางแผนโครงงานและแบ่งหน้าที่\n3. ค้นคว้า ออกแบบ และสร้างชิ้นงาน\n4. ทดลอง ปรับปรุง และรับข้อเสนอแนะ\n5. นำเสนอผลงานและสะท้อนการเรียนรู้'
    }
    if request.method == 'POST':
        subject=request.form.get('subject','').strip(); grade=request.form.get('grade','').strip(); topic=request.form.get('topic','').strip()
        if not subject or not grade or not topic:
            flash('กรุณากรอกรายวิชา ระดับชั้น และหัวข้อบทเรียน', 'error')
        else:
            activities=request.form.get('activities','').strip()
            if not activities and request.form.get('template') in templates: activities=templates[request.form.get('template')]
            plan=LessonPlan(user_id=current_user().id, subject=subject[:120], grade=grade[:80], topic=topic[:180], duration=request.form.get('duration','50 นาที')[:40], objectives=request.form.get('objectives','').strip(), activities=activities, materials=request.form.get('materials','').strip(), assessment=request.form.get('assessment','').strip())
            db.session.add(plan); db.session.commit(); flash('บันทึกแผนการสอนแล้ว'); return redirect(url_for('view_plan', plan_id=plan.id))
    body = r'''<div class="card"><h2>Smart Lesson Planner</h2><p class="sub">ใช้แม่แบบกิจกรรมเพื่อเริ่มร่างแผนได้เร็วขึ้น</p><form method="post"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><div class="layout"><div class="field"><label>รายวิชา *</label><input name="subject" required maxlength="120" value="{{ request.form.get('subject','') }}" placeholder="เช่น วิทยาศาสตร์"></div><div class="field"><label>ระดับชั้น *</label><input name="grade" required maxlength="80" value="{{ request.form.get('grade','') }}" placeholder="เช่น ป.6"></div><div class="field"><label>หัวข้อบทเรียน *</label><input name="topic" required maxlength="180" value="{{ request.form.get('topic','') }}" placeholder="เช่น ระบบสุริยะ"></div><div class="field"><label>ระยะเวลา</label><select name="duration">{% for d in ['50 นาที','60 นาที','90 นาที','100 นาที','120 นาที'] %}<option {% if request.form.get('duration','50 นาที')==d %}selected{% endif %}>{{ d }}</option>{% endfor %}</select></div></div><div class="field"><label>แม่แบบกิจกรรม (เลือกเพื่อเติมกิจกรรมอัตโนมัติ)</label><select name="template"><option value="">ไม่ใช้แม่แบบ</option><option value="5E">5E: สืบเสาะหาความรู้</option><option value="active">Active Learning</option><option value="project">Project-based Learning</option></select></div><div class="field"><label>จุดประสงค์การเรียนรู้</label><textarea name="objectives">{{ request.form.get('objectives','') }}</textarea></div><div class="field"><label>กิจกรรมการเรียนรู้</label><textarea name="activities" placeholder="ถ้าเว้นว่าง ระบบจะใช้กิจกรรมจากแม่แบบที่เลือก">{{ request.form.get('activities','') }}</textarea></div><div class="field"><label>สื่อและอุปกรณ์</label><textarea name="materials">{{ request.form.get('materials','') }}</textarea></div><div class="field"><label>การวัดและประเมินผล</label><textarea name="assessment">{{ request.form.get('assessment','') }}</textarea></div><div class="actions"><button class="primary">บันทึกแผน</button><a class="btn secondary" href="{{ url_for('ai_studio') }}">ให้ AI ช่วยร่าง</a></div></form></div>'''
    return page('สร้างแผนการสอน', body)


@app.route('/plans/search')
@login_required
def search_plans():
    q=request.args.get('q','').strip()
    query=LessonPlan.query.filter_by(user_id=current_user().id)
    if q: query=query.filter(or_(LessonPlan.topic.ilike(f'%{q}%'), LessonPlan.subject.ilike(f'%{q}%'), LessonPlan.grade.ilike(f'%{q}%')))
    plans=query.order_by(LessonPlan.created_at.desc()).all()
    body=r'''<div class="card"><h2>ค้นหาและคัดลอกแผน</h2><form method="get" class="actions"><div style="flex:1;min-width:200px"><input name="q" value="{{ q }}" placeholder="ค้นหาวิชา หัวข้อ หรือระดับชั้น"></div><button class="primary">ค้นหา</button></form>{% for p in plans %}<div class="lesson"><h4>{{ p.topic }}</h4><small>{{ p.subject }} · {{ p.grade }} · {{ p.created_at.strftime('%d/%m/%Y') }}</small><div class="actions" style="margin-top:10px"><a class="btn secondary" href="{{ url_for('view_plan',plan_id=p.id) }}">เปิดแผน</a><form method="post" action="{{ url_for('copy_plan',plan_id=p.id) }}"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><button class="primary">คัดลอกแผน</button></form></div></div>{% else %}<div class="empty">ไม่พบแผนที่ตรงกับคำค้น</div>{% endfor %}</div>'''
    return page('ค้นหาแผน', body, plans=plans, q=q)


@app.route('/plans/<int:plan_id>/copy', methods=['POST'])
@login_required
def copy_plan(plan_id):
    p=owned_plan(plan_id)
    clone=LessonPlan(user_id=current_user().id, subject=p.subject, grade=p.grade, topic=(p.topic+' (สำเนา)')[:180], duration=p.duration, objectives=p.objectives, activities=p.activities, materials=p.materials, assessment=p.assessment)
    db.session.add(clone); db.session.commit(); flash('คัดลอกแผนแล้ว คุณแก้ไขสำเนาได้จากแผนใหม่'); return redirect(url_for('view_plan', plan_id=clone.id))


@app.route('/plans/<int:plan_id>')
@login_required
def view_plan(plan_id):
    plan=owned_plan(plan_id)
    body=r'''<div class="card"><div class="welcome"><div><span class="tag">แผนการสอน</span><h2 style="margin-top:10px">{{ plan.topic }}</h2><p>{{ plan.subject }} · {{ plan.grade }} · {{ plan.duration }}</p></div><div class="actions no-print"><a class="btn secondary" href="{{ url_for('search_plans') }}">คลังแผน</a><form method="post" action="{{ url_for('copy_plan',plan_id=plan.id) }}"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><button class="secondary">คัดลอก</button></form><button class="primary" onclick="window.print()">พิมพ์ / บันทึก PDF</button></div></div><div class="lesson"><h3>จุดประสงค์การเรียนรู้</h3><p>{{ plan.objectives or 'ยังไม่ได้ระบุ' }}</p></div><div class="lesson"><h3>กิจกรรมการเรียนรู้</h3><p>{{ plan.activities or 'ยังไม่ได้ระบุ' }}</p></div><div class="lesson"><h3>สื่อและอุปกรณ์</h3><p>{{ plan.materials or 'ยังไม่ได้ระบุ' }}</p></div><div class="lesson"><h3>การวัดและประเมินผล</h3><p>{{ plan.assessment or 'ยังไม่ได้ระบุ' }}</p></div><p class="small">สร้างเมื่อ {{ plan.created_at.strftime('%d/%m/%Y %H:%M') }}</p></div>'''
    return page('รายละเอียดแผน', body, plan=plan)


@app.route('/plans/<int:plan_id>/delete', methods=['POST'])
@login_required
def delete_plan(plan_id):
    p=owned_plan(plan_id); db.session.delete(p); db.session.commit(); flash('ลบแผนการสอนแล้ว'); return redirect(url_for('dashboard'))


@app.route('/ai', methods=['GET', 'POST'])
@login_required
def ai_studio():
    generated = None
    kind = request.form.get('kind', 'plan')
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        grade = request.form.get('grade', '').strip()
        topic = request.form.get('topic', '').strip()
        duration = request.form.get('duration', '50 นาที')
        if not topic:
            flash('กรุณากรอกหัวข้อบทเรียนก่อน', 'error')
        else:
            generated, _ = build_free_draft(kind, subject, grade, topic, duration)
    body = r'''<div class="card"><h2>✨ Teaching Studio · ใช้ฟรี</h2><p class="sub">สร้างร่างแผนการสอนหรือโครงคำถามจากแม่แบบภายในแอป ไม่เรียก OpenAI/Gemini API และไม่มีค่า API แต่ไม่ใช่ AI ที่สร้างเนื้อหาใหม่ได้อย่างอิสระ</p><form method="post"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><div class="field"><label>ต้องการสร้างอะไร</label><select name="kind"><option value="plan" {% if kind=='plan' %}selected{% endif %}>ร่างแผนการสอน</option><option value="quiz" {% if kind=='quiz' %}selected{% endif %}>โครงแบบทดสอบ</option></select></div><div class="layout"><div class="field"><label>วิชา</label><input name="subject" value="{{ request.form.get('subject','') }}" placeholder="เช่น ภาษาไทย"></div><div class="field"><label>ระดับชั้น</label><input name="grade" value="{{ request.form.get('grade','') }}" placeholder="เช่น ป.5"></div></div><div class="field"><label>หัวข้อบทเรียน *</label><input name="topic" required value="{{ request.form.get('topic','') }}" placeholder="เช่น คำควบกล้ำ"></div><div class="field"><label>เวลาเรียน</label><select name="duration">{% for d in ['50 นาที','60 นาที','90 นาที','100 นาที'] %}<option {% if request.form.get('duration','50 นาที')==d %}selected{% endif %}>{{ d }}</option>{% endfor %}</select></div><button class="primary">สร้างร่างจากแม่แบบฟรี</button></form>{% if generated %}<div class="lesson"><div class="split"><h3>ร่างเนื้อหา</h3><button class="secondary no-print" onclick="window.print()">พิมพ์ / บันทึก PDF</button></div><p style="white-space:pre-wrap;line-height:1.8">{{ generated }}</p><p class="small">คัดลอกผลลัพธ์ไปปรับแก้ หรือบันทึกในหน้าสร้างแผน/แบบทดสอบ เนื้อหานี้ยังไม่ได้บันทึกอัตโนมัติ</p></div>{% endif %}</div>'''
    return page('Teaching Studio', body, generated=generated, kind=kind)


@app.route('/quizzes')
@login_required
def quiz_list():
    quizzes=Quiz.query.filter_by(user_id=current_user().id).order_by(Quiz.created_at.desc()).all()
    body=r'''<div class="welcome"><div><h2>คลังแบบทดสอบ</h2><p>เก็บข้อสอบและเฉลยของคุณในที่เดียว</p></div><a class="btn primary" href="{{ url_for('quiz_new') }}">＋ สร้างแบบทดสอบ</a></div><div class="card">{% for q in quizzes %}<div class="lesson"><h4>{{ q.title }}</h4><small>{{ q.subject }} · {{ q.grade }} · {{ q.created_at.strftime('%d/%m/%Y') }}</small><div class="actions" style="margin-top:10px"><a class="btn secondary" href="{{ url_for('quiz_view',quiz_id=q.id) }}">เปิด / พิมพ์</a><form method="post" action="{{ url_for('quiz_delete',quiz_id=q.id) }}"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><button class="danger">ลบ</button></form></div></div>{% else %}<div class="empty">ยังไม่มีแบบทดสอบ สร้างข้อสอบชุดแรกได้เลย</div>{% endfor %}</div>'''
    return page('คลังแบบทดสอบ', body, quizzes=quizzes)


@app.route('/quizzes/new', methods=['GET','POST'])
@login_required
def quiz_new():
    if request.method=='POST':
        title=request.form.get('title','').strip(); subject=request.form.get('subject','').strip(); grade=request.form.get('grade','').strip(); questions=request.form.get('questions','').strip(); answers=request.form.get('answer_key','').strip()
        if not title or not questions: flash('กรุณากรอกชื่อชุดและเนื้อหาข้อสอบ', 'error')
        else:
            q=Quiz(user_id=current_user().id,title=title[:180],subject=subject[:120],grade=grade[:80],questions=questions,answer_key=answers); db.session.add(q); db.session.commit(); return redirect(url_for('quiz_view',quiz_id=q.id))
    body=r'''<div class="card"><h2>สร้างแบบทดสอบ / ใบงาน</h2><p class="sub">พิมพ์ข้อสอบเอง หรือใช้ Teaching Studio สร้างโครงคำถามแล้วนำมาวางที่นี่</p><form method="post"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><div class="field"><label>ชื่อชุดแบบทดสอบ *</label><input name="title" required maxlength="180" placeholder="เช่น แบบทดสอบเรื่องเศษส่วน"></div><div class="layout"><div class="field"><label>วิชา</label><input name="subject"></div><div class="field"><label>ระดับชั้น</label><input name="grade"></div></div><div class="field"><label>ข้อสอบ / ใบงาน *</label><textarea name="questions" required style="min-height:220px" placeholder="1. ...\nก. ... ข. ... ค. ... ง. ..."></textarea></div><div class="field"><label>เฉลย (แยกเก็บและเลือกซ่อนตอนพิมพ์ได้)</label><textarea name="answer_key" placeholder="1. ข — เพราะ..."></textarea></div><button class="primary">บันทึกแบบทดสอบ</button></form></div>'''
    return page('สร้างแบบทดสอบ', body)


@app.route('/quizzes/<int:quiz_id>')
@login_required
def quiz_view(quiz_id):
    q=Quiz.query.filter_by(id=quiz_id,user_id=current_user().id).first_or_404()
    body=r'''<div class="card"><div class="welcome"><div><span class="tag">แบบทดสอบ / ใบงาน</span><h2 style="margin-top:10px">{{ q.title }}</h2><p>{{ q.subject }} · {{ q.grade }}</p></div><div class="actions no-print"><button class="primary" onclick="window.print()">พิมพ์ / บันทึก PDF</button><button class="secondary" onclick="document.getElementById('answers').classList.toggle('hidden')">แสดง/ซ่อนเฉลย</button></div></div><div class="lesson"><h3>ข้อสอบ / ใบงาน</h3><p style="white-space:pre-wrap;line-height:1.8">{{ q.questions }}</p></div><div id="answers" class="lesson"><h3>เฉลยสำหรับครู</h3><p style="white-space:pre-wrap;line-height:1.8">{{ q.answer_key or 'ยังไม่ได้ระบุเฉลย' }}</p></div><style>.hidden{display:none}@media print{#answers{display:block!important}}</style></div>'''
    return page('ดูแบบทดสอบ', body, q=q)


@app.route('/quizzes/<int:quiz_id>/delete', methods=['POST'])
@login_required
def quiz_delete(quiz_id):
    q=Quiz.query.filter_by(id=quiz_id,user_id=current_user().id).first_or_404(); db.session.delete(q); db.session.commit(); flash('ลบแบบทดสอบแล้ว'); return redirect(url_for('quiz_list'))


@app.route('/calendar', methods=['GET','POST'])
@login_required
def calendar():
    if request.method=='POST':
        title=request.form.get('title','').strip(); raw_date=request.form.get('due_date','').strip(); notes=request.form.get('notes','').strip()
        if not title: flash('กรุณากรอกชื่องาน', 'error')
        else:
            due=None
            if raw_date:
                try: due=date.fromisoformat(raw_date)
                except ValueError: flash('รูปแบบวันที่ไม่ถูกต้อง', 'error'); return redirect(url_for('calendar'))
            t=TeachingTask(user_id=current_user().id,title=title[:180],due_date=due,notes=notes); db.session.add(t); db.session.commit(); flash('เพิ่มงานในปฏิทินแล้ว'); return redirect(url_for('calendar'))
    tasks=TeachingTask.query.filter_by(user_id=current_user().id).order_by(TeachingTask.due_date.asc(),TeachingTask.created_at.desc()).all()
    body=r'''<div class="card"><h2>🗓️ ปฏิทินการสอนและติดตามงาน</h2><p class="sub">เพิ่มกำหนดส่ง แล้วทำเครื่องหมายเมื่อเสร็จงาน</p><form method="post"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><div class="layout"><div class="field"><label>ชื่องาน *</label><input name="title" required placeholder="เช่น เตรียมใบงานบทที่ 2"></div><div class="field"><label>กำหนดส่ง</label><input type="date" name="due_date"></div></div><div class="field"><label>รายละเอียด</label><textarea name="notes" placeholder="หมายเหตุหรือสิ่งที่ต้องเตรียม"></textarea></div><button class="primary">＋ เพิ่มงาน</button></form></div><div class="card" style="margin-top:16px"><h3>รายการงาน</h3>{% for t in tasks %}<div class="lesson"><div class="split"><div><h4>{{ t.title }}</h4><small>กำหนดส่ง: {{ t.due_date.strftime('%d/%m/%Y') if t.due_date else 'ไม่กำหนด' }} · <span class="tag">{{ t.status }}</span></small>{% if t.notes %}<p>{{ t.notes }}</p>{% endif %}</div><div class="actions">{% if t.status=='ยังไม่เสร็จ' %}<form method="post" action="{{ url_for('task_done',task_id=t.id) }}"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><button class="primary">ทำเสร็จแล้ว</button></form>{% else %}<form method="post" action="{{ url_for('task_reopen',task_id=t.id) }}"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><button class="secondary">เปิดงานอีกครั้ง</button></form>{% endif %}<form method="post" action="{{ url_for('task_delete',task_id=t.id) }}"><input type="hidden" name="csrf_token" value="{{ csrf_token() }}"><button class="danger">ลบ</button></form></div></div></div>{% else %}<div class="empty">ยังไม่มีงาน เพิ่มงานแรกได้จากแบบฟอร์มด้านบน</div>{% endfor %}</div>'''
    return page('ปฏิทินและงาน', body, tasks=tasks)


@app.route('/tasks/<int:task_id>/done', methods=['POST'])
@login_required
def task_done(task_id):
    t=TeachingTask.query.filter_by(id=task_id,user_id=current_user().id).first_or_404(); t.status='เสร็จแล้ว'; db.session.commit(); return redirect(url_for('calendar'))


@app.route('/tasks/<int:task_id>/reopen', methods=['POST'])
@login_required
def task_reopen(task_id):
    t=TeachingTask.query.filter_by(id=task_id,user_id=current_user().id).first_or_404(); t.status='ยังไม่เสร็จ'; db.session.commit(); return redirect(url_for('calendar'))


@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def task_delete(task_id):
    t=TeachingTask.query.filter_by(id=task_id,user_id=current_user().id).first_or_404(); db.session.delete(t); db.session.commit(); return redirect(url_for('calendar'))


@app.errorhandler(404)
def not_found(_error):
    return page('ไม่พบหน้า', '<div class="card"><h2>ไม่พบหน้าที่ต้องการ</h2><a class="btn primary" href="/">กลับหน้าหลัก</a></div>'), 404


with app.app_context():
    # Creates only missing tables; does not drop existing users or lesson plans.
    db.create_all()

if __name__ == '__main__':
    app.run(debug=False)
