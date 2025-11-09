from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import bcrypt

def home():
    return redirect('/login')

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# -------------------- Models --------------------

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    # Admin/approval fields
    is_admin = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='Approved')  # 'Approved' or 'Pending'

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

    math_practical = db.Column(db.Integer, default=0)
    physics_practical = db.Column(db.Integer, default=0)
    chemistry_practical = db.Column(db.Integer, default=0)
    cs_practical = db.Column(db.Integer, default=0)
    electronics_practical = db.Column(db.Integer, default=0)

    math_written = db.Column(db.Integer, default=0)
    physics_written = db.Column(db.Integer, default=0)
    chemistry_written = db.Column(db.Integer, default=0)
    cs_written = db.Column(db.Integer, default=0)
    electronics_written = db.Column(db.Integer, default=0)

    def total_score(self):
        return (
            self.math_practical + self.math_written +
            self.physics_practical + self.physics_written +
            self.chemistry_practical + self.chemistry_written +
            self.cs_practical + self.cs_written +
            self.electronics_practical + self.electronics_written
        )

    def percentage(self):
        return (self.total_score() / 500) * 100

    def grade(self):
        p = self.percentage()
        if p >= 90:
            return 'A'
        elif p >= 80:
            return 'B'
        elif p >= 70:
            return 'C'
        elif p >= 60:
            return 'D'
        elif p >= 50:
            return 'E'
        else:
            return 'Fail'

class RecheckQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    student = db.relationship('Student', backref='recheck_queries')

# -------------------- Helpers --------------------

def ensure_schema():
    """
    Lightweight migration for existing SQLite DB:
    adds Teacher.is_admin and Teacher.status if missing.
    """
    try:
        cols = db.session.execute(text("PRAGMA table_info(teacher);")).fetchall()
        colnames = {c[1] for c in cols}
        if 'is_admin' not in colnames:
            db.session.execute(text("ALTER TABLE teacher ADD COLUMN is_admin BOOLEAN DEFAULT 0;"))
        if 'status' not in colnames:
            db.session.execute(text("ALTER TABLE teacher ADD COLUMN status VARCHAR(20) DEFAULT 'Approved';"))
        db.session.commit()
    except Exception:
        db.session.rollback()

def is_logged_in(role=None):
    ut = session.get('user_type')
    if role:
        return ut == role
    return ut is not None

# -------------------- Routes --------------------
@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        # Teacher / Admin login (lookup by username only, then verify hash)
        teacher = Teacher.query.filter_by(username=username).first()
        if teacher:
            # verify hashed password
            if bcrypt.checkpw(password.encode('utf-8'), teacher.password.encode('utf-8')):
                if teacher.is_admin:
                    session['user_type'] = 'teacher'
                    session['teacher_id'] = teacher.id
                    session['is_admin'] = True
                    return redirect('/admin_dashboard')
                if teacher.status != 'Approved':
                    msg = 'Your teacher account is not approved yet by admin.'
                else:
                    session['user_type'] = 'teacher'
                    session['teacher_id'] = teacher.id
                    session['is_admin'] = False
                    return redirect('/teacher_dashboard')
            else:
                msg = 'Invalid login!'

        # Student login (lookup by roll_number only, then verify hash)
        if not msg:
            student = Student.query.filter_by(roll_number=username).first()
            if student:
                if bcrypt.checkpw(password.encode('utf-8'), student.password.encode('utf-8')):
                    session['user_type'] = 'student'
                    session['student_id'] = student.id
                    return redirect('/student_dashboard')
                else:
                    msg = 'Invalid login!'

        if not msg:
            msg = 'Invalid login!'
    return render_template('login.html', msg=msg)


# ---------- Registration flow ----------


