import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, request, session
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "randomsecret")

TUEV_CONTACT_LINK = "https://wa.me/4915738099687"
TUEV_CONTACT_NAME = "183 cars"

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
    resp = MessagingResponse()
    msg = resp.message()

    # Menü explizit anfordern
    if lower_msg in ['menü', 'menu']:
        session["step"] = None
        session["finished"] = False
        msg.body(
            "Wie können wir Ihnen helfen? Bitte wählen Sie eine Option:\n\n"
            "1️⃣ Fahrzeugsuche\n"
            "2️⃣ TÜV- & Serviceanfrage\n"
            "3️⃣ Wie funktioniert der Import?\n\n"
            "Antworten Sie einfach mit 1, 2 oder 3."
        )
        return str(resp)

    # Nach Abschluss: Nur noch auf "menü" reagieren!
    if session.get("finished"):
        # Keine Reaktion, außer auf "menü" oben
        return str(resp)

    # Begrüßung / Menü bei Erstkontakt oder Reset
    if lower_msg in ['start', 'hallo', 'hi', 'help']:
        session["step"] = None
        session["finished"] = False
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
        session["finished"] = False
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
        session["step"] = None
        session["finished"] = True
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
        session["step"] = None
        session["finished"] = True
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
            customer_number = request.values.get('From')
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
        session["step"] = None
        session["finished"] = True
        return str(resp)

    # Fallback: Nach dem Abschluss keine weiteren Antworten
    return str(resp)

if __name__ == '__main__':
    app.run(debug=True)
