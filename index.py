from flask import Flask, flash, redirect, render_template, request, session, url_for, make_response
# from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime
import math
import psycopg2
import os
import time

from utils.decorators import logout_required, login_required

# Configure application
app = Flask(__name__)
app.secret_key = os.environ.get("cgpaSecret")



# Initialize the serializer for signed cookies
serializer = URLSafeTimedSerializer(app.secret_key)

# Setup Postgresql
def connect():
    conn = psycopg2.connect(database="verceldb", 
                        user="default",
                        password=os.environ.get("cgpaDBPass"),
                        host="ep-super-term-91068119-pooler.eu-central-1.postgres.vercel-storage.com",
                        port="5432")
    cur = conn.cursor()
    return cur, conn

semesters = {"Harmattan", "Rain"}
year = datetime.today().year
sessions = list(range(year, year - 49, -1))

def get_courses(id):
    # Get list of user's courses
    cur.execute("SELECT course_code FROM courses WHERE user_id = %s", (id,))
    all_courses = cur.fetchall()
    return all_courses

def get_user_data(request):
    course_code = request.form.get("course_Code").upper()
    credit_unit = request.form.get("credit_unit")
    check = credit_unit.isdecimal()
    letter_grade = request.form.get("letter_grade").upper()
    exam_session = request.form.get("session")
    semester = request.form.get("semester")

    return course_code, credit_unit, check, letter_grade, exam_session, semester


def get_grade_point(letter_grade):
    # Assign grade point to each letter grade
    if letter_grade == 'A':
        grade_point = 5
    elif letter_grade == 'B':
        grade_point = 4
    elif letter_grade == 'C':
        grade_point = 3
    elif letter_grade == 'D':
        grade_point = 2
    elif letter_grade == 'E':
        grade_point = 1
    else:
        grade_point = 0

    return grade_point

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route('/set_cookie')
def set_cookie():
    user_id = request.args.get('data')
    # Set session data
    session['user_id'] = user_id  # Replace with your user ID or relevant data

    # Serialize session data and sign the cookie
    serialized_data = serializer.dumps(dict(session))
    response = make_response('Cookie set')
    response.set_cookie('session_cookie', value=serialized_data, httponly=True, secure=True)
    
    return redirect("/")

# Variable to store last activity time
last_activity_time = 0

# Function to check and reset session timeout
@app.before_request
def check_session_timeout():
    global last_activity_time
    if 'user_id' in session:
        # Get the last activity time from the session
        if last_activity_time == 0:
            last_activity_time = time.time()
        else:
            # Calculate the time elapsed since the last activity
            elapsed_time = time.time() - last_activity_time
            # Check if the elapsed time exceeds 5 minutes (300 seconds)
            if elapsed_time > 3600:
                # Clear the session and log the user out
                session.clear()
                return redirect(url_for('logout'))
        last_activity_time = time.time()


@app.before_request
def update_last_activity():
    global last_activity_time
    if 'user_id' in session:
        last_activity_time = time.time()

