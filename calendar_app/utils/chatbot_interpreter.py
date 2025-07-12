import spacy
from dateparser.search import search_dates
from datetime import timedelta

nlp = spacy.load("en_core_web_sm")

def interpret_user_message(message):
    doc = nlp(message.lower())
    verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
    nouns = [token.text for token in doc if token.pos_ == "NOUN"]

    if any(v in verbs for v in ["create", "add", "schedule"]):
        title = "Untitled Chatbot Event"
        for chunk in doc.noun_chunks:
            if chunk.root.head.lemma_ in ["create", "add", "schedule"]:
                title = chunk.text.title()
                break

        results = search_dates(
            message,
            settings={
                'PREFER_DATES_FROM': 'future',
                'TIMEZONE': 'Asia/Kolkata',
                'RETURN_AS_TIMEZONE_AWARE': True,
            }
        )

        if not results:
            return {"intent": "create_event", "error": " I couldn’t understand the date/time."}

        _, parsed_time = results[0]

        return {
            "intent": "create_event",
            "title": title,
            "start": parsed_time.isoformat(),
            "end": (parsed_time + timedelta(hours=1)).isoformat()
        }


    elif any(v in verbs for v in ["show", "list", "get", "fetch"]):
        date_result = search_dates(

            message,

            settings={

                'PREFER_DATES_FROM': 'future',

                'TIMEZONE': 'Asia/Kolkata',

                'RETURN_AS_TIMEZONE_AWARE': True,

            }

        )

        if date_result:
            _, date_time = date_result[0]

            return {

                "intent": "fetch_events",

                "date": date_time.date().isoformat()

            }

        return {"intent": "fetch_events"}

    return {"intent": "unknown"}
