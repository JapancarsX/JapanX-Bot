from flask import Flask, request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# Temporäre Speicherung von Sitzungen (pro Nummer)
sessions = {}

# Deine E-Mail-Konfiguration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_USER = 'deine.email@gmail.com'
EMAIL_PASS = 'dein-app-passwort'
EMAIL_RECEIVER = 'empfaenger@email.de'

# Fragen im Ablauf (angepasst)
questions = [
    "Willkommen bei Japan X! 🇯🇵\n\nIch bin der Chatbot von Japan X. Ich begleite dich auf dem Weg zu deinem Traumauto – schnell, einfach und unverbindlich.\n\nBevor wir starten, wähle bitte eine Option:\n1️⃣ Auto suchen\n2️⃣ Informationen zum Ablauf",
    "Welche Automarke suchst du? (z. B. Toyota, Honda, Nissan...)",
    "Welches Modell interessiert dich? (z. B. Civic, Corolla, Skyline...)",
    "Wie hoch darf der maximale Kilometerstand sein? (z. B. unter 100.000 km)",
    "Gibt es besondere Wünsche oder Anforderungen? (z. B. Automatik, Schiebedach, Hybrid...)"
]

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot():
    from_number = request.form.get('From')
    body = request.form.get('Body').strip()

    if from_number not in sessions:
        sessions[from_number] = {'step': 0, 'answers': []}

    session = sessions[from_number]
    step = session['step']

    if step > 0:
        if step == 1 and body.strip() == '2':
            return (
                "🛈 Japan X begleitet seit 2015 erfolgreich den Import hochwertiger Fahrzeuge aus Japan.\n"
                "Über 100 zufriedene Kunden vertrauen bereits auf unsere Erfahrung und Abwicklung.\n\n"
                "Lass uns jetzt dein Wunschfahrzeug finden! 😊\n"
                "Welche Automarke suchst du? (z. B. Toyota, Honda, Nissan...)"
            )
        if step in [1, 2, 3] and body.lower() in ['egal', 'weiß nicht', 'ka', 'k.a.', 'keine ahnung']:
            return (
                "Bitte gib eine möglichst genaue Angabe, damit wir das passende Fahrzeug für dich finden können.\n"
                f"{questions[step - 1]}"
            )

        session['answers'].append(body)

    if step >= len(questions):
        send_email(session['answers'], from_number)
        del sessions[from_number]
        return (
            "Vielen Dank für deine Angaben! 🙏\n\n"
            "Wir haben deine Anfrage per E-Mail erfasst und an unser Team weitergeleitet."
            "\nDie weitere Kommunikation erfolgt per E-Mail – du erhältst schnellstmöglich eine Rückmeldung. 📧"
        )

    question = questions[step]
    session['step'] += 1
    return question

def send_email(answers, user_id):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = 'Neue Fahrzeuganfrage von WhatsApp'

    text = f"Neue Anfrage von: {user_id}\n\n"
    labels = [
        "Marke", "Modell", "Kilometerstand", "Sonderwünsche"
    ]

    for label, answer in zip(labels, answers):
        text += f"{label}: {answer}\n"

    msg.attach(MIMEText(text, 'plain'))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_RECEIVER, msg.as_string())

if __name__ == '__main__':
    app.run(debug=True)
