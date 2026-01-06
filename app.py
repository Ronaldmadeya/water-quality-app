from flask import Flask, request, send_file
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
import sqlite3, os

# =========================
# APP CONFIG
# =========================
app = Flask(__name__)
DB_NAME = "assessments.db"

# =========================
# PARAMETERS (WHO)
# =========================
CORE_PARAMS = {
    "ph": (6.5, 8.5),
    "turbidity": (0, 5),
    "tds": (0, 500),
    "nitrate": (0, 50),
    "fluoride": (0, 1.5),
    "iron": (0, 0.3),
    "lead": (0, 0.01),
    "ecoli": (0, 0),
    "conductivity": (0, 2500),
    "hardness": (0, 200)
}

EXTRA_PARAMS = {
    "chloride": (0, 500),
    "sodium": (0, 200),
    "calcium": (0, 100),
    "sulphate": (0, 100),
    "ammonium": (0, 0.5),
    "phosphate": (0, 0.1),
    "zinc": (0, 5),
    "manganese": (0, 0.5),
    "copper": (0, 2),
    "chromium": (0, 0.05),
    "cadmium": (0, 0.003),
    "bod": (0, 6),
    "cod": (0, 10),
    "do": (4, 6)
}

ALL_PARAMS = {**CORE_PARAMS, **EXTRA_PARAMS}

# =========================
# LANGUAGE CONTENT
# =========================
LANG = {
    "en": {
        "title": "Water Quality Assessment",
        "name": "Name",
        "location": "Location",
        "source": "Water Source",
        "priority": "Priority Parameters",
        "optional": "Optional Parameters",
        "test_more": "Test More",
        "assess": "Assess Water",
        "risk": "Overall Risk Level",
        "recommendations": "Recommendations",
        "download": "Download Assessment Report (PDF)",
        "menu_title": "About This App",
        "menu_body": """
This application exists because millions still drink unsafe water —
not by choice, but by lack of access to testing tools.

<strong>How it works:</strong><br>
You test only what you can. Even with limited data, the system
intelligently evaluates health risk.

<strong>Benefits:</strong><br>
• Works without laboratories<br>
• Supports rural decision-making<br>
• Reduces preventable waterborne disease

<strong>Gaps it fills:</strong><br>
Cost, distance, equipment scarcity, and technical exclusion.

<strong>Developer Vision:</strong><br>
To place scientific water safety into the hands of every village,
every household, every mother.

<strong>Barriers Being Broken:</strong><br>
Poverty, geography, literacy, and silence.

If this vision speaks to you, your support becomes protection.
""",
        "donation_title": "❤️Support This Vision",
        "donation_text": """
By supporting this project, you are funding African-led solutions,
not temporary aid. You are investing in dignity, science, and survival.
""",
        "developer": "Developed by Ronald Madeya — Local Innovation for Africa 🌍",
        "treatments": {
            "Low": [
                "Water meets safety standards",
                "Maintain clean storage containers"
            ],
            "Medium": [
                "Boil water before drinking",
                "Use household chlorination",
                "Sand and charcoal filtration",
                "Clay pot filtration"
            ],
            "High": [
                "DO NOT drink without treatment",
                "Use RO or UV treatment if available",
                "Combine boiling and filtration",
                "Change water source if possible"
            ]
        }
    },
    "ny": {
        "title": "Kuyeza Ubwino wa Madzi",
        "name": "Dzina",
        "location": "Malo",
        "source": "Gwero la Madzi",
        "priority": "Zoyesa Zofunika Kwambiri",
        "optional": "Zoyesa Zina",
        "test_more": "Yezani Zina",
        "assess": "Yezani Madzi",
        "risk": "Mulingo wa Chiopsezo",
        "recommendations": "Malangizo",
        "download": "Tsitsani Lipoti la PDF",
        "menu_title": "Za Pulogalamuyi",
        "menu_body": """
Pulogalamuyi ilipo chifukwa anthu ambiri amamwa madzi osatetezeka
chifukwa chosowa zida zoyezera.

<strong>Momwe imagwirira ntchito:</strong><br>
Mumayesera zomwe mungathe. Ngakhale ndi zochepa,
dongosololi limatha kuweruza chiopsezo.

<strong>Ubwino wake:</strong><br>
• Simafuna labotale<br>
• Imathandiza m’midzi<br>
• Imapulumutsa miyoyo

<strong>Masiyana omwe imadzaza:</strong><br>
Mtengo, mtunda, kusowa zida, ndi kusowa chidziwitso.

<strong>Masomphenya a Wopanga:</strong><br>
Kubweretsa chitetezo cha madzi kwa banja lililonse.

Ngati masomphenyawa akukhudzani, thandizani.
""",
        "donation_title": "❤️Thandizani Masomphenyawa",
        "donation_text": """
Thandizo lililonse silingokhala mphatso —
ndi moyo wopulumutsidwa, mwana wotetezedwa,
ndi sitepe yopita ku chilungamo cha madzi.
""",
        "developer": "Wopangidwa ndi Ronald Madeya — Zatsopano za ku Africa 🌍",
        "treatments": {
            "Low": [
                "Madzi ndi otetezeka",
                "Sungani mu ziwiya zoyera"
            ],
            "Medium": [
                "Wiritse madzi musanamwe",
                "Gwiritsani ntchito mankhwala a chlorine",
                "Sefa ndi mchenga ndi makala"
            ],
            "High": [
                "OSAMWA popanda kuyeretsa",
                "Gwiritsani ntchito RO kapena UV",
                "Sinthani gwero la madzi"
            ]
        }
    }
}

