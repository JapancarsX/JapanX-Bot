from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

TUEV_CONTACT_LINK = "https://wa.me/4915738099687"
TUEV_CONTACT_NAME = "183 cars"

@app.route('/whatsapp', methods=['POST'])
def whatsapp():
    incoming_msg = request.values.get('Body', '').strip().lower()
    resp = MessagingResponse()
    msg = resp.message()

    # Begrüßung & Menü
    if incoming_msg in ['start', 'hallo', 'hi', 'menu', 'menü', 'help']:
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
    # Option 1: Fahrzeugsuche
    elif incoming_msg in ['1', '1️⃣', 'fahrzeugsuche']:
        msg.body(
            "Super, Sie möchten ein Fahrzeug suchen! 🚗\n\n"
            "Bitte schicken Sie uns einfach eine Nachricht mit diesen Infos zu Ihrem Wunschfahrzeug:\n"
            "- Marke & Modell\n"
            "- Maximaler Kilometerstand\n"
            "- Maximaler Jahrgang/Baujahr\n"
            "- Weitere Wünsche oder Besonderheiten\n\n"
            "Wir prüfen Ihre Anfrage und melden uns schnellstmöglich mit passenden Angeboten zurück."
        )
    # Option 2: TÜV- & Serviceanfrage
    elif incoming_msg in ['2', '2️⃣', 'tüv', 'tüv- & serviceanfrage']:
        msg.body(
            "Sie interessieren sich für unseren TÜV- & Servicepartner. 🛠️\n\n"
            "Wir leiten Sie gern an unsere Partnerwerkstatt weiter!\n"
            "Wenn Sie möchten, können Sie direkt folgende Infos mitschicken:\n"
            "- 'TÜV Anfrage'\n"
            "- Marke, Modell und Importland\n\n"
            f"Hier geht's direkt zu unserem Partner {TUEV_CONTACT_NAME} auf WhatsApp:\n{TUEV_CONTACT_LINK}\n\n"
            "Unser Partner meldet sich zeitnah bei Ihnen!"
        )
    # Option 3: Import-Ablauf
    elif incoming_msg in ['3', '3️⃣', 'ablauf', 'wie funktioniert der import']:
        msg.body(
            "So funktioniert der Import bei uns:\n\n"
            "1️⃣ Sie teilen uns Ihre Fahrzeugwünsche mit.\n"
            "2️⃣ Wir suchen passende Autos und beraten Sie persönlich.\n"
            "3️⃣ Nach Zusage kümmern wir uns um alle Importformalitäten und die Verzollung.\n"
            "4️⃣ Ihr Fahrzeug kommt sicher in Deutschland an – Sie können es selbst abholen oder sich liefern lassen.\n\n"
            "Bei Fragen sind wir jederzeit für Sie da!"
        )
    # Fallback bei unbekannter Eingabe
    else:
        msg.body(
            "Bitte wählen Sie eine der folgenden Optionen:\n\n"
            "1️⃣ Fahrzeugsuche\n"
            "2️⃣ TÜV- & Serviceanfrage\n"
            "3️⃣ Wie funktioniert der Import?\n\n"
            "Antworten Sie einfach mit 1, 2 oder 3."
        )
    return str(resp)

if __name__ == '__main__':
    app.run(debug=True)
