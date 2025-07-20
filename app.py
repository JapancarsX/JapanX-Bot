import os
import smtplib
import sqlite3
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, request, session
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "randomsecret")

TUEV_CONTACT_LINK = "https://wa.me/4915738099687"
TUEV_CONTACT_NAME = "183 cars"
DB_FILE = "user_state.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(
            "CREATE TABLE IF NOT EXISTS finished_users (number TEXT PRIMARY KEY, until DATETIME)"
        )
        conn.commit()

init_db()

def set_finished(number):
    until = datetime.now() + timedelta(days=3)
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO finished_users (number, until) VALUES (?, ?)",
            (number, until.isoformat()),
        )
        conn.commit()

def get_finished_until(number):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT until FROM finished_users WHERE number = ?", (number,))
        row = c.fetchone()
        if row:
            return datetime.fromisoformat(row[0])
        return None

def clear_finished(number):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM finished_users WHERE number = ?", (number,))
        conn.commit()

def send_email(subject, body):
    from_email = os.environ.get('EMAIL_USER')
    from_password = os.environ.get('EMAIL_PASS')
    to_email = os.environ.get('EMAIL_RECEIVER')
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    text = f"{subject}\n\n{body}"
    body_html = body.replace('\n', '<br>')

    html = f"""
    <html>
      <body>
        <h2 style="color:#333; font-size:1.4em;">Neue Fahrzeugsuche-Anfrage über WhatsApp</h2>
        <p><b>Kundendaten:</b></p>
        <div style="font-size:1.1em; font-family:Arial, sans-serif;">
            {body_html}
        </div>
      </body>
    </html>
    """

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    msg.attach(part1)
    msg.attach(part2)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(from_email, from_password)
        server.send_message(msg)

@app.route('/whatsapp', methods=['POST'])
def whatsapp():
    incoming_msg = request.values.get('Body', '').strip()
    lower_msg = incoming_msg.lower()
    customer_number = request.values.get('From')
    resp = MessagingResponse()
    msg = resp.message()

    finished_until = get_finished_until(customer_number)
    now = datetime.now()

    # Session-Blockierung nach Abschluss
    if finished_until and finished_until > now:
        if lower_msg in ['menü', 'menu']:
            clear_finished(customer_number)
            session.clear()
            msg.body(
                "👋 Willkommen bei JapanX Import GmbH!\n"
                "Wie können wir Ihnen weiterhelfen? Bitte wählen Sie eine der folgenden Optionen:\n\n"
                "1️⃣ Fahrzeugsuche\n"
                "2️⃣ TÜV- & Serviceanfrage\n\n"
                "👉 Antworten Sie einfach mit 1 oder 2.\n\n"
                "Liebe Grüße\n"
                "Ihr JapanX Import Team"
            )
            return str(resp)
        else:
            return str(resp)

    # Ablaufende Session wird zurückgesetzt
    if finished_until and finished_until <= now:
        clear_finished(customer_number)
        session.clear()

    # Menü explizit anfordern
    if lower_msg in ['menü', 'menu']:
        clear_finished(customer_number)
        session.clear()
        msg.body(
            "👋 Willkommen bei JapanX Import GmbH!\n"
            "Wie können wir Ihnen weiterhelfen? Bitte wählen Sie eine der folgenden Optionen:\n\n"
            "1️⃣ Fahrzeugsuche\n"
            "2️⃣ TÜV- & Serviceanfrage\n\n"
            "👉 Antworten Sie einfach mit 1 oder 2.\n\n"
            "Liebe Grüße\n"
            "Ihr JapanX Import Team"
        )
        return str(resp)

    # Begrüßung / Menü bei Erstkontakt oder Reset
    if lower_msg in ['start', 'hallo', 'hi', 'help']:
        session.clear()
        msg.body(
            "👋 Willkommen bei JapanX Import GmbH!\n"
            "Wie können wir Ihnen weiterhelfen? Bitte wählen Sie eine der folgenden Optionen:\n\n"
            "1️⃣ Fahrzeugsuche\n"
            "2️⃣ TÜV- & Serviceanfrage\n\n"
            "👉 Antworten Sie einfach mit 1 oder 2.\n\n"
            "Liebe Grüße\n"
            "Ihr JapanX Import Team"
        )
        return str(resp)

    # Fahrzeugsuche Menü (Option 1)
    if lower_msg in ['1', '1️⃣', 'fahrzeugsuche']:
        session["step"] = "fahrzeugsuche"
        msg.body(
            "🚗 Vielen Dank für Ihre Anfrage zum Fahrzeugimport!\n"
            "Damit wir gezielt nach passenden Angeboten suchen können, senden Sie uns bitte folgende Informationen zu Ihrem Wunschfahrzeug:\n\n"
            "🔹 Marke & Modell\n"
            "📉 Max. Kilometerstand\n"
            "📅 +/- Baujahr\n"
            "⭐ Besondere Wünsche oder Ausstattung\n\n"
            "Sobald Ihre Angaben bei uns eingehen, prüfen wir verfügbare Optionen und melden uns zeitnah mit passenden Vorschlägen zurück."
        )
        return str(resp)

    # TÜV & Serviceanfrage (Option 2)
    if lower_msg in ['2', '2️⃣', 'tüv', 'tüv- & serviceanfrage']:
        set_finished(customer_number)
        session.clear()
        msg.body(
            "🔧 Sie interessieren sich für unseren TÜV- & Servicepartner?\n"
            "Wir leiten Ihre Anfrage gerne an unsere Partnerwerkstatt weiter! 🛠️\n\n"
            "Damit Ihr Anliegen schnell bearbeitet werden kann, senden Sie bitte folgende Infos mit:\n"
            "📝 „TÜV Anfrage“\n"
            "🚗 Marke & Modell\n"
            "📅 Baujahr\n"
            "🌍 Importland\n\n"
            "📲 Direktkontakt zu unserem Partner 183 Cars auf WhatsApp:\n"
            "https://wa.me/4915738099687\n\n"
            "✅ Unser Partner meldet sich zeitnah bei Ihnen!\n\n"
            "📌 Tipp: Schreiben Sie „menü“, um unser Hauptmenü erneut aufzurufen."
        )
        return str(resp)

    # Nach der Auswahl von "Fahrzeugsuche" kommt hier die Fahrzeuganfrage
    if session.get("step") == "fahrzeugsuche":
        try:
            send_email(
                subject="Neue Fahrzeugsuche über WhatsApp-Bot",
                body=f"Absender: {customer_number}\n\n{incoming_msg}"
            )
            msg.body(
                "✅ Vielen Dank für Ihre Angaben!\n"
                "🔍 Wir schauen uns Ihre Wünsche jetzt im Detail an und melden uns in Kürze mit passenden Angeboten bei Ihnen zurück. 🚗📩"
            )
        except Exception as e:
            print("E-Mail Fehler:", e)
            msg.body(
                "Entschuldigung, beim Versenden Ihrer Anfrage ist ein Fehler aufgetreten. Bitte versuchen Sie es später erneut."
            )
        set_finished(customer_number)
        session.clear()
        return str(resp)

    return str(resp)

if __name__ == '__main__':
    app.run(debug=True)
