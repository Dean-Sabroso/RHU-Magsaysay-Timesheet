import csv
import os
from flask import Flask, render_template, request, session, send_file, redirect, jsonify
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime, timedelta
import io

app = Flask(__name__)
app.secret_key = "ojt_secret_key_123"  # Change this for production

CSV_FILE = "timesheet.csv"
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def save_to_csv(timesheet):
    with open(CSV_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["full_name", "college_year", "company_name", "company_address", "date", "day", "morning_in", "morning_out",
             "afternoon_in", "afternoon_out", "total_hours"])
        for entry in timesheet:
            writer.writerow([
                session.get("full_name", ""), session.get("college_year", ""),
                session.get("company_name", ""), session.get("company_address", ""),
                entry["date"], entry["day"], entry["morning_in"], entry["morning_out"],
                entry["afternoon_in"], entry["afternoon_out"], entry["total_hours"]
            ])


def load_from_csv():
    if not os.path.exists(CSV_FILE): return []
    timesheet = []
    with open(CSV_FILE, mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            row["total_hours"] = float(row["total_hours"])
            timesheet.append(row)
    return timesheet


def calculate_hours(start, end):
    if not start or not end: return 0
    try:
        s, e = datetime.strptime(start, "%H:%M"), datetime.strptime(end, "%H:%M")
        return max(0, (e - s).total_seconds() / 3600)
    except:
        return 0


def predict_completion_date(timesheet, required_hours):
    if not timesheet or not required_hours: return None
    total_worked = sum(float(e["total_hours"]) for e in timesheet)
    remaining = required_hours - total_worked
    if remaining <= 0: return None

    avg = sum(float(e["total_hours"]) for e in timesheet) / len(timesheet)
    if avg <= 0: return None

    days_needed = remaining / avg
    last_date = datetime.strptime(max(e["date"] for e in timesheet), "%Y-%m-%d")
    finish_date = last_date + timedelta(days=int(days_needed))

    while finish_date.weekday() >= 5: finish_date += timedelta(days=1)
    return finish_date


@app.route("/", methods=["GET", "POST"])
def index():
    if "timesheet" not in session or not session["timesheet"]:
        session["timesheet"] = load_from_csv()

    if request.method == "POST":
        if "save_details" in request.form:
            for field in ["full_name", "college_year", "company_name", "company_address"]:
                session[field] = request.form.get(field)

            # Handle photo upload
            photo = request.files.get("profile_photo")
            if photo and photo.filename != "":
                filename = secure_filename(photo.filename)
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                session["profile_photo"] = filename

        if "program" in request.form:
            session["required_hours"] = int(request.form["program"])

        if "add_entry" in request.form:
            date = request.form.get("date")
            h = calculate_hours(request.form.get("morning_in"), request.form.get("morning_out")) + \
                calculate_hours(request.form.get("afternoon_in"), request.form.get("afternoon_out"))

            entry = {
                "date": date, "day": datetime.strptime(date, "%Y-%m-%d").strftime("%A"),
                "morning_in": request.form.get("morning_in"), "morning_out": request.form.get("morning_out"),
                "afternoon_in": request.form.get("afternoon_in"), "afternoon_out": request.form.get("afternoon_out"),
                "total_hours": f"{h:.2f}"
            }
            # Remove any existing entry for this date before adding to avoid duplicates
            session["timesheet"] = [e for e in session["timesheet"] if e["date"] != date]
            session["timesheet"].append(entry)
            # Sort timesheet by date
            session["timesheet"] = sorted(session["timesheet"], key=lambda x: x["date"])
            save_to_csv(session["timesheet"])

        session.modified = True
        return redirect("/")

    timesheet = session.get("timesheet", [])
    total_hrs = sum(float(e["total_hours"]) for e in timesheet)
    req_hrs = session.get("required_hours", 0)

    return render_template("index.html",
                           timesheet=timesheet,
                           total_week_hours=f"{total_hrs:.2f}",
                           remaining_hours=max(0, req_hrs - total_hrs),
                           required_hours=req_hrs,
                           predicted_completion_date=predict_completion_date(timesheet, req_hrs),
                           full_name=session.get("full_name", ""),
                           college_year=session.get("college_year", ""),
                           company_name=session.get("company_name", ""),
                           company_address=session.get("company_address", ""),
                           profile_photo=session.get("profile_photo", "")
                           )


@app.route("/edit_entry", methods=["POST"])
def edit_entry():
    data = request.json
    old_date = data.get("old_date")
    timesheet = session.get("timesheet", [])

    for entry in timesheet:
        if entry["date"] == old_date:
            entry["date"] = data.get("date")
            entry["day"] = datetime.strptime(data.get("date"), "%Y-%m-%d").strftime("%A")
            entry["morning_in"] = data.get("morning_in")
            entry["morning_out"] = data.get("morning_out")
            entry["afternoon_in"] = data.get("afternoon_in")
            entry["afternoon_out"] = data.get("afternoon_out")

            # Recalculate hours
            h = calculate_hours(entry["morning_in"], entry["morning_out"]) + \
                calculate_hours(entry["afternoon_in"], entry["afternoon_out"])
            entry["total_hours"] = f"{h:.2f}"
            break

    # Sort and save
    session["timesheet"] = sorted(timesheet, key=lambda x: x["date"])
    save_to_csv(session["timesheet"])
    session.modified = True
    return jsonify({"success": True})


@app.route("/delete_entry/<date>", methods=["DELETE"])
def delete_entry(date):
    session["timesheet"] = [e for e in session.get("timesheet", []) if e["date"] != date]
    save_to_csv(session["timesheet"])
    session.modified = True
    return jsonify({"success": True})


@app.route("/reset", methods=["POST"])
def reset():
    session.clear()
    if os.path.exists(CSV_FILE): os.remove(CSV_FILE)
    return redirect("/")


@app.route("/download/csv")
def download_csv():
    return send_file(CSV_FILE, as_attachment=True) if os.path.exists(CSV_FILE) else redirect("/")


@app.route("/download/pdf")
def download_pdf():
    timesheet = session.get("timesheet", [])

    # Create an in-memory buffer for the PDF
    buffer = io.BytesIO()

    # Setup canvas (letter size)
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # --- PDF HEADER ---
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, height - 50, "OJT Timesheet Report")

    # --- INTERN DETAILS ---
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 90, f"Name: {session.get('full_name', 'N/A')}")
    c.drawString(50, height - 110, f"Company: {session.get('company_name', 'N/A')}")
    c.drawString(50, height - 130, f"Year Level: {session.get('college_year', 'N/A')}")
    c.drawString(50, height - 150, f"Target Hours: {session.get('required_hours', 0)} hrs")

    # --- TABLE HEADERS ---
    y_position = height - 190
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y_position, "Date")
    c.drawString(130, y_position, "Day")
    c.drawString(220, y_position, "AM Shift")
    c.drawString(340, y_position, "PM Shift")
    c.drawString(480, y_position, "Daily Hours")

    # Draw a line under headers
    c.line(50, y_position - 5, 550, y_position - 5)

    # --- TABLE RECORDS ---
    y_position -= 25
    c.setFont("Helvetica", 10)
    total_hours = 0.0

    for entry in timesheet:
        c.drawString(50, y_position, entry.get("date", ""))
        c.drawString(130, y_position, entry.get("day", ""))

        # Format AM/PM times so they look clean even if blank
        am_in, am_out = entry.get("morning_in", ""), entry.get("morning_out", "")
        pm_in, pm_out = entry.get("afternoon_in", ""), entry.get("afternoon_out", "")

        am_text = f"{am_in} - {am_out}" if am_in or am_out else "-"
        pm_text = f"{pm_in} - {pm_out}" if pm_in or pm_out else "-"

        c.drawString(220, y_position, am_text)
        c.drawString(340, y_position, pm_text)

        c.drawString(480, y_position, str(entry.get("total_hours", "0")))

        total_hours += float(entry.get("total_hours", 0))
        y_position -= 20

        # Create a new page if we run out of space at the bottom
        if y_position < 50:
            c.showPage()
            y_position = height - 50
            c.setFont("Helvetica", 10)

    # --- FOOTER / TOTALS ---
    c.line(50, y_position, 550, y_position)
    y_position -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(340, y_position, "Total Rendered Hours:")
    c.drawString(480, y_position, f"{total_hours:.2f} hrs")

    # Save PDF to buffer
    c.save()
    buffer.seek(0)

    # Send the PDF file to the browser
    return send_file(
        buffer,
        as_attachment=True,
        download_name="OJT_Timesheet_Report.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    app.run(debug=True)