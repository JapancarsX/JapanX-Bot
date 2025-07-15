from flask import Flask, request
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.twiml.messaging_response import MessagingResponse  # <--- hinzugefügt

app = Flask(__name__)

# Root route for Render deployment
@app.route('/')
def home():
    return "\U0001F697 JapanX WhatsApp-Bot läuft! Verwende /whatsapp für Anfragen."

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
    "Willkommen bei Japan X! \U0001F1EF\U0001F1F5\n\n"
    "Ich bin der Chatbot von Japan X. Ich begleite dich auf dem Weg zu deinem Traumauto – schnell, einfach und unverbindlich.\n\n"
    "Bevor wir starten, wähle bitte eine Option:\n"
    "1⃣ Auto suchen\n"
    "2⃣ Informationen zum Ablauf",
    "Welche Automarke suchst du? (z. B. Toyota, Honda, Nissan...)",
    "Welches Modell interessiert dich? (z. B. Civic, Corolla, Skyline...)",
    "Wie hoch darf der maximale Kilometerstand sein? (z. B. unter 100.000 km)",
    "Gibt es besondere Wünsche oder Anforderungen? (z. B. Automatik, Schiebedach, Hybrid...)"
]

@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot():
    print("INCOMING FORM DATA:", request.form)  # Debug-Ausgabe
    from_number = request.form.get('From')
    body = request.form.get('Body', '').strip().lower()

    resp = MessagingResponse()

    # Initialisiere Session, falls neu
    if from_number not in sessions:
        sessions[from_number] = {'step': 0, 'answers': []}

    session = sessions[from_number]
    step = session['step']

    # Begrüßungserkennung bei Schritt 0
    if step == 0:
        if body in ['hallo', 'hi', 'hey', 'guten tag', 'servus']:
            question = questions[0]
            session['step'] += 1
            resp.message(question)
            return str(resp)
        else:
            resp.message("Bitte beginne mit 'Hallo', um den Prozess zu starten.")
            return str(resp)

    # Speichere Antwort, wenn nicht Begrüßung
    if step > 0:
        # Sonderbehandlung für Option 2 bei Schritt 1
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

        if step in [1, 2, 3] and body in ['egal', 'weiß nicht', 'ka', 'k.a.', 'keine ahnung']:
            resp.message(
                "Bitte gib eine möglichst genaue Angabe, damit wir das passende Fahrzeug für dich finden können.\n"
                f"{questions[step]}"
            )
            return str(resp)

        session['answers'].append(body)

    # Prüfe, ob alle Fragen beantwortet wurden
    if step >= len(questions) - 1:
        send_email(session['answers'], from_number)
        del sessions[from_number]  # Session löschen
        abschied = (
            "Vielen Dank für deine Angaben! \U0001F64F\n\n"
            "Wir haben deine Anfrage per E-Mail erfasst und an unser Team weitergeleitet."
            "\nDie weitere Kommunikation erfolgt per E-Mail – du erhältst schnellstmöglich eine Rückmeldung. \U0001F4E7"
        )
        resp.message(abschied)
        return str(resp)

    # Nächste Frage stellen
    session['step'] += 1
    resp.message(questions[session['step']])
    return str(resp)

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

# App starten (z. B. mit gunicorn oder auf Render)
if __name__ == '__main__':
    app.run(debug=True)
