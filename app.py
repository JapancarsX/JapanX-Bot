from flask import Flask, request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route('/')
def home():
    return "\U0001F697 JapanX WhatsApp-Bot läuft! Verwende /whatsapp für Anfragen."

sessions = {}

import os

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')
EMAIL_RECEIVER = os.environ.get('EMAIL_RECEIVER')

questions = [
    "Willkommen bei Japan X! \U0001F1EF\U0001F1F5\n\n"
    "Ich bin der Chatbot von Japan X. Ich begleite dich auf dem Weg zu deinem Traumauto – schnell, einfach und unverbindlich.\n\n"
    "Bevor wir starten, wähle bitte eine Option:\n"
    "1⃣ Auto suchen\n"
    "2⃣ Informationen zum Ablauf",
    "Welche Automarke suchst du? (z. B. Toyota, Honda, Nissan...)",
    "Welches Modell interessiert dich? (z. B. Civic, Corolla, Skyline...)",
    "Wie hoch darf der maximale Kilometerstand sein? (z. B. unter 100.000 km)",
    "Gibt es besondere Wünsche oder Anforderungen? (z. B. Automatik, Schiebedach, Hybrid...)",
    "Hast du noch weitere Wünsche, die wir berücksichtigen sollen?",
    "Wie lautet dein Vor- und Nachname?",
    "Bitte gib auch deine Handynummer an für die Rückmeldung.",
    "Wie lautet deine E-Mail-Adresse?"
]

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot():
    from_number = request.form.get('From')
    body = request.form.get('Body', '').strip()

    resp = MessagingResponse()

    if from_number not in sessions:
        sessions[from_number] = {'step': 0, 'answers': []}

    session = sessions[from_number]
    step = session['step']

    if step == 0:
        if body.lower() in ['hallo', 'hi', 'hey', 'guten tag', 'servus']:
            question = questions[0]
            session['step'] += 1
            resp.message(question)
            return str(resp)
        else:
            resp.message("Bitte beginne mit 'Hallo', um den Prozess zu starten.")
            return str(resp)

    if step > 0:
        if step == 1 and body == '2':
            session['step'] += 1
            info = (
                "\U0001F501 Japan X begleitet seit 2015 erfolgreich den Import hochwertiger Fahrzeuge aus Japan.\n"
                "Über 100 zufriedene Kunden vertrauen bereits auf unsere Erfahrung und Abwicklung.\n\n"
                "Lass uns jetzt dein Wunschfahrzeug finden! \U0001F60A\n"
                f"{questions[1]}"
            )
            resp.message(info)
            return str(resp)

        if step in [1, 2, 3] and body.lower() in ['egal', 'weiß nicht', 'ka', 'k.a.', 'keine ahnung']:
            resp.message(
                "Bitte gib eine möglichst genaue Angabe, damit wir das passende Fahrzeug für dich finden können.\n"
                f"{questions[step]}"
            )
            return str(resp)

        session['answers'].append(body)

    if step >= len(questions) - 1:
        send_email(session['answers'], from_number)
        del sessions[from_number]
        abschied = (
            "Vielen Dank für deine Angaben! \U0001F64F\n\n"
            "Wir haben deine Anfrage per E-Mail erfasst und an unser Team weitergeleitet."
            "\nDie weitere Kommunikation erfolgt per E-Mail – du erhältst schnellstmöglich eine Rückmeldung. \U0001F4E7"
        )
        resp.message(abschied)
        return str(resp)

    session['step'] += 1
    resp.message(questions[session['step']])
    return str(resp)

def send_email(answers, user_id):
    msg = MIMEMultipart("alternative")
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = 'Neue Fahrzeuganfrage von WhatsApp'

    labels = [
        "Marke", "Modell", "Kilometerstand", "Sonderwünsche",
        "Weitere Wünsche", "Name", "Handynummer", "E-Mail"
    ]

    rows = "".join([
        f"<tr><td><strong>{label}:</strong></td><td>{answer}</td></tr>"
        for label, answer in zip(labels, answers)
    ])

    html = f"""
    <html>
      <body>
        <div style='text-align: center;'>
          <img src="https://i.imgur.com/DWJzPbe.png" alt="Japan X Logo" style="max-width:200px; display:block; margin: 0 auto 20px;" />
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
