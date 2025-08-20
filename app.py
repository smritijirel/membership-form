import os
import uuid
from datetime import datetime
from flask import Flask, request, redirect, url_for, render_template_string, session, send_from_directory, flash
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine, Column, Integer, String, Date, Text
from sqlalchemy.orm import declarative_base, sessionmaker

# Optional BS→AD converter
try:
    from nepali_datetime import date as nep_date  # noqa: F401
except Exception:
    nep_date = None

# ------------------------------------------------------------------
# Flask setup
# ------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "devkey-jan-membership")

BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
ALLOWED_EXTS = {"png", "jpg", "jpeg", "pdf"}

# ------------------------------------------------------------------
# Database (SQLite via SQLAlchemy ORM)
# ------------------------------------------------------------------
Base = declarative_base()
engine = create_engine("sqlite:///jan_members.db", echo=False, future=True)
DBSession = sessionmaker(bind=engine)

class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True)
    lang = Column(String(8))

    # Member Info
    name = Column(String(200))
    full_name_en = Column(String(200))
    dob_bs = Column(String(20))
    dob_ad = Column(Date, nullable=True)
    gender = Column(String(50))
    occupation = Column(String(200))

    # Contact
    perm_address = Column(Text)
    temp_address = Column(Text)
    phone = Column(String(50))
    email = Column(String(200))

    # Govt Doc
    doc_type = Column(String(100))
    doc_issued_date = Column(String(20))
    doc_file = Column(String(300))

    # Education
    education = Column(String(100))

    # Professional
    job_title = Column(String(200))
    experience_years = Column(String(50))
    skills = Column(Text)
    org_name = Column(String(200))

    # Membership
    membership_type = Column(String(100))

    # Family
    father_name = Column(String(200))
    mother_name = Column(String(200))
    spouse_name = Column(String(200))
    children = Column(Text)

    # Emergency
    em_name = Column(String(200))
    em_relation = Column(String(100))
    em_phone = Column(String(50))
    em_address = Column(Text)

    # Payment
    pay_method = Column(String(100))
    transaction_id = Column(String(200))
    payment_file = Column(String(300))

    # Declaration
    declaration = Column(String(10))

Base.metadata.create_all(engine)

