# CGPA Calculator
#### Video Demo: <https://youtu.be/hMNQSwUZ1z0>
#### Description:
This is dynamic web application that help students in calculating their CGPA and also allows them to store their courses to avoid havong to reenter course information everytime one need to calculate his or her CGPA. This project is inpired by the stress I usually have to face just to calculate my CGPA, I always have to punch calculator every time I need to calculator my CGPA. At the moment, the calculation is based on 5 point grading system which is the most common grading system for colleges and universities in my country, Nigeria. 

So this app is built with flask, a web programming microframework of Python programming language. 

#### Technologies used
- On the frontend
    - HTML
    - CSS
    - Bootstrap
- On the backend
   - Python
   - Flask
   - SQL

### Files/folders contain in project directory
- Static folder
    -
    This contains stylesheets and fav icon for the app. It contains:
    - Styles.css, which is the file that has the styling for all the pages in the app
    - Also Bootstrap files
- Templates folder
    -
    This includes all the HTML files, we have;
    - add.html, which is the page that allows user to add their courses to the database.
    User adds course code, credit unit, letter grade, and also chooses which semester and session does the course belong. Form validation is done in such a way that it rejects the request if any field is empty or not entered correctly. Also it rejects course if it already exist for the user

    - delete.html, this is page where user can delete any course, or remove any course. This page list all the added courses for a user and it rejects the request if no course is chosen on click of the delete button.

    - edit.html, in this page, user gets to edit any course that has already been added to database incase of mistake at point of input. It list all the courses added by the user and allow user to edit every field except the course code.

    - index.html, this is the homepage which shows the table of courses user has added to database and also shows their CGPA. It shows the table of courses per session and also shows the to quality points and total credit units for each session.

    - layout.html, this is the layout for the app, it includes the navbars and also the footer which has some icons for easy navigation

    - login.html, this is the page where all user get redirected to by default if they are yet to login, it accepts users username and password and log registered users in. It makes sure the user exist also the password is correctly entered.

    - register.html, on this page user gets to register account using a unique username and password. It rejects the request if the username already exist

- Utils folder: This folder has the decorator for the app

- app.py: this file contains all codes that connect the frontend of the app to the backend. It also includes the database connections

- database file: this is the file that stores users information

- requirements file: this is the file that contains all the requirement to run this app

- README: Readme file that contains the documentation for the app

## Features of the app
- It allows user to add courses
- It allows user to edit/modify added courses
- It allows user to delete courses
- It only support unique username, that is two users cannot have the same username
- It contains navigation icons for easy movement from one page to another
- Each course name/code must be unique for each user
- It shows the user's courses in tables per session
- It shows the calculated CGPA with 2 decimal precision which is done at point of rendering. That is no approximation is done until the final CGPA value has been calculated
- Strong backend form validation was put in place
- Every page except login and register pages make sure the user is logged in before they can have access.

### Features to be added
- Password recovery. That is user should be able to reset their password if forgotten
- Inclusion of email is registration credential
- Email confirmation 
- Listing the courses added per semester and per session
- Support for other grading systems
- Improvements on the frontend