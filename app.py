from flask import Flask, request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.twiml.messaging_response import MessagingResponse
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "\U0001F697 JapanX WhatsApp-Bot läuft! Verwende /whatsapp für Anfragen."

sessions = {}

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')
EMAIL_RECEIVER = os.environ.get('EMAIL_RECEIVER')

questions = [
    "Welche Automarke suchst du? (z. B. Toyota, Honda, Nissan...)",
    "Welches Modell interessiert dich? (z. B. Civic, Corolla, Skyline...)",
    "Wie hoch darf der maximale Kilometerstand sein? (z. B. unter 100.000 km)",
    "Gibt es besondere Wünsche oder Anforderungen? (z. B. Automatik, Schiebedach, Hybrid...)",
    "Hast du noch weitere Wünsche, die wir berücksichtigen sollen?",
    "Wie lautet dein Vor- und Nachname?",
    "Wie lautet deine E-Mail-Adresse?"
]

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot():
    from_number = request.form.get('From')
    body = request.form.get('Body', '').strip().lower()

    resp = MessagingResponse()

    if from_number not in sessions:
        sessions[from_number] = {'step': None, 'answers': [], 'mode': None, 'started': False}

    session = sessions[from_number]

    # Begrüßung immer bei neuer Session
    if not session['started']:
        session['started'] = True
        resp.message(
            "Willkommen bei Japan X! 🇯🇵\n\n"
            "Ich bin dein persönlicher Chatbot und helfe dir, dein Traumauto schnell und einfach zu finden.\n\n"
            "Bitte wähle eine Option:\n"
            "1⃣ Auto suchen\n2⃣ Informationen zum Ablauf"
        )
        session['step'] = 'awaiting_choice'
        return str(resp)

    # Benutzerantwort auf die Auswahl
    if session['step'] == 'awaiting_choice':
        if body == '1':
            session['mode'] = 'suche'
            session['step'] = 0
            resp.message(questions[0])
            return str(resp)
        elif body == '2':
            session['mode'] = 'info'
            session['step'] = 'info_ack'
            resp.message(
                "🔧 Seit 2015 importieren wir erfolgreich Fahrzeuge aus Japan.\n"
                "Über 100 zufriedene Kunden vertrauen bereits auf uns.\n\n"
                "Möchtest du jetzt mit der Fahrzeugsuche starten? (Ja/Nein)"
            )
            return str(resp)
        else:
            resp.message("Bitte antworte mit '1' oder '2'.")
            return str(resp)

    if session['step'] == 'info_ack':
        if body == 'ja':
            session['mode'] = 'suche'
            session['step'] = 0
            resp.message(questions[0])
            return str(resp)
        else:
            resp.message("Kein Problem! Wenn du später bereit bist, schreibe einfach 'Hallo'.")
            del sessions[from_number]
            return str(resp)

    # Hauptfragen-Antworten Ablauf
    if session['mode'] == 'suche' and isinstance(session['step'], int):
        session['answers'].append(request.form.get('Body', '').strip())
        session['step'] += 1

        if session['step'] < len(questions):
            resp.message(questions[session['step']])
        else:
            send_email(session['answers'], from_number)
            del sessions[from_number]
            resp.message(
                "Vielen Dank für deine Angaben! 🙏\n\n"
                "Wir haben alles gespeichert und unser Team meldet sich so schnell wie möglich bei dir. 📧"
            )
        return str(resp)

    # Fallback
    resp.message("Etwas ist schiefgelaufen. Bitte starte neu mit 'Hallo'.")
    return str(resp)

def send_email(answers, user_id):
    msg = MIMEMultipart("alternative")
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = 'Neue Fahrzeuganfrage von WhatsApp'

    labels = [
        "Marke", "Modell", "Kilometerstand", "Sonderwünsche",
        "Weitere Wünsche", "Name", "E-Mail"
    ]

    rows = "".join([
        f"<tr><td><strong>{label}:</strong></td><td>{answer}</td></tr>"
        for label, answer in zip(labels, answers)
    ])

    html = f"""
    <html>
      <body>
        <div style='text-align: center;'>
          <img src="https://i.imgur.com/vwgUCFo.png" alt="Japan X Logo" style="max-width:200px; display:block; margin: 0 auto 20px;" />
        </div>
        <h2>Neue WhatsApp-Anfrage</h2>
        <p><strong>Absender:</strong> {user_id}</p>
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
          {rows}
        </table>
      </body>
    </html>
    """

    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_RECEIVER, msg.as_string())

if __name__ == '__main__':
    app.run(debug=True)