@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register/student', methods=['GET', 'POST'])
def register_student():
    msg = ''
    if request.method == 'POST':
        name = request.form['name'].strip()
        roll = request.form['roll_number'].strip()
        password = bcrypt.hashpw(request.form['password'].strip().encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()

        exists = Student.query.filter_by(roll_number=roll).first()
        if exists:
            msg = 'Roll number already registered.'
        else:
            s = Student(name=name, roll_number=roll, password=password, email=email, phone=phone)
            db.session.add(s)
            db.session.commit()
            flash('Student registered successfully. You can log in now.')
            return redirect(url_for('login'))
    return render_template('register_student.html', msg=msg)

@app.route('/register/teacher', methods=['GET', 'POST'])
def register_teacher():
    msg = ''
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = bcrypt.hashpw(request.form['password'].strip().encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


        exists = Teacher.query.filter_by(username=username).first()
        if exists:
            msg = 'Username already taken.'
        else:
            t = Teacher(username=username, password=password, is_admin=False, status='Pending')
            db.session.add(t)
            db.session.commit()
            flash('Teacher registration submitted. Wait for admin approval.')
            return redirect(url_for('login'))
    return render_template('register_teacher.html', msg=msg)

# ---------- Dashboards ----------

@app.route('/teacher_dashboard')
def teacher_dashboard():
    # Only non-admin teachers here
    if not is_logged_in('teacher') or session.get('is_admin'):
        return redirect('/login')
    students = Student.query.all()
    queries = RecheckQuery.query.order_by(RecheckQuery.created_at.desc()).all()
    return render_template('teacher_dashboard.html', students=students, queries=queries)

@app.route('/admin_dashboard')
def admin_dashboard():
    # Only admin here
    if not is_logged_in('teacher') or not session.get('is_admin'):
        return redirect('/login')
    pending_teachers = Teacher.query.filter(Teacher.is_admin == False, Teacher.status == 'Pending').all()
    return render_template('admin_dashboard.html', pending_teachers=pending_teachers)

@app.route('/student_dashboard')
def student_dashboard():
    if not is_logged_in('student'):
        return redirect('/login')
    student = Student.query.get(session['student_id'])
    recent_queries = (RecheckQuery.query
                      .filter_by(student_id=student.id)
                      .order_by(RecheckQuery.created_at.desc())
                      .limit(5).all())
    return render_template('student_dashboard.html', student=student, recent_queries=recent_queries)

# ---------- Recheck ----------

@app.route('/recheck_query', methods=['POST'])
def recheck_query():
    if not is_logged_in('student'):
        return redirect('/login')
    subject = request.form.get('subject', '').strip()
    sid = session.get('student_id')
    if subject and sid:
        rq = RecheckQuery(student_id=sid, subject=subject)
        db.session.add(rq)
        db.session.commit()
        flash('Your rechecking request was sent to the teacher.')
    return redirect('/student_dashboard')

@app.route('/recheck_query/<int:qid>/<status>')
def update_recheck_status(qid, status):
    # Only non-admin teacher should manage student queries
    if not is_logged_in('teacher') or session.get('is_admin'):
        return redirect('/login')
    q = RecheckQuery.query.get_or_404(qid)
    if status in ('Pending', 'Reviewed', 'Resolved'):
        q.status = status
        db.session.commit()
    return redirect('/teacher_dashboard')

# ---------- Admin: approve/reject teachers ----------

@app.route('/approve_teacher/<int:tid>')
def approve_teacher(tid):
    if not is_logged_in('teacher') or not session.get('is_admin'):
        return redirect('/login')
    t = Teacher.query.get_or_404(tid)
    t.status = 'Approved'
    db.session.commit()
    flash(f"Approved teacher: {t.username}")
    return redirect('/admin_dashboard')

@app.route('/reject_teacher/<int:tid>')
def reject_teacher(tid):
    if not is_logged_in('teacher') or not session.get('is_admin'):
        return redirect('/login')
    t = Teacher.query.get_or_404(tid)
    db.session.delete(t)
    db.session.commit()
    flash("Teacher registration rejected & removed.")
    return redirect('/admin_dashboard')

# ---------- Legacy student edit (route kept, no button shown) ----------




@app.route('/edit_student/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    if not is_logged_in('teacher') or session.get('is_admin'):
        return redirect('/login')
    student = Student.query.get(id)
    msg = ''
    if request.method == 'POST':
        student.name = request.form['name']
        student.roll_number = request.form['roll_number']
        student.password = request.form['password']
        student.email = request.form['email']
        student.phone = request.form['phone']

        student.math_practical = int(request.form.get('math_practical', 0))
        student.physics_practical = int(request.form.get('physics_practical', 0))
        student.chemistry_practical = int(request.form.get('chemistry_practical', 0))
        student.cs_practical = int(request.form.get('cs_practical', 0))
        student.electronics_practical = int(request.form.get('electronics_practical', 0))

        student.math_written = int(request.form.get('math_written', 0))
        student.physics_written = int(request.form.get('physics_written', 0))
        student.chemistry_written = int(request.form.get('chemistry_written', 0))
        student.cs_written = int(request.form.get('cs_written', 0))
        student.electronics_written = int(request.form.get('electronics_written', 0))

        db.session.commit()
        return redirect('/teacher_dashboard')
    return render_template('edit_student.html', student=student, msg=msg)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# -------------------- Bootstrap --------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        ensure_schema()

        admin = Teacher.query.filter_by(username='admin').first()
        if not admin:
            hashed = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            admin = Teacher(username='admin', password=hashed, is_admin=True, status='Approved')
            db.session.add(admin)
            db.session.commit()
            print("Default admin added: username=admin, password=admin123")
        else:
            if admin.username == 'admin':
                admin.is_admin = True
                admin.status = 'Approved'
                db.session.commit()

    app.run(debug=True)