# ------------------------------------------------------------------
# Language packs (EN / Nepali / Jirel)
# ------------------------------------------------------------------
LABELS = {
    "en": {
        "lang_name": "English",
        "take_membership": "Take Membership",
        "sections": {
            "language": "Choose Language",
            "member_info": "Member Information",
            "contact": "Contact Details",
            "gov_doc": "Government Document Upload",
            "education": "Educational Qualification",
            "professional": "Professional Skills / Expertise",
            "membership": "Membership Type",
            "family": "Family Information",
            "emergency": "Emergency Contact Person",
            "payment": "Membership Payment",
            "declaration": "Declaration",
            "review": "Review & Submit"
        },
        "fields": {
            "name": "Name",
            "full_name_en": "Full Name in English",
            "dob": "Date of Birth (B.S.)",
            "dob_ad": "Date of Birth (A.D.)",
            "gender": "Gender",
            "male": "Male",
            "female": "Female",
            "others": "Others",
            "occupation": "Occupation",
            "perm_address": "Permanent Address",
            "temp_address": "Temporary Address",
            "phone": "Phone Number",
            "email": "Email",
            "doc_type": "Document Type",
            "doc_issued": "Issued Date",
            "upload": "Upload File",
            "education": "Education Level",
            "job_title": "Current Job Title / Position",
            "experience_years": "Years of Work Experience",
            "skills": "Special Skills",
            "org_name": "Organization / Company Name",
            "membership_type": "Select Membership Type",
            "father": "Father’s Name",
            "mother": "Mother’s Name",
            "spouse": "Spouse Name",
            "children": "Children (Number / Names)",
            "em_name": "Name",
            "em_relation": "Relationship",
            "em_phone": "Phone Number",
            "em_address": "Address",
            "pay_method": "Payment Method",
            "transaction_id": "Transaction ID",
            "payment_file": "Upload Payment Proof",
            "agree": "I hereby declare that all information provided is true to the best of my knowledge.",
            "submit": "Submit"
        },
        "doc_types": ["Citizenship", "Driving License", "PAN Card", "Voter ID", "National ID", "Passport"],
        "education_opts": ["Literate", "SLC / SEE", "10+2", "Bachelors", "Masters", "PhD"],
        "membership_opts": ["General Member", "Life Member", "Honorary Member"],
        "payment_opts": ["eSewa", "Khalti", "ConnectIPS", "Bank Transfer"],
        "success": "Thank you for registering as a member of Jirel Association Nepal.",
        "next": "Next",
        "prev": "Previous",
        "save": "Save & Continue",
        "finish": "Finish"
    },
    "ne": {
        "lang_name": "नेपाली",
        "take_membership": "सदस्यता लिनुहोस्",
        "sections": {
            "language": "भाषा छान्नुहोस्",
            "member_info": "सदस्यको विवरण",
            "contact": "सम्पर्क विवरण",
            "gov_doc": "सरकारी प्रमाणपत्र अपलोड",
            "education": "शैक्षिक योग्यता",
            "professional": "व्यावसायिक सीप / दक्षता",
            "membership": "सदस्यता प्रकार",
            "family": "परिवार विवरण",
            "emergency": "आपतकालीन सम्पर्क व्यक्ति",
            "payment": "सदस्यता भुक्तानी",
            "declaration": "घोषणा",
            "review": "समिक्षा र पेश गर्नुहोस्"
        },
        "fields": {
            "name": "नाम",
            "full_name_en": "अंग्रेजीमा पूरा नाम",
            "dob": "जन्म मिति (वि.सं.)",
            "dob_ad": "जन्म मिति (ई.सं.)",
            "gender": "लिङ्ग",
            "male": "पुरुष",
            "female": "महिला",
            "others": "अन्य",
            "occupation": "पेशा",
            "perm_address": "स्थायी ठेगाना",
            "temp_address": "अस्थायी ठेगाना",
            "phone": "फोन नं.",
            "email": "इमेल",
            "doc_type": "कागजातको प्रकार",
            "doc_issued": "जारि मिति",
            "upload": "फाइल अपलोड",
            "education": "शैक्षिक स्तर",
            "job_title": "हालको पद / पदनाम",
            "experience_years": "कामको अनुभव (वर्ष)",
            "skills": "विशेष सीप",
            "org_name": "संस्था / कम्पनीको नाम",
            "membership_type": "सदस्यता प्रकार छान्नुहोस्",
            "father": "बाबुको नाम",
            "mother": "आमाको नाम",
            "spouse": "पति/पत्नीको नाम",
            "children": "सन्तान (संख्या / नाम)",
            "em_name": "नाम",
            "em_relation": "सम्बन्ध",
            "em_phone": "फोन नं.",
            "em_address": "ठेगाना",
            "pay_method": "भुक्तानी विधि",
            "transaction_id": "ट्रान्ज्याक्सन आईडी",
            "payment_file": "भुक्तानी प्रमाण अपलोड",
            "agree": "मैले दिएको सम्पूर्ण जानकारी मेरो जानकारी अनुसार सत्य हो भन्ने म घोषणा गर्दछु।",
            "submit": "पेश गर्नुहोस्"
        },
        "doc_types": ["नागरिकता", "सवारी चालक अनुमतिपत्र", "पान कार्ड", "मतदाता परिचयपत्र", "रास्ट्रिय परिचयपत्र", "पासपोर्ट"],
        "education_opts": ["साधारण लेखपढ", "SLC / SEE", "१०+२", "स्नातक", "स्नातकोत्तर", "पिएचडी"],
        "membership_opts": ["साधारण सदस्य", "आजीवन सदस्य", "मानार्थ सदस्य"],
        "payment_opts": ["इसेवा", "खल्ती", "कनेक्टआईपीएस", "बैंक ट्रान्सफर"],
        "success": "जिरेल संघ नेपालको सदस्य बन्नु भएकोमा धन्यवाद।",
        "next": "अर्को",
        "prev": "अघिल्लो",
        "save": "सेभ गरी अघि बढ्नुहोस्",
        "finish": "समाप्त"
    },
    "ji": {
        "lang_name": "जिरेल",
        "take_membership": "सदस्यता लोङ्ग",
        "sections": {
            "language": "भाषा चुन",
            "member_info": "सदस्यते विवरण",
            "contact": "सम्पर्क विवरण",
            "gov_doc": "सरकारी प्रमाणपत्र अपलोड",
            "education": "शैक्षिक थ्योबो",
            "professional": "व्यावसायिक सीप",
            "membership": "सदस्यते प्रकार",
            "family": "परिवार विवरण",
            "emergency": "आपतकालीन सम्पर्क व्यक्ति",
            "payment": "सदस्यता भुक्तानी",
            "declaration": "घोषणा",
            "review": "हेलाइ र पेश लोङ्ग"
        },
        "fields": {
            "name": "म्यिन",
            "full_name_en": "अंग्रेजीला पूरा म्यिन",
            "dob": "केबाते मिति (वि.सं.)",
            "dob_ad": "केबाते मिति (ई.सं.)",
            "gender": "लिङ्ग",
            "male": "ख्योबो म्यी",
            "female": "फेम्बे म्यी",
            "others": "जेन",
            "occupation": "पेशा",
            "perm_address": "स्थायी थलो",
            "temp_address": "अस्थायी थलो",
            "phone": "फोन नं.",
            "email": "इमेल",
            "doc_type": "कागजात प्रकार",
            "doc_issued": "जारी खाबते मिति",
            "upload": "फाइल अपलोड",
            "education": "शैक्षिक स्तर",
            "job_title": "हालको पद",
            "experience_years": "काम अनुभव (वर्ष)",
            "skills": "विशेष सीप",
            "org_name": "संस्था / कम्पनी",
            "membership_type": "सदस्यते प्रकार छान्नुहोस्",
            "father": "बुबा म्यिन",
            "mother": "आमा म्यिन",
            "spouse": "जोडी म्यिन",
            "children": "सन्तान (संख्या / नाम)",
            "em_name": "म्यिन",
            "em_relation": "सम्बन्ध",
            "em_phone": "फोन नं.",
            "em_address": "ठेगाना",
            "pay_method": "भुक्तानी विधि",
            "transaction_id": "लेनदेन आईडी",
            "payment_file": "भुक्तानी प्रमाण अपलोड",
            "agree": "ङा दिआ जानकारी सारा सत्य बा थोक मा घोषणा लाङ।",
            "submit": "पेश लोङ्ग"
        },
        "doc_types": ["नागरिकता", "सवारी चालक अनुमतिपत्र", "पान कार्ड", "मतदाता परिचयपत्र", "रास्ट्रिय परिचयपत्र", "पासपोर्ट"],
        "education_opts": ["साधारण लेखापढी", "SLC / SEE", "१०+२", "स्नातक", "स्नातकोत्तर", "पिएचडी"],
        "membership_opts": ["साधारण सदस्य", "आजीवन सदस्य", "मानार्थ सदस्य"],
        "payment_opts": ["इसेवा", "खल्ती", "कनेक्टआईपीएस", "बैंक ट्रान्सफर"],
        "success": "जिरेल संघ नेपाल ला धन्यवाद।",
        "next": "अगाडि",
        "prev": "पाछाडि",
        "save": "सेभ करी अघि जाम",
        "finish": "समाप्त"
    }
}

