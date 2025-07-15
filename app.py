from flask import Flask, request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# Temporäre Speicherung von Sitzungen (pro Nummer)
sessions = {}

# Deine E-Mail-Konfiguration
import os

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')
EMAIL_RECEIVER = os.environ.get('EMAIL_RECEIVER')

# Fragen im Ablauf (angepasst)
questions = [
    "Willkommen bei Japan X! 🇯🇵\n\n"
    "Ich bin der Chatbot von Japan X. Ich begleite dich auf dem Weg zu deinem Traumauto – schnell, einfach und unverbindlich.\n\n"
    "Bevor wir starten, wähle bitte eine Option:\n"
    "1⃣ Auto suchen\n"
    "2⃣ Informationen zum Ablauf",
    "Welche Automarke suchst du? (z.\u202fB. Toyota, Honda, Nissan...)",
    "Welches Modell interessiert dich? (z.\u202fB. Civic, Corolla, Skyline...)",
    "Wie hoch darf der maximale Kilometerstand sein? (z.\u202fB. unter 100.000 km)",
    "Gibt es besondere Wünsche oder Anforderungen? (z.\u202fB. Automatik, Schiebedach, Hybrid...)"
]

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot():
    from_number = request.form.get('From')
    body = request.form.get('Body').strip()

    # Initialisiere Session, falls neu
    if from_number not in sessions:
        sessions[from_number] = {'step': 0, 'answers': []}

    session = sessions[from_number]
    step = session['step']

    # Speichere Antwort, wenn nicht erster Schritt (Begrüßung)
    if step > 0:
        # Sonderbehandlung für Option 2 bei Schritt 1
        if step == 1 and body.strip() == '2':
            return (
                "🔁 Japan X begleitet seit 2015 erfolgreich den Import hochwertiger Fahrzeuge aus Japan.\n"
                "Über 100 zufriedene Kunden vertrauen bereits auf unsere Erfahrung und Abwicklung.\n\n"
                "Lass uns jetzt dein Wunschfahrzeug finden! 😊\n"
                "Welche Automarke suchst du? (z.\u202fB. Toyota, Honda, Nissan...)"
            )
        # Validierung für Schritt 1–3
        if step in [1, 2, 3] and body.lower() in ['egal', 'weiß nicht', 'ka', 'k.a.', 'keine ahnung']:
            return (
                "Bitte gib eine möglichst genaue Angabe, damit wir das passende Fahrzeug für dich finden können.\n"
                f"{questions[step - 1]}"
            )

        session['answers'].append(body)

    # Prüfe, ob alle Fragen beantwortet wurden
    if step >= len(questions):
        send_email(session['answers'], from_number)
        del sessions[from_number]  # Session löschen
        return (
            "Vielen Dank für deine Angaben! 🙏\n\n"
            "Wir haben deine Anfrage per E-Mail erfasst und an unser Team weitergeleitet."
            "\nDie weitere Kommunikation erfolgt per E-Mail – du erhältst schnellstmöglich eine Rückmeldung. 📧"
        )

    # Nächste Frage stellen
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

# App starten (z.\u202fB. mit gunicorn oder auf Render)
if __name__ == '__main__':
    app.run(debug=True)
