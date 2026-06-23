import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def authenticate_google():
    """Obsługuje logowanie do Google i zwraca uwierzytelniony serwis."""
    creds = None
    if os.path.exists("../Demos/token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("../Secrets/credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("../Demos/token.json", "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def run_google_demo():
    print("Łączenie z Google Calendar...")
    service = authenticate_google()
    print("Połączono pomyślnie!\n")

    print("Dodaję testowe wydarzenie...")
    now = datetime.datetime.now(datetime.timezone.utc)
    start_time = now.isoformat()
    end_time = (now + datetime.timedelta(hours=1)).isoformat()

    event_body = {
        "summary": "Testowe zadanie z Pythona",
        "description": "Udało się połączyć z API!",
        "start": {
            "dateTime": start_time,
            "timeZone": "Europe/Warsaw",
        },
        "end": {
            "dateTime": end_time,
            "timeZone": "Europe/Warsaw",
        },
    }

    created_event = service.events().insert(calendarId="primary", body=event_body).execute()
    print(f"✅ Utworzono wydarzenie! Link: {created_event.get('htmlLink')}\n")

    print("Pobieram 5 najbliższych wydarzeń z Twojego kalendarza...")
    now_str = datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z")

    events_result = (
        service.events()
        .list(calendarId="primary", timeMin=now_str, maxResults=5, singleEvents=True, orderBy="startTime")
        .execute()
    )

    events = events_result.get("items", [])

    if not events:
        print("Brak nadchodzących wydarzeń.")
        return

    for event in events:
        # Daty całodniowe mają 'date', normalne mają 'dateTime'
        start = event["start"].get("dateTime", event["start"].get("date"))
        print(f" -> {start} | {event['summary']}")


if __name__ == "__main__":
    run_google_demo()