# ------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTS


def save_upload(file_storage):
    if not file_storage or file_storage.filename == "":
        return None
    if not allowed_file(file_storage.filename):
        return None
    safe = secure_filename(file_storage.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe}"
    path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file_storage.save(path)
    return unique_name


def L():
    """Current labels based on session language."""
    lang = session.get("lang", "en")
    return LABELS.get(lang, LABELS["en"])


def get_form():
    session.setdefault("form", {})
    return session["form"]

# ------------------------------------------------------------------
# Templates (inline via render_template_string for single-file simplicity)
# ------------------------------------------------------------------

BASE_TPL = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{{ title }}</title>
  <style>
    body{font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 2rem;}
    .card{max-width: 900px; margin: 0 auto; padding: 1.5rem; border: 1px solid #ddd; border-radius: 14px;}
    h1{margin-top:0}
    .row{display:grid; grid-template-columns: 1fr 1fr; gap: 1rem;}
    label{display:block; font-weight:600; margin-bottom: .35rem}
    input, select, textarea{width:100%; padding:.6rem .7rem; border:1px solid #ccc; border-radius:10px}
    textarea{min-height:90px}
    .actions{display:flex; gap:.5rem; margin-top:1rem}
    button{padding:.7rem 1rem; border-radius:10px; border:1px solid #999; background:#111; color:#fff; cursor:pointer}
    .ghost{background:#fff; color:#111}
    .hint{color:#666; font-size:.9rem}
    .divider{height:1px; background:#eee; margin:1.25rem 0}
    .success{padding:1rem; background:#f0fff4; border:1px solid #c6f6d5; border-radius:10px}
  </style>
</head>
<body>
  <div class="card">
    {% with m = get_flashed_messages() %}
      {% if m %}<div class="success">{{ m[0] }}</div>{% endif %}
    {% endwith %}
    {{ body|safe }}
  </div>
</body>
</html>
"""


def page(title: str, body: str):
    return render_template_string(BASE_TPL, title=title, body=body)

# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@app.route("/")
def index():
    # Step 1: choose language
    body = f"""
    <h1>{L()['sections']['language']}</h1>
    <form method=post action="{url_for('set_language')}">
      <div class=row>
        <div>
          <label>Language</label>
          <select name="lang">
            <option value="en">English</option>
            <option value="ne">नेपाली</option>
            <option value="ji">जिरेल</option>
          </select>
        </div>
      </div>
      <div class=actions>
        <button type=submit>{L()['next']}</button>
      </div>
    </form>
    """
    return page("Choose Language", body)


@app.route("/set-language", methods=["POST"])
def set_language():
    lang = request.form.get("lang", "en")
    session["lang"] = lang
    session["form"] = {}
    return redirect(url_for("step", n=2))


@app.route("/step/<int:n>", methods=["GET", "POST"])
def step(n: int):
    f = get_form()

    # handle navigation for POST
    if request.method == "POST":
        action = request.form.get("action", "next")
        # collect fields based on step
        if n == 2:
            for k in ["name", "full_name_en", "dob_bs", "dob_ad", "gender", "occupation"]:
                f[k] = request.form.get(k, "")
        elif n == 3:
            for k in ["perm_address", "temp_address", "phone", "email"]:
                f[k] = request.form.get(k, "")
        elif n == 4:
            for k in ["doc_type", "doc_issued_date"]:
                f[k] = request.form.get(k, "")
            # upload doc file
            doc_file = request.files.get("doc_file")
            saved = save_upload(doc_file)
            if saved:
                f["doc_file"] = saved
        elif n == 5:
            for k in ["education"]:
                f[k] = request.form.get(k, "")
        elif n == 6:
            for k in ["job_title", "experience_years", "skills", "org_name"]:
                f[k] = request.form.get(k, "")
        elif n == 7:
            for k in ["father_name", "mother_name", "spouse_name", "children", "em_name", "em_relation", "em_phone", "em_address"]:
                f[k] = request.form.get(k, "")
        elif n == 8:
            for k in ["membership_type", "pay_method", "transaction_id", "declaration"]:
                f[k] = request.form.get(k, "")
            pay_file = request.files.get("payment_file")
            saved = save_upload(pay_file)
            if saved:
                f["payment_file"] = saved
        session.modified = True

        if action == "prev":
            return redirect(url_for("step", n=max(2, n-1)))
        else:
            return redirect(url_for("step", n=min(9, n+1)))

    # render step pages
    S = L()["sections"]
    F = L()["fields"]

    if n == 2:
        body = f"""
        <h1>{S['member_info']}</h1>
        <form method=post>
          <div class=row>
            <div><label>{F['name']}</label><input name=name value="{f.get('name','')}" required></div>
            <div><label>{F['full_name_en']}</label><input name=full_name_en value="{f.get('full_name_en','')}"></div>
            <div><label>{F['dob']}</label><input name=dob_bs placeholder="YYYY-MM-DD" value="{f.get('dob_bs','')}"></div>
            <div><label>{F['dob_ad']}</label><input type=date name=dob_ad value="{f.get('dob_ad','')}"></div>
            <div><label>{F['gender']}</label>
              <select name=gender>
                <option { 'selected' if f.get('gender')==F['male'] else '' } value="{F['male']}">{F['male']}</option>
                <option { 'selected' if f.get('gender')==F['female'] else '' } value="{F['female']}">{F['female']}</option>
                <option { 'selected' if f.get('gender')==F['others'] else '' } value="{F['others']}">{F['others']}</option>
              </select>
            </div>
            <div><label>{F['occupation']}</label><input name=occupation value="{f.get('occupation','')}"></div>
          </div>
          <div class=actions>
            <button class=ghost name=action value=prev type=submit>{L()['prev']}</button>
            <button name=action value=next type=submit>{L()['next']}</button>
          </div>
        </form>
        """
        return page(S['member_info'], body)

    if n == 3:
        body = f"""
        <h1>{S['contact']}</h1>
        <form method=post>
          <div class=row>
            <div><label>{F['perm_address']}</label><input name=perm_address value="{f.get('perm_address','')}"></div>
            <div><label>{F['temp_address']}</label><input name=temp_address value="{f.get('temp_address','')}"></div>
            <div><label>{F['phone']}</label><input name=phone value="{f.get('phone','')}"></div>
            <div><label>{F['email']}</label><input type=email name=email value="{f.get('email','')}"></div>
          </div>
          <div class=actions>
            <button class=ghost name=action value=prev type=submit>{L()['prev']}</button>
            <button name=action value=next type=submit>{L()['next']}</button>
          </div>
        </form>
        """
        return page(S['contact'], body)

    if n == 4:
        opts = "".join([f"<option {'selected' if f.get('doc_type')==o else ''} value='{o}'>{o}</option>" for o in L()['doc_types']])
        body = f"""
        <h1>{S['gov_doc']}</h1>
        <form method=post enctype=multipart/form-data>
          <div class=row>
            <div><label>{F['doc_type']}</label><select name=doc_type>{opts}</select></div>
            <div><label>{F['doc_issued']}</label><input name=doc_issued_date placeholder="YYYY-MM-DD" value="{f.get('doc_issued_date','')}"></div>
            <div><label>{F['upload']}</label><input type=file name=doc_file></div>
            { f"<div><span class='hint'>Saved: {f.get('doc_file')}</span></div>" if f.get('doc_file') else '' }
          </div>
          <div class=actions>
            <button class=ghost name=action value=prev type=submit>{L()['prev']}</button>
            <button name=action value=next type=submit>{L()['next']}</button>
          </div>
        </form>
        """
        return page(S['gov_doc'], body)

    if n == 5:
        opts = "".join([f"<option {'selected' if f.get('education')==o else ''} value='{o}'>{o}</option>" for o in L()['education_opts']])
        body = f"""
        <h1>{S['education']}</h1>
        <form method=post>
          <div class=row>
            <div><label>{F['education']}</label><select name=education>{opts}</select></div>
          </div>
          <div class=actions>
            <button class=ghost name=action value=prev type=submit>{L()['prev']}</button>
            <button name=action value=next type=submit>{L()['next']}</button>
          </div>
        </form>
        """
        return page(S['education'], body)

    if n == 6:
        body = f"""
        <h1>{S['professional']}</h1>
        <form method=post>
          <div class=row>
            <div><label>{F['job_title']}</label><input name=job_title value="{f.get('job_title','')}"></div>
            <div><label>{F['experience_years']}</label><input name=experience_years value="{f.get('experience_years','')}"></div>
            <div style="grid-column:1/-1"><label>{F['skills']}</label><textarea name=skills>{f.get('skills','')}</textarea></div>
            <div style="grid-column:1/-1"><label>{F['org_name']}</label><input name=org_name value="{f.get('org_name','')}"></div>
          </div>
          <div class=actions>
            <button class=ghost name=action value=prev type=submit>{L()['prev']}</button>
            <button name=action value=next type=submit>{L()['next']}</button>
          </div>
        </form>
        """
        return page(S['professional'], body)

    if n == 7:
        body = f"""
        <h1>{S['family']} & {S['emergency']}</h1>
        <form method=post>
          <div class=row>
            <div><label>{F['father']}</label><input name=father_name value="{f.get('father_name','')}"></div>
            <div><label>{F['mother']}</label><input name=mother_name value="{f.get('mother_name','')}"></div>
            <div><label>{F['spouse']}</label><input name=spouse_name value="{f.get('spouse_name','')}"></div>
            <div><label>{F['children']}</label><input name=children value="{f.get('children','')}"></div>
            <div><label>{F['em_name']}</label><input name=em_name value="{f.get('em_name','')}"></div>
            <div><label>{F['em_relation']}</label><input name=em_relation value="{f.get('em_relation','')}"></div>
            <div><label>{F['em_phone']}</label><input name=em_phone value="{f.get('em_phone','')}"></div>
            <div><label>{F['em_address']}</label><input name=em_address value="{f.get('em_address','')}"></div>
          </div>
          <div class=actions>
            <button class=ghost name=action value=prev type=submit>{L()['prev']}</button>
            <button name=action value=next type=submit>{L()['next']}</button>
          </div>
        </form>
        """
        return page(S['family'], body)

    if n == 8:
        m_opts = "".join([f"<option {'selected' if f.get('membership_type')==o else ''} value='{o}'>{o}</option>" for o in L()['membership_opts']])
        p_opts = "".join([f"<option {'selected' if f.get('pay_method')==o else ''} value='{o}'>{o}</option>" for o in L()['payment_opts']])
        checked = "checked" if f.get("declaration") == "yes" else ""
        body = f"""
        <h1>{S['membership']} & {S['payment']}</h1>
        <form method=post enctype=multipart/form-data>
          <div class=row>
            <div><label>{F['membership_type']}</label><select name=membership_type>{m_opts}</select></div>
            <div><label>{F['pay_method']}</label><select name=pay_method>{p_opts}</select></div>
            <div><label>{F['transaction_id']}</label><input name=transaction_id value="{f.get('transaction_id','')}"></div>
            <div><label>{F['payment_file']}</label><input type=file name=payment_file></div>
            { f"<div><span class='hint'>Saved: {f.get('payment_file')}</span></div>" if f.get('payment_file') else '' }
          </div>
          <div class=divider></div>
          <label><input type=checkbox name=declaration value=yes {checked}> {F['agree']}</label>
          <div class=actions>
            <button class=ghost name=action value=prev type=submit>{L()['prev']}</button>
            <button name=action value=next type=submit>{L()['next']}</button>
          </div>
        </form>
        """
        return page(S['payment'], body)

    if n == 9:
        # Review page
        def fmt_file(key):
            fname = get_form().get(key)
            if not fname:
                return "—"
            return f"<a href='{url_for('uploaded', filename=fname)}' target=_blank>{fname}</a>"

        body = f"""
        <h1>{S['review']}</h1>
        <div class=hint>Review your details below. Click Previous to make changes or Finish to submit.</div>
        <div class=divider></div>
        <h3>{S['member_info']}</h3>
        <ul>
          <li>{F['name']}: {f.get('name','')}</li>
          <li>{F['full_name_en']}: {f.get('full_name_en','')}</li>
          <li>{F['dob']}: {f.get('dob_bs','')}</li>
          <li>{F['dob_ad']}: {f.get('dob_ad','')}</li>
          <li>{F['gender']}: {f.get('gender','')}</li>
          <li>{F['occupation']}: {f.get('occupation','')}</li>
        </ul>
        <h3>{S['contact']}</h3>
        <ul>
          <li>{F['perm_address']}: {f.get('perm_address','')}</li>
          <li>{F['temp_address']}: {f.get('temp_address','')}</li>
          <li>{F['phone']}: {f.get('phone','')}</li>
          <li>{F['email']}: {f.get('email','')}</li>
        </ul>
        <h3>{S['gov_doc']}</h3>
        <ul>
          <li>{F['doc_type']}: {f.get('doc_type','')}</li>
          <li>{F['doc_issued']}: {f.get('doc_issued_date','')}</li>
          <li>{F['upload']}: {fmt_file('doc_file')}</li>
        </ul>
        <h3>{S['education']}</h3>
        <ul>
          <li>{F['education']}: {f.get('education','')}</li>
        </ul>
        <h3>{S['professional']}</h3>
        <ul>
          <li>{F['job_title']}: {f.get('job_title','')}</li>
          <li>{F['experience_years']}: {f.get('experience_years','')}</li>
          <li>{F['skills']}: {f.get('skills','')}</li>
          <li>{F['org_name']}: {f.get('org_name','')}</li>
        </ul>
        <h3>{S['family']}</h3>
        <ul>
          <li>{F['father']}: {f.get('father_name','')}</li>
          <li>{F['mother']}: {f.get('mother_name','')}</li>
          <li>{F['spouse']}: {f.get('spouse_name','')}</li>
          <li>{F['children']}: {f.get('children','')}</li>
        </ul>
        <h3>{S['emergency']}</h3>
        <ul>
          <li>{F['em_name']}: {f.get('em_name','')}</li>
          <li>{F['em_relation']}: {f.get('em_relation','')}</li>
          <li>{F['em_phone']}: {f.get('em_phone','')}</li>
          <li>{F['em_address']}: {f.get('em_address','')}</li>
        </ul>
        <h3>{S['payment']}</h3>
        <ul>
          <li>{F['pay_method']}: {f.get('pay_method','')}</li>
          <li>{F['transaction_id']}: {f.get('transaction_id','')}</li>
          <li>{F['payment_file']}: {fmt_file('payment_file')}</li>
        </ul>
        <div class=divider></div>
        <form method=post action="{url_for('final_submit')}">
          <div class=actions>
            <a href="{url_for('step', n=8)}"><button class=ghost type=button>{L()['prev']}</button></a>
            <button type=submit>{L()['finish']}</button>
          </div>
        </form>
        """
        return page(S['review'], body)

    # fallback redirect
    return redirect(url_for("index"))


@app.route("/submit", methods=["POST"])  # not used directly in wizard, kept for safety

def final_submit():
    f = get_form()
    if not f.get("name"):
        flash("Session expired or incomplete. Please start again.")
        return redirect(url_for("index"))

    # Create DB row
    db = DBSession()
    try:
        dob_ad_val = None
        if f.get("dob_ad"):
            try:
                dob_ad_val = datetime.strptime(f["dob_ad"], "%Y-%m-%d").date()
            except ValueError:
                dob_ad_val = None

        m = Member(
            lang=session.get("lang", "en"),
            name=f.get("name"),
            full_name_en=f.get("full_name_en"),
            dob_bs=f.get("dob_bs"),
            dob_ad=dob_ad_val,
            gender=f.get("gender"),
            occupation=f.get("occupation"),
            perm_address=f.get("perm_address"),
            temp_address=f.get("temp_address"),
            phone=f.get("phone"),
            email=f.get("email"),
            doc_type=f.get("doc_type"),
            doc_issued_date=f.get("doc_issued_date"),
            doc_file=f.get("doc_file"),
            education=f.get("education"),
            job_title=f.get("job_title"),
            experience_years=f.get("experience_years"),
            skills=f.get("skills"),
            org_name=f.get("org_name"),
            membership_type=f.get("membership_type"),
            father_name=f.get("father_name"),
            mother_name=f.get("mother_name"),
            spouse_name=f.get("spouse_name"),
            children=f.get("children"),
            em_name=f.get("em_name"),
            em_relation=f.get("em_relation"),
            em_phone=f.get("em_phone"),
            em_address=f.get("em_address"),
            pay_method=f.get("pay_method"),
            transaction_id=f.get("transaction_id"),
            payment_file=f.get("payment_file"),
            declaration=f.get("declaration"),
        )
        db.add(m)
        db.commit()
        session.pop("form", None)
        return redirect(url_for("thankyou"))
    except Exception as e:
        db.rollback()
        flash(f"Error saving submission: {e}")
        return redirect(url_for("step", n=9))
    finally:
        db.close()


@app.route("/thank-you")
def thankyou():
    msg = L()["success"]
    body = f"""
    <h1>✔️ {msg}</h1>
    <p><a href="{url_for('index')}">Start a new submission</a></p>
    """
    return page("Thank You", body)


@app.route("/uploads/<path:filename>")
def uploaded(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    import os
    app.run(
        debug=True, 
        host="0.0.0.0",  # allows the app to be accessed publicly
        port=int(os.environ.get("PORT", 5000))  # host chooses the port
    )
