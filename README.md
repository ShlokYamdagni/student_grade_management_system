# Student Grade Management System (Flask)

A Flask-based Student Grade Management System with Admin, Teacher, and Student access roles. This system allows teachers to manage student marks, handle recheck queries, while the admin approves teacher accounts. Students can view their detailed results, percentage, and grades online. Passwords are secured using bcrypt hashing.

## Features

- Teacher Registration + Admin Approval System
- Secure login for Students and Teachers
- Student Marks (Practical + Written)
- Student Dashboard with Result + Percentage + Grade calculation
- Raise Rechecking Query by Student
- Teacher can Mark Query as Pending / Reviewed / Resolved
- Admin Panel to approve or reject Teacher account requests
- Password hashing using bcrypt (no plain passwords stored)

## Subjects Included

- Mathematics  
- Physics  
- Chemistry  
- Computer Science  
- Electronics  

## Tech Stack

- Python (Flask)
- SQLite Database
- HTML / CSS (Frontend Templates)
- bcrypt (Password hashing)

## Run Project Locally

```bash
pip install flask flask_sqlalchemy bcrypt
python app.py
