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

# --- Initialisiere SQLite-Datenbank ---
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

# --- E-Mail-Sende-Funktion ---
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

    html = f"""
    <html>
      <body>
        <h2 style="color:#333; font-size:1.4em;">Neue Fahrzeugsuche-Anfrage über WhatsApp</h2>
        <p><b>Kundendaten:</b></p>
        <div style="font-size:1.1em; font-family:Arial, sans-serif;">
            {body.replace('\n', '<br>')}
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

# --- Bot-Handler ---
@app.route('/whatsapp', methods=['POST'])
def whatsapp():
    incoming_msg = request.values.get('Body', '').strip()
    lower_msg = incoming_msg.lower()
    customer_number = request.values.get('From')
    resp = MessagingResponse()
    msg = resp.message()

    # 3-Tage-Session-Check
    finished_until = get_finished_until(customer_number)
    now = datetime.now()

    # User hat abgeschlossen und 3 Tage sind noch nicht vorbei
    if finished_until and finished_until > now:
        if lower_msg in ['menü', 'menu']:
            clear_finished(customer_number)
            session.clear()  # <-- NEU: Session komplett zurücksetzen!
            msg.body(
                "Wie können wir Ihnen helfen? Bitte wählen Sie eine Option:\n\n"
                "1️⃣ Fahrzeugsuche\n"
                "2️⃣ TÜV- & Serviceanfrage\n"
                "3️⃣ Wie funktioniert der Import?\n\n"
                "Antworten Sie einfach mit 1, 2 oder 3."
            )
        return str(resp)

    # Zeit abgelaufen: Session für User zurücksetzen
    if finished_until and finished_until <= now:
        clear_finished(customer_number)
        session.clear()

    # Menü explizit anfordern (funktioniert immer)
    if lower_msg in ['menü', 'menu']:
        clear_finished(customer_number)
        session.clear()  # <-- NEU: Session komplett zurücksetzen!
        msg.body(
            "Wie können wir Ihnen helfen? Bitte wählen Sie eine Option:\n\n"
            "1️⃣ Fahrzeugsuche\n"
            "2️⃣ TÜV- & Serviceanfrage\n"
            "3️⃣ Wie funktioniert der Import?\n\n"
            "Antworten Sie einfach mit 1, 2 oder 3."
        )
        return str(resp)

    # Begrüßung / Menü bei Erstkontakt oder Reset
    if lower_msg in ['start', 'hallo', 'hi', 'help']:
        session.clear()
        msg.body(
            "Willkommen bei JapanX Import GmbH! 👋\n\n"
            "Wie können wir Ihnen helfen? Bitte wählen Sie eine Option:\n\n"
            "1️⃣ Fahrzeugsuche\n"
            "2️⃣ TÜV- & Serviceanfrage\n"
            "3️⃣ Wie funktioniert der Import?\n\n"
            "Wir melden uns in Kürze bei Ihnen.\n\n"
            "Liebe Grüße\n"
            "Ihr JapanX Import Team"
        )
        return str(resp)

    # Fahrzeugsuche Menü
    if lower_msg in ['1', '1️⃣', 'fahrzeugsuche']:
        session["step"] = "fahrzeugsuche"
        msg.body(
            "Super, Sie möchten ein Fahrzeug suchen! 🚗\n\n"
            "Bitte schicken Sie uns einfach eine Nachricht mit diesen Infos zu Ihrem Wunschfahrzeug:\n"
            "- Marke & Modell\n"
            "- Maximaler Kilometerstand\n"
            "- Maximaler Jahrgang/Baujahr\n"
            "- Weitere Wünsche oder Besonderheiten\n\n"
            "Wir prüfen Ihre Anfrage und melden uns schnellstmöglich mit passenden Angeboten zurück."
        )
        return str(resp)

    # TÜV
    if lower_msg in ['2', '2️⃣', 'tüv', 'tüv- & serviceanfrage']:
        set_finished(customer_number)
        session.clear()
        msg.body(
            "Sie interessieren sich für unseren TÜV- & Servicepartner. 🛠️\n\n"
            "Wir leiten Sie gern an unsere Partnerwerkstatt weiter!\n"
            "Wenn Sie möchten, können Sie direkt folgende Infos mitschicken:\n"
            "- 'TÜV Anfrage'\n"
            "- Marke, Modell und Importland\n\n"
            f"Hier geht's direkt zu unserem Partner {TUEV_CONTACT_NAME} auf WhatsApp:\n{TUEV_CONTACT_LINK}\n\n"
            "Unser Partner meldet sich zeitnah bei Ihnen!\n\n"
            "Falls Sie das Menü erneut benötigen, schreiben Sie einfach 'menü'."
        )
        return str(resp)

    # Import Ablauf
    if lower_msg in ['3', '3️⃣', 'ablauf', 'wie funktioniert der import']:
        set_finished(customer_number)
        session.clear()
        msg.body(
            "So funktioniert der Import bei uns:\n\n"
            "1️⃣ Sie teilen uns Ihre Fahrzeugwünsche mit.\n"
            "2️⃣ Wir suchen passende Autos und beraten Sie persönlich.\n"
            "3️⃣ Nach Zusage kümmern wir uns um alle Importformalitäten und die Verzollung.\n"
            "4️⃣ Ihr Fahrzeug kommt sicher in Deutschland an – Sie können es selbst abholen oder sich liefern lassen.\n\n"
            "Bei Fragen sind wir jederzeit für Sie da!\n\n"
            "Falls Sie das Menü erneut benötigen, schreiben Sie einfach 'menü'."
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
                "Vielen Dank für Ihre Angaben! 🙏 Wir prüfen Ihre Anfrage und melden uns zeitnah mit passenden Angeboten bei Ihnen.\n\n"
                "Falls Sie das Menü erneut benötigen, schreiben Sie einfach 'menü'."
            )
        except Exception as e:
            print("E-Mail Fehler:", e)
            msg.body(
                "Entschuldigung, beim Versenden Ihrer Anfrage ist ein Fehler aufgetreten. Bitte versuchen Sie es später erneut."
            )
        set_finished(customer_number)
        session.clear()
        return str(resp)

    # Fallback: Keine Reaktion
    return str(resp)

if __name__ == '__main__':
    app.run(debug=True)
