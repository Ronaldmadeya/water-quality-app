from flask import Flask, request, send_file
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

import csv
import os

app = Flask(__name__)

# =========================
# LANGUAGE DICTIONARY
# =========================
LANG = {
    "en": {
        "title": "Water Quality Assessment App",
        "submit": "Assess Water",
        "safe": "SAFE",
        "unsafe": "UNSAFE",
        "recommendations": "Recommendations",
        "language": "Language"
    },
    "ny": {
        "title": "Pulogalamu Yoyesa Madzi",
        "submit": "Yezani Madzi",
        "safe": "OTETEZEKA",
        "unsafe": "OWOPSA",
        "recommendations": "Malangizo",
        "language": "Chilankhulo"
    }
}

# =========================
# WHO GUIDELINES
# =========================

# =========================
# WHO GUIDELINES
# =========================
HEALTH_BASED = {
    "ecoli": (0, 0),
    "arsenic": (0, 0.01),
    "lead": (0, 0.01),
    "mercury": (0, 0.006),
    "nitrate": (0, 50),
    "fluoride": (0, 1.5),
}

AESTHETIC = {
    "ph": (6.5, 8.5),
    "turbidity": (0, 5),
    "tds": (0, 600),
}

# =========================
# TREATMENTS
# =========================
TREATMENTS = {
    "Low": ["No treatment required"],
    "Medium": [
        "Cloth filtration",
        "Boiling",
        "Solar disinfection (SODIS)",
        "Chlorination"
    ],
    "High": [
        "DO NOT drink",
        "Reverse Osmosis (RO)",
        "UV treatment",
        "Source substitution"
    ]
}

# =========================
# ASSESSMENT
# =========================
def assess(values):
    issues = []
    risk = "Low"

    for p, (lo, hi) in HEALTH_BASED.items():
        if not (lo <= values[p] <= hi):
            risk = "High"
            issues.append(f"{p.upper()} exceeds health guideline")

    for p, (lo, hi) in AESTHETIC.items():
        if not (lo <= values[p] <= hi) and risk != "High":
            risk = "Medium"
            issues.append(f"{p.upper()} outside acceptable range")

    return risk, issues

# =========================
# PDF REPORT
# =========================
def generate_pdf(data, risk, issues):
    filename = "water_report.pdf"
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    c = []

    c.append(Paragraph("Water Quality Assessment Report", styles["Title"]))
    c.append(Paragraph(f"Date: {datetime.now()}", styles["Normal"]))
    c.append(Paragraph(f"Name: {data['name']}", styles["Normal"]))
    c.append(Paragraph(f"Location: {data['location']}", styles["Normal"]))
    c.append(Paragraph(f"Water Source: {data['source']}", styles["Normal"]))
    c.append(Paragraph(f"Risk Level: {risk}", styles["Heading2"]))

    c.append(Paragraph("Issues Identified:", styles["Heading3"]))
    for i in issues:
        c.append(Paragraph(f"- {i}", styles["Normal"]))

    c.append(Paragraph("Recommended Treatments:", styles["Heading3"]))
    for t in TREATMENTS[risk]:
        c.append(Paragraph(f"- {t}", styles["Normal"]))

    doc.build(c)
    return filename

# =========================
# WEB APP
# =========================
def save_assessment(data, risk, issues):
    file_exists = os.path.isfile("assessments.csv")

    with open("assessments.csv", mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "Date",
                "Name",
                "Location",
                "Water Source",
                "Risk Level",
                "Issues"
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            data["name"],
            data["location"],
            data["source"],
            risk,
            "; ".join(issues) if issues else "None"
        ])
