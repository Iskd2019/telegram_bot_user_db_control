# Minimal Admin Page (Option 2): Flask + SQLAlchemy + Plain HTML Forms
# -------------------------------------------------------------------
# Purpose: List and edit selected columns of `telegram_user_settings`
#          without changing the schema, using simple pages + full reloads.
#
# Editable fields: wants_updates (bool), settlement_points (text[]),
#                  lmp_threshold (numeric), approved_live (bool),
#                  approved_forecast (bool)
#
# Constraints:
#  - settlement_points must be a subset of:
#       {LZ_NORTH, LZ_WEST, LZ_SOUTH, LZ_HOUSTON}
#  - No schema changes
#  - Validate numeric for lmp_threshold
#
# Quick start
# -----------
# 1) Save this file as app.py
# 2) Create a virtualenv & install deps:
#    python -m venv .venv && . .venv/Scripts/activate  # (Windows)
#    # or: source .venv/bin/activate                   # (Linux/macOS)
#    pip install Flask SQLAlchemy psycopg2-binary python-dotenv
# 3) Set environment variable (or edit DATABASE_URL below):
#    set DATABASE_URL=postgresql+psycopg2://odoo:odoo123@10.10.112.106:5432/power
# 4) Run:
#    python app.py
#    # open http://127.0.0.1:8000

# Minimal Admin Page (Option 2): Flask + SQLAlchemy + Plain HTML Forms
from __future__ import annotations
import os
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from functools import wraps
from flask import Flask, request, redirect, url_for, render_template_string, flash, abort
from sqlalchemy import create_engine, BigInteger, Numeric, String
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, Session
from sqlalchemy.dialects.postgresql import ARRAY

ALLOWED_SP = ["LZ_NORTH", "LZ_WEST", "LZ_SOUTH", "LZ_HOUSTON"]
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://odoo:odoo123@10.10.112.106:5432/power",
)
BASIC_AUTH_USER = os.getenv("BASIC_AUTH_USER")
BASIC_AUTH_PASS = os.getenv("BASIC_AUTH_PASS")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def require_auth(f):
    if not BASIC_AUTH_USER or not BASIC_AUTH_PASS:
        return f
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == BASIC_AUTH_USER and auth.password == BASIC_AUTH_PASS):
            return ("Authentication required", 401, {"WWW-Authenticate": "Basic realm='Admin'"})
        return f(*args, **kwargs)
    return wrapper

class Base(DeclarativeBase):
    pass

class TelegramUserSettings(Base):
    __tablename__ = "telegram_user_settings"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    wants_updates: Mapped[Optional[bool]]
    # Use ARRAY(String) (SQLAlchemy type), NOT Python str
    settlement_points: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    lmp_threshold: Mapped[Optional[Decimal]] = mapped_column(Numeric)
    update_frequency: Mapped[Optional[str]]
    approved_live: Mapped[Optional[bool]]
    moreinfo: Mapped[Optional[str]]
    approved_forecast: Mapped[Optional[bool]]

BASE_HTML = r"""
<!doctype html>
<html lang='en'>
<head>
<meta charset='utf-8'>
<title>Telegram User Settings</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial,ui-sans-serif,system-ui;background:#f6f8fa;margin:0}
header{background:#0d1117;color:#fff;padding:14px 20px}
main{padding:20px;max-width:1100px;margin:auto}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden}
th,td{padding:8px;border-bottom:1px solid #e5e7eb;text-align:left;vertical-align:top}
th{background:#f3f4f6}
.btn{background:#0ea5e9;color:#fff;padding:6px 10px;border:none;border-radius:8px;text-decoration:none;display:inline-block}
.btn.gray{background:#64748b}
.flash{padding:8px;border-radius:8px;margin-bottom:10px}
.flash.ok{background:#ecfdf5;color:#065f46}
.flash.err{background:#fef2f2;color:#991b1b}
label{font-weight:600}
input[type="text"],input[type="number"],select{padding:8px;border:1px solid #cbd5e1;border-radius:8px}
</style>
</head>
<body>
<header><strong>Telegram User Settings</strong></header>
<main>
  {% with msgs=get_flashed_messages(with_categories=true) %}
    {% for cat,msg in msgs %}
      <div class="flash {{ 'ok' if cat=='success' else 'err' }}">{{ msg }}</div>
    {% endfor %}
  {% endwith %}
  {{ content|safe }}
</main>
</body>
</html>
"""

