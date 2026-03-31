OJT Timesheet Pro 🕒
A comprehensive and responsive web-based timesheet tracking system designed to help On-the-Job Training (OJT) students effortlessly log their hours, track their progress, and predict their completion date at the Rural Health Unit (RHU).

Features ✨
👤 Intern Profile Management

Upload and display 2x2 profile photos

Manage personal details (Full Name, Year Level)

Manage deployment details (Company Name, Address)

🎯 Goal & Progress Tracking

Select target program hours (e.g., Computer Science 300 hrs, IT 280 hrs)

Real-time Dashboard calculating:

Total rendered hours

Remaining required hours

Predicted finish date based on current pacing

⏱️ Time Logging & Management

Log daily AM and PM shifts (In/Out)

"Quick 8-5 Shift" button for fast autofill

View all logged records in a clean, responsive table

Edit existing timesheet entries via a modal interface

Delete individual records or Reset all data

📥 Export & Reporting

Download timesheet records as a CSV file

Download timesheet records as a formatted PDF report

Tech Stack 🛠️
Backend: Python, Flask

Frontend: HTML5, CSS3, Vanilla JavaScript

Styling: Bootstrap 5.3, Custom CSS (Glassmorphism UI)

Data Storage: Local CSV (timesheet.csv) and file system handling for image uploads

Folder Structure 📁
Plaintext
OJT RHU/
├── static/
│   ├── uploads/          # Stores user 2x2 photos and RHU logo
│   ├── script.js         # Frontend interactivity
│   └── styles.css        # Custom CSS and glassmorphism styles
├── templates/
│   └── index.html        # Main dashboard interface
├── app.py                # Main Flask application and backend logic
├── requirements.txt      # Python dependencies
├── timesheet.csv         # Database for logged hours
├── timesheet_report.pdf  # Generated PDF reports
└── README.md             # Project documentation
How to Run Locally 🚀
Clone the repository:

Bash
git clone https://github.com/yourusername/ojt-timesheet-pro.git
cd ojt-timesheet-pro
Set up a virtual environment (optional but recommended):

Bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
Install dependencies:

Bash
pip install -r requirements.txt
Run the application:

Bash
python app.py
Open in your browser:
Navigate to http://127.0.0.1:5000 to view the app!