@app.route("/", methods=["GET", "POST"])
def home():
    message = ""
    issues_html = ""
    treatments_html = ""
    pdf_ready = False

    if request.method == "POST":
        values = {k: float(request.form[k]) for k in {**HEALTH_BASED, **AESTHETIC}}

        risk, issues = assess(values)

        data = {
            "name": request.form["name"],
            "location": request.form["location"],
            "source": request.form["source"]
        }

        generate_pdf(data, risk, issues)
        save_assessment(data, risk, issues)

        message = f"Overall Risk Level: {risk}"
        issues_html = "".join(f"<li>{i}</li>" for i in issues)
        treatments_html = "".join(f"<li>{t}</li>" for t in TREATMENTS[risk])
        pdf_ready = True
    # LANGUAGE CHOICE (GET or POST)
    lang = request.values.get("lang", "en")
    text = LANG.get(lang, LANG["en"])

    message = ""
    issues_html = ""
    treatments_html = ""
    pdf_ready = False

    if request.method == "POST":
        values = {k: float(request.form[k]) for k in {**HEALTH_BASED, **AESTHETIC}}

        risk, issues = assess(values)

        data = {
            "name": request.form["name"],
            "location": request.form["location"],
            "source": request.form["source"]
        }

        generate_pdf(data, risk, issues)

        message = f"{text['recommendations']}: {risk}"
        issues_html = "".join(f"<li>{i}</li>" for i in issues)
        treatments_html = "".join(f"<li>{t}</li>" for t in TREATMENTS[risk])
        pdf_ready = True

    form_inputs = "".join(
        f"<label>{k.upper()}</label><input name='{k}' required>"
        for k in {**HEALTH_BASED, **AESTHETIC}
    )

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial;
                background: linear-gradient(120deg,#e0f7fa,#e8f5e9);
                padding:10px;
                margin:0;
            }}
            .card {{
                background:white;
                padding:20px;
                border-radius:12px;
                box-shadow:0 4px 10px rgba(0,0,0,0.15);
                max-width:95%;
                margin:10px auto;
            }}
            h2 {{ color:#0277bd; text-align:center; }}
            label {{ color:#2e7d32; font-weight:bold; }}
            input, select {{
                width:100%;
                padding:10px;
                margin-bottom:12px;
                border-radius:6px;
                border:1px solid #ccc;
            }}
            button {{
                background:#0288d1;
                color:white;
                border:none;
                padding:14px;
                width:100%;
                border-radius:8px;
                font-size:16px;
                cursor:pointer;
            }}
            ul {{ padding-left:18px; }}
        </style>
    </head>

    <body>

        <!-- LANGUAGE SELECTION (USER CHOICE) -->
        <form method="get" style="text-align:center;margin-bottom:10px;">
            <label>{text['language']}:</label>
            <select name="lang" onchange="this.form.submit()">
                <option value="en" {"selected" if lang=="en" else ""}>English</option>
                <option value="ny" {"selected" if lang=="ny" else ""}>Chichewa</option>
            </select>
        </form>

        <div class="card">
            <h2>💧 {text['title']}</h2>

            <form method="post">
                <!-- PRESERVE LANGUAGE CHOICE -->
                <input type="hidden" name="lang" value="{lang}">

                <label>Your Name</label>
                <input name="name" required>

                <label>Location</label>
                <input name="location" required>

                <label>Water Source</label>
                <select name="source">
                    <option>Well</option>
                    <option>Borehole</option>
                    <option>River</option>
                    <option>Tap</option>
                </select>

                {form_inputs}

                <button>{text['submit']}</button>
            </form>

            <h3>{message}</h3>
            <ul>{issues_html}</ul>

            <h4>{text['recommendations']}</h4>
            <ul>{treatments_html}</ul>

            {"<a href='/download'>📄 Download PDF Report</a>" if pdf_ready else ""}
        </div>

        <hr style="margin:30px 0;">

        <!-- DEVELOPER & DONATION SECTION -->
        <div style="text-align:center; font-size:14px; color:#333; padding:15px;">
            <p>
                <strong>Developed by RONALD TECH</strong><br>
                <em>Local Innovation for Africa 🌍</em>
            </p>

            <p>
                Developer: <strong>Ronald Madeya</strong><br>
                Email:
                <a href="mailto:madeyaronald727@gmail.com">
                    madeyaronald727@gmail.com
                </a>
            </p>

            <button onclick="document.getElementById('donate').style.display='block'"
                style="background:#1e88e5;color:white;border:none;
                padding:10px 18px;border-radius:6px;cursor:pointer;">
                ❤️ Support This Project
            </button>

            <div id="donate" style="display:none; margin-top:15px;
                border:1px solid #ccc; padding:15px; border-radius:8px;">
                <p><strong>Support via Mobile Money / Bank</strong></p>
                <p>
                    Airtel Money Code: <strong>10032217</strong><br>
                    TNM Agent Code: <strong>286291</strong><br>
                    Standard Bank Account: <strong>9100005969937</strong>
                </p>
                <p style="font-size:12px;color:#666;">
                    Your support helps improve water safety tools
                    for rural and urban communities.
                </p>
            </div>
        </div>

    </body>
    </html>
    """
@app.route("/data")
def view_data():
    rows = []

    if os.path.exists("assessments.csv"):
        with open("assessments.csv", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

    table_rows = ""
    for i, row in enumerate(rows):
        tag = "th" if i == 0 else "td"
        table_rows += "<tr>" + "".join(f"<{tag}>{cell}</{tag}>" for cell in row) + "</tr>"

    return f"""
    <html>
    <head>
        <title>Saved Water Assessments</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: Arial;
                padding: 15px;
                background: #f1f8e9;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                border: 1px solid #999;
                padding: 8px;
                font-size: 14px;
            }}
            th {{
                background: #0288d1;
                color: white;
            }}
            a {{
                display:inline-block;
                margin-top:15px;
                text-decoration:none;
                color:#0288d1;
                font-weight:bold;
            }}
        </style>
    </head>
    <body>
        <h2>📊 Saved Water Assessments</h2>

        <table>
            {table_rows}
        </table>

        <a href="/download_csv">⬇ Download CSV</a><br>
        <a href="/">⬅ Back to App</a>
    </body>
    </html>
    """
@app.route("/download_csv")
def download_csv():
    return send_file("assessments.csv", as_attachment=True)
@app.route("/download")
def download():
    return send_file("water_report.pdf", as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)