# =========================
# ASSESSMENT
# =========================
def assess(values):
    issues = []
    risk = "Low"
    for p, v in values.items():
        lo, hi = ALL_PARAMS[p]
        if not (lo <= v <= hi):
            issues.append(p.upper())
            risk = "High"
    if risk != "High" and issues:
        risk = "Medium"
    return risk, issues

# =========================
# PDF REPORT (LANG AWARE)
# =========================
def generate_pdf(data, risk, issues, text):
    doc = SimpleDocTemplate("water_report.pdf", pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(text["title"], styles["Title"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"{text['name']}: {data['name']}", styles["Normal"]))
    story.append(Paragraph(f"{text['location']}: {data['location']}", styles["Normal"]))
    story.append(Paragraph(f"{text['source']}: {data['source']}", styles["Normal"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"{text['risk']}: {risk}", styles["Heading2"]))

    story.append(Spacer(1, 10))
    story.append(Paragraph(text["recommendations"], styles["Heading3"]))
    for t in text["treatments"][risk]:
        story.append(Paragraph(f"- {t}", styles["Normal"]))

    doc.build(story)

# =========================
# DATABASE
# =========================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS assessments (
        id INTEGER PRIMARY KEY,
        date TEXT,
        name TEXT,
        location TEXT,
        source TEXT,
        risk TEXT
    )
    """)
    conn.commit()
    conn.close()

# =========================
# MAIN ROUTE
# =========================
@app.route("/", methods=["GET", "POST"])
def home():
    lang = request.values.get("lang", "en")
    text = LANG[lang]

    message = ""
    treatments_html = ""
    pdf_ready = False

    if request.method == "POST":
        values = {p: float(request.form[p]) for p in ALL_PARAMS if request.form.get(p)}
        risk, issues = assess(values)

        data = {
            "name": request.form["name"],
            "location": request.form["location"],
            "source": request.form["source"]
        }

        generate_pdf(data, risk, issues, text)
        message = f"{text['risk']}: {risk}"
        treatments_html = "".join(f"<li>{t}</li>" for t in text["treatments"][risk])
        pdf_ready = True

    core_inputs = "".join(f"<label>{p.upper()}</label><input name='{p}' type='number' step='any'>" for p in CORE_PARAMS)
    extra_inputs = "".join(f"<label>{p.upper()}</label><input name='{p}' type='number' step='any'>" for p in EXTRA_PARAMS)

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {{
    font-family: Arial;
    background: linear-gradient(120deg,#e0f7fa,#e8f5e9);
    margin:0;
}}
.menu {{
    position:fixed; top:12px; left:12px;
    font-size:26px; cursor:pointer;
}}
.panel {{
    display:none; position:fixed; inset:0;
    background:white; padding:20px; overflow:auto; z-index:10;
}}
.card {{
    background:white; margin:60px auto;
    padding:20px; width:95%; border-radius:14px;
}}
label {{ font-weight:bold; display:block; margin-top:10px; }}
input, select {{
    width:100%; padding:12px; border-radius:8px;
}}
button {{
    margin-top:14px; padding:14px;
    width:100%; background:#0288d1;
    color:white; border:none; border-radius:10px;
}}
</style>
<script>
function openMenu(){{document.getElementById('panel').style.display='block';}}
function closeMenu(){{document.getElementById('panel').style.display='none';}}
</script>
</head>

<body>

<div class="menu" onclick="openMenu()">☰</div>

<form method="get" style="position:fixed; top:10px; right:10px;">
<select name="lang" onchange="this.form.submit()">
<option value="en" {"selected" if lang=="en" else ""}>EN</option>
<option value="ny" {"selected" if lang=="ny" else ""}>NY</option>
</select>
</form>

<div id="panel" class="panel">
<button onclick="closeMenu()" style="
    background:#0288d1;
    color:white;
    border:none;
    padding:14px;
    width:100%;
    border-radius:10px;
    font-size:18px;
">✕ Close</button>

<div style="max-width:700px;margin:auto;line-height:1.7;">

<h2 style="color:#01579b;margin-top:25px;">
💧 About This App
</h2>

<p style="font-size:17px;">
<strong>
{ "Clean water should never be a privilege."
  if lang=="en" else
  "Madzi oyera sayenera kukhala mwayi wa ochepa." }
</strong>
</p>

<p>
{ "This application exists because millions of people drink unsafe water — not by choice, but because testing tools are expensive, distant, or unavailable."
  if lang=="en" else
  "Pulogalamuyi ilipo chifukwa anthu mamiliyoni ambiri amamwa madzi osatetezeka — osati chifukwa chosankha, koma chifukwa zida zoyesera madzi ndizodula, zakutali, kapena palibe." }
</p>

<hr>

<h3 style="color:#0277bd;">⚙️ { "How It Works" if lang=="en" else "Mmene Imagwirira Ntchito" }</h3>

<p>
{ "You only test what you are able to test. Even with limited data, the system intelligently evaluates health risk and gives practical guidance."
  if lang=="en" else
  "Mumayesetsa zomwe mungathe. Ngakhale deta ikhale yochepa, dongosololi limasanthula chiopsezo cha thanzi ndikuupatsani malangizo omveka." }
</p>

<hr>

<h3 style="color:#0277bd;">🌍 { "Why This Matters" if lang=="en" else "Chifukwa Chake Ndi Chofunika" }</h3>

<ul>
<li>{ "Works without laboratories" if lang=="en" else "Imagwira ntchito popanda labotale" }</li>
<li>{ "Supports rural and low-income communities" if lang=="en" else "Imathandiza madera akumidzi ndi osauka" }</li>
<li>{ "Reduces preventable waterborne diseases" if lang=="en" else "Imachepetsa matenda obwera chifukwa cha madzi" }</li>
</ul>

<hr>

<h3 style="color:#0277bd;">🧩 { "Gaps It Fills" if lang=="en" else "Mipata Imene Ikudzaza" }</h3>

<p>
{ "High cost, long distances, lack of equipment, low literacy, and technological exclusion."
  if lang=="en" else
  "Mtengo wokwera, mtunda wautali, kusowa kwa zida, kusaphunzira, ndi kusiyidwa paukadaulo." }
</p>

<hr>

<h3 style="color:#0277bd;">🚀 { "Developer Vision" if lang=="en" else "Masomphenya a Wopanga" }</h3>

<p style="font-style:italic;">
{ "To place scientific water safety into the hands of every village, every household, and every mother — so no child gets sick from the water they drink."
  if lang=="en" else
  "Kupereka chitetezo cha madzi cha sayansi m'manja mwa mudzi uliwonse, banja lililonse, ndi amayi onse — kuti mwana aliyense azimwa madzi otetezeka." }
</p>

<hr>

<h3 style="color:#0277bd;">🛠️ { "Barriers Being Broken" if lang=="en" else "Zotchinga Zikuphwanyidwa" }</h3>

<p>
{ "Poverty. Geography. Silence. This app exists to break them — permanently."
  if lang=="en" else
  "Umphawi. Mtunda. Kusadziwika. Pulogalamuyi ilipo kuti iziphwanye zonsezi — kosatha." }
</p>

<p style="margin-top:20px;font-weight:bold;">
{ "If this vision speaks to you, your support becomes protection."
  if lang=="en" else
  "Ngati masomphenyawa akukhudzani, thandizo lanu limakhala chitetezo." }
</p>

</div>
</div>

<div class="card">
<h2>💧 {text["title"]}</h2>

<form method="post">
<input type="hidden" name="lang" value="{lang}">

<label>{text["name"]}</label><input name="name" required>
<label>{text["location"]}</label><input name="location" required>

<label>{text["source"]}</label>
<select name="source">
<option>Well</option><option>Borehole</option>
<option>River</option><option>Tap</option>
</select>

<h3>{text["priority"]}</h3>
{core_inputs}

<button type="button" onclick="document.getElementById('more').style.display='block'">
➕ {text["test_more"]}
</button>

<div id="more" style="display:none">
<h3>{text["optional"]}</h3>
{extra_inputs}
</div>

<button>{text["assess"]}</button>
</form>

<h3>{message}</h3>
<ul>{treatments_html}</ul>

{"<a href='/download'>📄 " + text["download"] + "</a>" if pdf_ready else ""}
<hr>

<div style="padding:20px; text-align:center;">
<p><strong>
{ "Every contribution you make is not a donation — it is a life protected, a child spared from disease, and a step toward water justice."
  if lang=="en" else
  "Thandizo lililonse silingokhala mphatso — ndi moyo wopulumutsidwa, mwana wotetezedwa ku matenda, ndi sitepe yopita ku chilungamo cha madzi." }
</strong></p>

<p>
{ "By supporting this project, you are funding African-led solutions, not temporary aid. You are investing in dignity, science, and survival."
  if lang=="en" else
  "Mukathandiza pulogalamuyi, mukuthandiza njira zothetsera mavuto zopangidwa ndi Aafrika okha — osati thandizo lakanthawi. Mukuyika ndalama mu ulemu, sayansi, ndi moyo." }
</p>

<button onclick="document.getElementById('donate').style.display='block'">
❤️ { "Support This Vision" if lang=="en" else "Thandizani Masomphenyawa" }
</button>

<div id="donate" style="display:none; margin-top:12px;">
<p>
Airtel Money: <strong>10032217</strong><br>
TNM Agent: <strong>286291</strong><br>
Standard Bank: <strong>9100005969937</strong>
</p>
</div>

<p style="font-size:14px; margin-top:14px;">
{ "Developed by" if lang=="en" else "Wopangidwa ndi" }
<strong>Ronald Madeya</strong><br>
{ "African Innovation for African Lives 🌍"
  if lang=="en" else
  "Zatsopano za ku Africa pa Miyoyo ya Aafrika 🌍" }
</p>
</div>

</body>
</html>
"""

@app.route("/download")
def download():
    return send_file("water_report.pdf", as_attachment=True)

# =========================
# START
# =========================
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)