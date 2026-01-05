from flask import Flask, request, send_file
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

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

        message = f"Overall Risk Level: {risk}"
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
    <style>
        body {{
            font-family: Arial;
            background: linear-gradient(120deg,#e0f7fa,#e8f5e9);
            padding:20px;
        }}
        .card {{
            background:white;
            padding:20px;
            border-radius:12px;
            box-shadow:0 4px 10px rgba(0,0,0,0.15);
            max-width:520px;
            margin:auto;
        }}
        h2 {{ color:#0277bd; }}
        label {{ color:#2e7d32; font-weight:bold; }}
        input, select {{
            width:100%;
            padding:8px;
            margin-bottom:12px;
            border-radius:6px;
            border:1px solid #ccc;
        }}
        button {{
            background:#0288d1;
            color:white;
            border:none;
            padding:12px;
            width:100%;
            border-radius:8px;
            font-size:16px;
        }}
    </style>
    </head>

    <body>
    <div class="card">
        <h2>💧 Water Quality Assessment</h2>

        <form method="post">
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

            <button>Assess Water</button>
        </form>

        <h3>{message}</h3>
        <ul>{issues_html}</ul>

        <h4>Recommended Treatments</h4>
        <ul>{treatments_html}</ul>

        {"<a href='/download'>📄 Download PDF Report</a>" if pdf_ready else ""}
    </div>
    </body>
    </html>
    """

@app.route("/download")
def download():
    return send_file("water_report.pdf", as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)