@app.route("/")
@login_required
def index():
    id = session["user_id"]
    cur, conn = connect()
    """Show Courses informations"""

    # Calculate CGPA
    cur.execute("SELECT SUM(quality_point) / SUM(credit_unit) FROM courses WHERE user_id = %s", (id,))
    cgpa = cur.fetchone()
    
    if cgpa[0] is None:
        flash("Please add course", "info")
        return redirect(url_for('add'))

    cgpa_ = cgpa[0]
    # for value in cgpa:
    #     cgpa_ = value
    
    cgpa_ = math.ceil(cgpa_ * 100) / 100

    # Get list of sessions fro user
    sessions = list()
    cur.execute("SELECT session FROM courses WHERE user_id = %s ORDER BY session", (id,))
    all_sessions = cur.fetchall()
    for session_ in all_sessions:
        if session_ in sessions:
            continue
        else:
            sessions.append(session_)

    # Get total quality point for each session
    tqp = list()
    totalQualityPoints = list()

    for session_ in sessions:
        cur.execute("SELECT SUM(quality_point) FROM courses WHERE session = %s AND user_id = %s", (session_[0], id))
        tqp.append(cur.fetchone())

    for total in tqp:
        totalQualityPoints.append(total[0])

    # Get total credit unit for each session
    tcu = list()
    totalCreditUnits = list()
    for session_ in sessions:
        cur.execute("SELECT SUM(credit_unit) FROM courses WHERE session = %s AND user_id = %s", (session_[0], id))
        tcu.append(cur.fetchone()) 

    for total in tcu:
        totalCreditUnits.append(total[0])
    
    length = len(sessions)

    # Get list of courses
    courses_sessional = list()

    for seSsion in sessions:
        cur.execute(
            "SELECT * FROM courses WHERE user_id = %s AND session = %s ORDER BY semester, course_code", (id, seSsion[0]))
        courses_sessional.append(cur.fetchall()) 
    
    # close the cursor and connection 
    cur.close() 
    conn.close()
    return render_template("/index.html", length = length, sessions = sessions, quality_points = totalQualityPoints,\
         credit_units = totalCreditUnits, cgpa = cgpa_, results = courses_sessional)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    id = session["user_id"]
    cur, conn = connect()
    """Add Course"""
    semesters = {"Harmattan", "Rain"}
    year = datetime.today().year
    sessions = list(range(year, year - 49, -1))
    if request.method == "POST":
        # Get data from user
        course_code, credit_unit, check, letter_grade, exam_session, semester = get_user_data(request)

        # Form Validation
        if not course_code or not credit_unit or not letter_grade or not exam_session or not semester:
            flash("Please fill the fields correctly. All fields are required!", "error")
            return render_template("/add.html", semesters=semesters, sessions=sessions, course_code=course_code,\
                credit_unit=credit_unit, letter_grade=letter_grade), 400
        
        if not check or credit_unit == '0':
            flash("Credit unit must be a positive integer", "error")
            return render_template("/add.html", semesters=semesters, sessions=sessions, course_code=course_code,\
                credit_unit=credit_unit, letter_grade=letter_grade), 400

        cur.execute("SELECT course_code FROM courses WHERE user_id = %s AND course_code = %s", (id, course_code))
        courses = cur.fetchall()

        if courses:
            flash("""Course already added!! To edit, please use the edit page.""", "warning")
            return render_template("/add.html", semesters=semesters, sessions=sessions), 400
        
        if letter_grade not in list(map(chr, range(65, 70))) or len(letter_grade) != 1:
            flash("Letter grade must be a single character A-F", "info")
            return render_template("/add.html", semesters=semesters, sessions=sessions), 400
        
        credit_unit = float(credit_unit)

        grade_point = get_grade_point(letter_grade)

        # Calculate the quality point for the course
        quality_point = credit_unit * grade_point

        # Add course to the database
        cur.execute("INSERT INTO courses (user_id, course_code, credit_unit, letter_grade, grade_point, \
            quality_point, semester, session) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                  (id, course_code, credit_unit, letter_grade, grade_point, quality_point, semester, exam_session))
        flash("Course added! To check GPA, click the calculate button", "success")

        # commit the changes 
        conn.commit() 
        
        # close the cursor and connection 
        cur.close() 
        conn.close()
        return render_template("/add.html", semesters=semesters, sessions=sessions), 201
    else:
        return render_template("/add.html", semesters=semesters, sessions=sessions), 200


@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    id = session["user_id"]
    cur, conn = connect()
    """Edit Course"""
    # Get list of user's courses
    all_courses = get_courses()

    if request.method == "POST":
        
        # Get data from user
        course_code, credit_unit, check, letter_grade, exam_session, semester = get_user_data(request)

        # Form Validation
        if not course_code or not credit_unit or not letter_grade or not exam_session or not semester:
            flash("Please fill the fields correctly. All fields are required!", "error")
            return render_template("/edit.html", all_courses=all_courses, semesters=semesters, sessions=sessions,\
                credit_unit=credit_unit, letter_grade=letter_grade), 400
        
        if not check or credit_unit == '0':
            flash("Credit unit must be a positive integer", "error")
            return render_template("/edit.html", all_courses=all_courses, semesters=semesters, sessions=sessions,\
                credit_unit=credit_unit, letter_grade=letter_grade), 400
        
        # Convert to upper case
        course_code = course_code.upper()

        values = list()
        for i in all_courses:
            values.append(i[0])

        if course_code not in values:
            flash("Course does not exist! Please add course through the add page.", "error")
            return render_template("/edit.html", all_courses=all_courses, semesters=semesters, sessions=sessions,\
                credit_unit=credit_unit, letter_grade=letter_grade), 400
        
        if letter_grade not in list(map(chr, range(65, 70))) or len(letter_grade) != 1:
            flash("Letter grade must be a single character A-F", "info")
            return render_template("/edit.html", all_courses=all_courses, semesters=semesters, sessions=sessions,\
                credit_unit=credit_unit, letter_grade=letter_grade), 400
        
        credit_unit = float(credit_unit)

        grade_point = get_grade_point(letter_grade)

        # Calculate the quality point for the course
        quality_point = credit_unit * grade_point
        
        # Update database
        cur.execute("UPDATE courses SET credit_unit = %s, letter_grade = %s, grade_point = %s, quality_point = %s, semester = %s, \
            session = %s WHERE user_id = %s AND course_code = %s",
                    (credit_unit, letter_grade, grade_point, quality_point, semester, exam_session, id, course_code))

        # commit the changes 
        conn.commit() 
        
        # close the cursor and connection 
        cur.close() 
        conn.close()
        flash("Course details edited", "success")
        return redirect("/")

    else:
        return render_template("/edit.html", all_courses=all_courses, semesters=semesters, sessions=sessions), 200


@app.route("/delete", methods=["GET", "POST"])
def delete():
    id = session["user_id"]
    cur, conn = connect()
    """Delete course"""

    # Get list of user's courses
    all_courses = get_courses(id)

    if request.method == "POST":

        # Get data from user
        course_code = request.form.get("course_Code")
    
        if not course_code:
            flash("Please enter the course code.", "error")
            return render_template("/delete.html", all_courses=all_courses), 400
        
        values = list()
        for i in all_courses:
            values.append(i[0])

        if course_code not in values:
            flash("Course does not exist!!", "error")
            return render_template("/delete.html", all_courses=all_courses), 400

        cur.execute("DELETE FROM courses WHERE user_id = %s AND course_code = %s", (id, course_code))
        
        # commit the changes 
        conn.commit() 
        
        # close the cursor and connection 
        cur.close() 
        conn.close()
        flash("Course deleted", "success")
        return redirect("/delete")
    else:
        return render_template("/delete.html", all_courses=all_courses), 200


@app.route("/login", methods=["GET", "POST"])
def login():
    cur, conn = connect()
    """Log user in"""

    # Forget any user_id
    session.clear()

    # Create a response to clear the cookie
    response = make_response('Logged out')
    response.set_cookie('session_cookie', '', expires=0)

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Enter username", "error")
            return render_template("/login.html"), 400

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Enter password", "error")
            return render_template("/login.html"), 400

        # Query database for username
        cur.execute("SELECT * FROM users WHERE username = %s", (request.form.get("username"),))
        rows = cur.fetchall()

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            flash("Invalid Username or password", "error")
            return render_template("/login.html"), 400
        
        # close the cursor and connection 
        cur.close() 
        conn.close()

        # Redirect to set cookies
        return redirect(url_for('set_cookie', data=rows[0][0]))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    cur, conn = connect()
    """Register user"""
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
         # Check username in database
        cur.execute("SELECT * FROM users WHERE username = %s", (request.form.get("username"),))
        name = cur.fetchall()
        password = request.form.get("password")

        # Ensure username is inputted
        if not request.form.get("username"):
            flash("Please enter username", "warning")
            return render_template("/register.html"), 400
        
        # Check if username already exists
        elif name:
            flash("Username already exist!", "error")
            return render_template("/register.html"), 400      

        # Ensure password is inputted
        if not password:
            flash("Please enter password", "warning")
            return render_template("/register.html"), 400
        
        # Ensure confirm password is inputted
        elif not request.form.get("confirmation"):
            flash("Re-enter password", "warning")
            return render_template("/register.html"), 400
        
        # Ensures passwords match
        if password != request.form.get("confirmation"):
            flash("Passwords do not match!", "error")
            return render_template("/register.html"), 400
        
        cur.execute("INSERT INTO users (username, hash) VALUES(%s, %s)", (request.form.get("username"),
                   generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)))

        # commit the changes 
        conn.commit() 
        
        # close the cursor and connection 
        cur.close() 
        conn.close()
        return redirect("/login")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html"), 200


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Create a response to clear the cookie
    response = make_response('Logged out')
    response.set_cookie('session_cookie', '', expires=0) 
    
    # Redirect user to login form
    return redirect("/login")