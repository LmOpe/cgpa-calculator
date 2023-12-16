from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import math

from utils.decorators import logout_required, login_required

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///cgpa.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show Courses informations"""
    id = session["user_id"]
    semesters = {"Harmattan", "Rain"}
    year = datetime.today().year
    sessions = list(range(year, year - 49, -1))

    # Calculate CGPA
    cgpa = db.execute("SELECT SUM(quality_point) / SUM(credit_unit) FROM courses WHERE user_id = ?", id)
    cgpa = cgpa[0].values()
    for value in cgpa:
        cgpa_ = value
    
    if cgpa_ is None:
        flash("Please add course", "info")
        return render_template("/add.html", semesters=semesters, sessions=sessions)

    cgpa_ = math.ceil(cgpa_ * 100) / 100

    # Get list of sessions fro user
    sessions = list()
    all_sessions = db.execute("SELECT session FROM courses WHERE user_id = ? ORDER BY session", id)
    for session_ in all_sessions:
        if session_ in sessions:
            continue
        else:
            sessions.append(session_)

    # Get total quality point for each session
    tqp = list()
    totalQualityPoints = list()

    for session_ in sessions:
        tqp.append(db.execute("SELECT SUM(quality_point) FROM courses WHERE session = ? AND user_id = ?", session_["session"], id))

    for total in tqp:

        total_ = total[0].values()
        for value in total_:
            totalQualityPoints.append(value)

    # Get total credit unit for each session
    tcu = list()
    totalCreditUnits = list()
    for session_ in sessions:
        tcu.append(db.execute("SELECT SUM(credit_unit) FROM courses WHERE session = ? AND user_id = ?", session_["session"], id)) 

    for total in tcu:

        total_ = total[0].values()
        for value in total_:
            totalCreditUnits.append(value)
    
    length = len(sessions)

    # Get list of courses
    courses_sessional = list()

    for seSsion in sessions:
        courses_sessional.append(db.execute(
            "SELECT * FROM courses WHERE user_id = ? AND session = ? ORDER BY semester, course_code", id, seSsion["session"]))

    return render_template("/index.html", length = length, sessions = sessions, quality_points = totalQualityPoints, credit_units = totalCreditUnits, cgpa = cgpa_, results = courses_sessional)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add Course"""
    semesters = {"Harmattan", "Rain"}
    year = datetime.today().year
    sessions = list(range(year, year - 49, -1))
    if request.method == "POST":
        id = session["user_id"]

        # Get data from user
        course_code = request.form.get("course_Code").upper()
        credit_unit = request.form.get("credit_unit")
        check = credit_unit.isdecimal()
        letter_grade = request.form.get("letter_grade").upper()
        exam_session = request.form.get("session")
        semester = request.form.get("semester")

        # Form Validation
        if not course_code or not credit_unit or not letter_grade or not exam_session or not semester:
            flash("Please fill the fileds correctly. All fields are required!", "info")
            return render_template("/add.html", semesters=semesters, sessions=sessions), 404
        
        if not check or credit_unit == '0':
            flash("Credit unit must be a positive integer")
            return render_template("/add.html", semesters=semesters, sessions=sessions), 404

        courses = db.execute("SELECT course_code FROM courses WHERE user_id = ? AND course_code = ?", id, course_code)

        if courses:
            flash("""Course already added!! To edit, please use the edit page.""")
            return render_template("/add.html", semesters=semesters, sessions=sessions), 404
        
        if letter_grade not in list(map(chr, range(65, 70))) or len(letter_grade) != 1:
            flash("Letter grade must be a single character A-F", "info")
            return render_template("/add.html", semesters=semesters, sessions=sessions), 404
        
        credit_unit = float(credit_unit)

        grade_point = 0

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

        # Calculate the quality point for the course
        quality_point = credit_unit * grade_point

        # Add course the to database
        db.execute("INSERT INTO courses (user_id, course_code, credit_unit, letter_grade, grade_point, quality_point, semester, session) VALUES(?,?,?,?,?,?,?,?)",
                  id, course_code, credit_unit, letter_grade, grade_point, quality_point, semester, exam_session)

        return render_template("/add.html", semesters=semesters, sessions=sessions)
    else:
        return render_template("/add.html", semesters=semesters, sessions=sessions)


@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    """Add Course"""
    semesters = {"Harmattan", "Rain"}
    year = datetime.today().year
    sessions = list(range(year, year - 49, -1))
    id = session["user_id"]

    # Get list of user's courses
    all_courses = db.execute("SELECT course_code FROM courses WHERE user_id = ?", id)

    if request.method == "POST":
        
        # Get data from user
        course_code = request.form.get("course_Code")
        credit_unit = request.form.get("credit_unit")
        check = credit_unit.isdecimal()
        letter_grade = request.form.get("letter_grade").upper()
        exam_session = request.form.get("session")
        semester = request.form.get("semester")

        # Form Validation
        if not course_code or not credit_unit or not letter_grade or not exam_session or not semester:
            flash("Please fill the fileds correctly. All fields are required!", "info")
            return render_template("/edit.html", all_courses=all_courses, semesters=semesters, sessions=sessions), 404
        
        if not check or credit_unit == '0':
            flash("Credit unit must be a positive integer")
            return render_template("/edit.html", all_courses=all_courses, semesters=semesters, sessions=sessions), 404

        courses = db.execute("SELECT course_code FROM courses WHERE user_id = ? AND course_code = ?", id, course_code)
        
        # Convert to upper case
        course_code = course_code.upper()

        values = list()
        for i in all_courses:
            for value in i.values():
                values.append(value)

        if course_code not in values:
            flash("Course does not exist! Please add course through the add page.")
            return render_template("/edit.html", all_courses=all_courses, semesters=semesters, sessions=sessions), 404
        
        if letter_grade not in list(map(chr, range(65, 70))) or len(letter_grade) != 1:
            flash("Letter grade must be a single character A-F", "info")
            return render_template("/edit.html", all_courses=user_courses, semesters=semesters, sessions=sessions), 404
        
        credit_unit = float(credit_unit)

        grade_point = 0

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

        # Calculate the quality point for the course
        quality_point = credit_unit * grade_point
        
        # Update database
        db.execute("UPDATE courses SET credit_unit = ?, letter_grade = ?, grade_point = ?, quality_point = ?, semester = ?, session = ? WHERE user_id = ? AND course_code = ?",
                    credit_unit, letter_grade, grade_point, quality_point, semester, exam_session, id, course_code)

        return redirect("/")

    else:
        return render_template("/edit.html", all_courses=all_courses, semesters=semesters, sessions=sessions)


@app.route("/delete", methods=["GET", "POST"])
def delete():
    """Delete course"""

    id = session["user_id"]

    # Get list of user's courses
    all_courses = db.execute("SELECT course_code FROM courses WHERE user_id = ?", id)

    if request.method == "POST":

        # Get data from user
        course_code = request.form.get("course_Code")
    
        if not course_code:
            flash("Please enter the course code.", "info")
            return render_template("/delete.html", all_courses=all_courses)
        
        values = list()
        for i in all_courses:
            for value in i.values():
                values.append(value)

        if course_code not in values:
            flash("Course does not exist!!")
            return render_template("/delete.html", all_courses=all_courses)

        db.execute("DELETE FROM courses WHERE user_id = ? AND course_code = ?", id, course_code)
        return redirect("/delete")
        return render_template("/")
    else:
        return render_template("/delete.html", all_courses=all_courses)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Enter username", "info")
            return render_template("/login.html"), 404

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Enter password", "info")
            return render_template("/login.html"), 404

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid Username or password", "info")
            return render_template("/login.html"), 403

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
         # Check username in database
        name = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        password = request.form.get("password")

        # Ensure username is inputted
        if not request.form.get("username"):
            flash("Please enter username", "info")
            return render_template("/register.html"), 404
        
        # Check if username already exists
        elif name:
            flash("Username already exist!", "info")
            return render_template("/register.html"), 404       

        # Ensure password is inputted
        if not password:
            flash("Please enter password", "info")
            return render_template("/register.html"), 404
        
        # Ensure confirm password is inputted
        elif not request.form.get("confirmation"):
            flash("Re-enter paswword", "info")
            return render_template("/register.html"), 404
        
        # Ensures passwords match
        if password != request.form.get("confirmation"):
            flash("Passwords do not match!", "info")
            return render_template("/register.html"), 404
        
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", request.form.get("username"),
                   generate_password_hash(password, method='pbkdf2:sha256', salt_length=8))

        return redirect("/login")
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")