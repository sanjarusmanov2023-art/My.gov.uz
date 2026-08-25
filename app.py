# -*- coding: utf-8 -*-
"""Private PDF generator web app (Flask).
Generates government-style documents with QR codes.
Only the admin (you) can log in.
"""
import os, io, json, uuid, datetime
from flask import (Flask, request, render_template, session, redirect,
                   url_for, send_file, abort, flash)
from werkzeug.security import generate_password_hash, check_password_hash
from generator import generate

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE, 'templates'))
app.secret_key = os.environ.get('SECRET_KEY', 'change-me-in-production-12345')

# --- Admin credentials (override with env vars in production) ---
ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS_HASH = generate_password_hash(os.environ.get('ADMIN_PASS', 'admin123'))

# In-memory store of generated docs (for /verify). On Render, volatile but fine for demo.
# For persistence you can later swap to SQLite.
DOCS = {}

DOCTYPES = [
    ('qaydvarag', 'QAYD VARAG\'I (yuridik shaxs)'),
    ('employment', 'Ish staji haqida ma\'lumotnoma'),
    ('salary', 'Maosh hisoboti (Certificate of Calculated Wages)'),
]
LANGS = [('uz','O\'zbekcha'),('ru','Русский'),('en','English')]

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username','')
        p = request.form.get('password','')
        if u == ADMIN_USER and check_password_hash(ADMIN_PASS_HASH, p):
            session['user'] = u
            return redirect(url_for('dashboard'))
        flash('Login yoki parol noto\'g\'ri')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', doctypes=DOCTYPES, langs=LANGS)

@app.route('/generate/<doc_type>', methods=['GET','POST'])
def generate_route(doc_type):
    if 'user' not in session:
        return redirect(url_for('login'))
    if doc_type not in [d[0] for d in DOCTYPES]:
        abort(404)
    if request.method == 'POST':
        lang = request.form.get('lang', 'uz')
        data = {k: v for k, v in request.form.items()}
        # parse dynamic lists
        if doc_type == 'qaydvarag':
            founders = []
            i = 0
            while f'founder_name_{i}' in request.form:
                nm = request.form.get(f'founder_name_{i}')
                pc = request.form.get(f'founder_pct_{i}', '100')
                if nm:
                    founders.append((nm, pc))
                i += 1
            data['founders'] = founders
        elif doc_type == 'employment':
            works = []
            i = 0
            while f'work_start_{i}' in request.form:
                works.append({
                    'start': request.form.get(f'work_start_{i}',''),
                    'end': request.form.get(f'work_end_{i}',''),
                    'org': request.form.get(f'work_org_{i}',''),
                    'inn': request.form.get(f'work_inn_{i}',''),
                    'position': request.form.get(f'work_position_{i}',''),
                    'dept': request.form.get(f'work_dept_{i}',''),
                })
                i += 1
            data['works'] = works
        elif doc_type == 'salary':
            rows = []
            i = 0
            while f'sal_year_{i}' in request.form:
                rows.append({
                    'year': request.form.get(f'sal_year_{i}',''),
                    'month': request.form.get(f'sal_month_{i}',''),
                    'org': request.form.get(f'sal_org_{i}',''),
                    'wage': request.form.get(f'sal_wage_{i}',''),
                    'pit': request.form.get(f'sal_pit_{i}',''),
                    'other': request.form.get(f'sal_other_{i}','0'),
                    'inps': request.form.get(f'sal_inps_{i}',''),
                })
                i += 1
            data['salary_rows'] = rows
        try:
            pdf_bytes, docno = generate(doc_type, data, lang)
        except Exception as e:
            flash('Xatolik: ' + str(e))
            return redirect(url_for('generate_route', doc_type=doc_type))
        # store for verify
        DOCS[docno] = {'doc_type': doc_type, 'lang': lang,
                      'created': datetime.datetime.now().isoformat(), 'data': data,
                      'check_code': docno[-4:]}
        # persist to disk cache
        cache_dir = os.path.join(BASE, 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        with open(os.path.join(cache_dir, docno + '.pdf'), 'wb') as f:
            f.write(pdf_bytes)
        return send_file(io.BytesIO(pdf_bytes),
                         mimetype='application/pdf',
                         as_attachment=True,
                         download_name=f'{doc_type}_{docno}.pdf')
    return render_template('generate.html', doc_type=doc_type, langs=LANGS)

@app.route('/verify', methods=['GET','POST'])
def verify():
    doc = request.args.get('doc') or request.form.get('doc','')
    if not doc or doc not in DOCS:
        return render_template('verify.html', found=False)
    info = DOCS[doc]
    if request.method == 'POST':
        code = request.form.get('code','').strip()
        if code == info.get('check_code'):
            # correct -> serve the PDF
            cache_path = os.path.join(BASE, 'cache', doc + '.pdf')
            if os.path.exists(cache_path):
                return send_file(cache_path, mimetype='application/pdf',
                                 as_attachment=True, download_name=f'{info["doc_type"]}_{doc}.pdf')
            pdf_bytes, _ = generate(info['doc_type'], info['data'], info['lang'])
            return send_file(io.BytesIO(pdf_bytes), mimetype='application/pdf',
                             as_attachment=True, download_name=f'{info["doc_type"]}_{doc}.pdf')
        else:
            return render_template('verify.html', found=True, doc=doc, error='Kod noto\'g\'ri. Qaytadan urinib ko\'ring.')
    return render_template('verify.html', found=True, doc=doc, info=info, error=None)

@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