INDEX_TPL = r"""
<h2>All Users</h2>
<form method='get' style='margin-bottom:10px'>
  <input type='text' name='q' placeholder='Search by user_id' value='{{request.args.get("q","")}}'>
  <button class='btn' type='submit'>Search</button>
  <a href='{{url_for("index")}}' class='btn gray'>Reset</a>
</form>
<table>
<tr>
  <th>user_id</th><th>wants_updates</th><th>settlement_points</th><th>lmp_threshold</th>
  <th>approved_live</th><th>approved_forecast</th><th>update_frequency</th><th>moreinfo</th><th>Actions</th>
</tr>
{% for row in rows %}
<tr>
  <td>{{row.user_id}}</td>
  <td>{{row.wants_updates}}</td>
  <td>{% if row.settlement_points %}{{row.settlement_points|join(', ')}}{% else %}<em>None</em>{% endif %}</td>
  <td>{{row.lmp_threshold if row.lmp_threshold is not none else ''}}</td>
  <td>{{row.approved_live}}</td>
  <td>{{row.approved_forecast}}</td>
  <td>{{row.update_frequency or ''}}</td>
  <td>{{row.moreinfo or ''}}</td>
  <td><a class='btn' href='{{url_for("edit",user_id=row.user_id)}}'>Edit</a></td>
</tr>
{% endfor %}
</table>
"""

EDIT_TPL = r"""
<h2>Edit user {{row.user_id}}</h2>
<form method='post'>
  <p><label><input type='checkbox' name='wants_updates' value='1' {% if row.wants_updates %}checked{% endif %}> wants_updates</label></p>

  <p>
    <label>settlement_points</label><br>
    <select name='settlement_points' multiple size='4'>
      {% for sp in allowed %}
        <option value='{{sp}}' {% if row.settlement_points and sp in row.settlement_points %}selected{% endif %}>{{sp}}</option>
      {% endfor %}
    </select><br>
    <small>Allowed: {{ allowed|join(', ') }}. Hold Ctrl/Cmd to select multiple.</small>
  </p>

  <p>
    <label>lmp_threshold</label><br>
    <input type='number' step='0.0001' name='lmp_threshold' value='{{row.lmp_threshold if row.lmp_threshold is not none else ""}}'>
  </p>

  <p><label><input type='checkbox' name='approved_live' value='1' {% if row.approved_live %}checked{% endif %}> approved_live</label></p>
  <p><label><input type='checkbox' name='approved_forecast' value='1' {% if row.approved_forecast %}checked{% endif %}> approved_forecast</label></p>

  <p>
    <button class='btn' type='submit'>Save</button>
    <a class='btn gray' href='{{url_for("index")}}'>Cancel</a>
  </p>
</form>
"""

def render_page(content_html: str, **ctx):
    """Render content_html inside BASE_HTML."""
    return render_template_string(BASE_HTML, content=render_template_string(content_html, **ctx))

@app.route("/")
@require_auth
def index():
    q = request.args.get("q","").strip()
    with Session(engine) as s:
        stmt = s.query(TelegramUserSettings)
        if q:
            try:
                stmt = stmt.filter(TelegramUserSettings.user_id == int(q))
            except ValueError:
                flash("Search must be numeric", "error")
        rows = stmt.limit(500).all()
    return render_page(INDEX_TPL, rows=rows, request=request, url_for=url_for)

@app.route("/edit/<int:user_id>", methods=["GET","POST"])
@require_auth
def edit(user_id: int):
    with Session(engine) as s:
        row = s.get(TelegramUserSettings, user_id)
        if not row:
            abort(404)

        if request.method == "POST":
            row.wants_updates = request.form.get("wants_updates") == "1"
            row.approved_live = request.form.get("approved_live") == "1"
            row.approved_forecast = request.form.get("approved_forecast") == "1"

            selected = request.form.getlist("settlement_points")
            if any(v not in ALLOWED_SP for v in selected):
                flash(f"Invalid settlement_points (must be subset of {ALLOWED_SP})", "error")
                return render_page(EDIT_TPL, row=row, allowed=ALLOWED_SP, url_for=url_for)
            row.settlement_points = selected if selected else None

            thr = request.form.get("lmp_threshold", "").strip()
            if thr == "":
                row.lmp_threshold = None
            else:
                try:
                    row.lmp_threshold = Decimal(thr)
                    if row.lmp_threshold < 0:
                        raise InvalidOperation
                except Exception:
                    flash("lmp_threshold must be a non-negative number", "error")
                    return render_page(EDIT_TPL, row=row, allowed=ALLOWED_SP, url_for=url_for)

            s.add(row)
            s.commit()
            flash("Row updated", "success")
            return redirect(url_for("index"))

        return render_page(EDIT_TPL, row=row, allowed=ALLOWED_SP, url_for=url_for)

@app.route("/health")
def health():
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)