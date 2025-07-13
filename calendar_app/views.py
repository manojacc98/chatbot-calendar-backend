import os
import requests
import jwt
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import GoogleUserToken
import spacy
from .utils.chatbot_interpreter import interpret_user_message
nlp = spacy.load("en_core_web_sm")


import re
import pytz
from pytz import timezone
from datetime import timedelta
import dateparser

def google_login(request):
    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    client_id = settings.GOOGLE_CLIENT_ID
    scope = (
        "https://www.googleapis.com/auth/calendar "
        "https://www.googleapis.com/auth/userinfo.email "
        "https://www.googleapis.com/auth/userinfo.profile "
        "openid"
    )

    auth_url = (
        f"{base_url}?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&access_type=offline"
        f"&include_granted_scopes=true"
        f"&prompt=consent"
    )

    return redirect(auth_url)



def google_callback(request):
    code = request.GET.get('code')
    if not code:
        return JsonResponse({"error": "Missing code"}, status=400)

    data = {
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'grant_type': 'authorization_code'
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post("https://oauth2.googleapis.com/token", data=data, headers=headers)
    token_info = response.json()

    if 'id_token' not in token_info:
        return JsonResponse({"error": "Missing id_token", "details": token_info}, status=400)

    try:
        decoded_token = jwt.decode(token_info['id_token'], options={"verify_signature": False})
        email = decoded_token.get("email")
    except Exception as e:
        return JsonResponse({"error": f"Failed to decode token: {str(e)}"}, status=400)

    if not email:
        return JsonResponse({"error": "Email not found in token"}, status=400)

    GoogleUserToken.objects.update_or_create(
        email=email,
        defaults={
            'access_token': token_info['access_token'],
            'refresh_token': token_info.get('refresh_token', ''),
            'expires_in': token_info['expires_in'],
            'token_type': token_info['token_type'],
            'scope': token_info['scope'],
        }
    )

    return redirect(f"https://chatbot-calendar-frontend.vercel.app/?email={email}")




@api_view(["GET", "POST"])
def calendar_events(request):
    print("📥 Incoming Event API Call")
    print("🔗 Request method:", request.method)
    print("🧠 Email param:", request.GET.get("email"))
    print("📦 Data received:", request.data)
    email = request.GET.get("email")

    if not email:
        return JsonResponse({"error": "Email parameter is required."}, status=400)

    try:
        user_token = GoogleUserToken.objects.get(email=email)
    except GoogleUserToken.DoesNotExist:
        return JsonResponse({"error": "No credentials found for this user."}, status=403)

    access_token = user_token.access_token

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    calendar_url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

    # Helper function to create event
    def try_post_event(event_data):
        return requests.post(calendar_url, headers=headers, json=event_data)

    # ----------- GET Method: Fetch Events -----------
    if request.method == "GET":
        response = requests.get(calendar_url, headers=headers)

        if response.status_code == 401:
            # Refresh token
            refreshed = refresh_google_token(user_token.refresh_token)
            if refreshed:
                user_token.access_token = refreshed["access_token"]
                user_token.expires_in = refreshed["expires_in"]
                user_token.save()

                headers["Authorization"] = f"Bearer {user_token.access_token}"
                response = requests.get(calendar_url, headers=headers)
            else:
                return Response({"error": "Failed to refresh token"}, status=403)

        if response.status_code != 200:
            return Response({"error": "Failed to fetch events", "details": response.json()}, status=response.status_code)

        return Response(response.json())

    # ----------- POST Method: Create Event -----------
    elif request.method == "POST":
        data = request.data

        event = {
            "summary": data.get("summary", "Untitled Event"),
            "description": data.get("description", ""),
            "start": {
                "dateTime": data.get("start"),
                "timeZone": data.get("timezone", "Asia/Kolkata")
            },
            "end": {
                "dateTime": data.get("end"),
                "timeZone": data.get("timezone", "Asia/Kolkata")
            }
        }

        response = try_post_event(event)

        if response.status_code == 401:
            refreshed = refresh_google_token(user_token.refresh_token)
            if refreshed:
                user_token.access_token = refreshed["access_token"]
                user_token.expires_in = refreshed["expires_in"]
                user_token.save()

                headers["Authorization"] = f"Bearer {user_token.access_token}"
                response = try_post_event(event)
            else:
                return Response({"error": "Failed to refresh token"}, status=403)

        if response.status_code not in [200, 201]:
            return Response({"error": "Failed to create event", "details": response.json()}, status=response.status_code)

        return Response(response.json(), status=status.HTTP_201_CREATED)


def refresh_google_token(refresh_token):
    data = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }

    response = requests.post("https://oauth2.googleapis.com/token", data=data)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def create_google_event(email, summary, start, end):
    try:
        user_token = GoogleUserToken.objects.get(email=email)
    except GoogleUserToken.DoesNotExist:
        return False

    headers = {
        "Authorization": f"Bearer {user_token.access_token}",
        "Content-Type": "application/json"
    }

    event = {
        "summary": summary,
        "description": "Created via chatbot",
        "start": {
            "dateTime": start,
            "timeZone": "Asia/Kolkata"
        },
        "end": {
            "dateTime": end,
            "timeZone": "Asia/Kolkata"
        }
    }

    response = requests.post(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        headers=headers,
        json=event
    )

    if response.status_code == 401:
        refreshed = refresh_google_token(user_token.refresh_token)
        if refreshed:
            user_token.access_token = refreshed["access_token"]
            user_token.expires_in = refreshed["expires_in"]
            user_token.save()

            headers["Authorization"] = f"Bearer {user_token.access_token}"
            response = requests.post(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers=headers,
                json=event
            )

    return response.status_code in [200, 201]



def fetch_google_events(email):
    try:
        user_token = GoogleUserToken.objects.get(email=email)
    except GoogleUserToken.DoesNotExist:
        return None

    headers = {
        "Authorization": f"Bearer {user_token.access_token}",
        "Content-Type": "application/json"
    }

    url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

    response = requests.get(url, headers=headers)

    if response.status_code == 401:
        refreshed = refresh_google_token(user_token.refresh_token)
        if refreshed:
            user_token.access_token = refreshed["access_token"]
            user_token.expires_in = refreshed["expires_in"]
            user_token.save()

            headers["Authorization"] = f"Bearer {user_token.access_token}"
            response = requests.get(url, headers=headers)

    return response.json() if response.status_code == 200 else None








@api_view(["POST"])
def chatbot_interpreter(request):
    from datetime import datetime
    user_input = request.data.get("message", "").strip()
    email = request.GET.get("email")

    if not user_input or not email:
        return Response({"response": "️ Please provide both the message and email."}, status=400)

    parsed = interpret_user_message(user_input)

    if parsed.get("intent") == "create_event":
        if parsed.get("error"):
            return Response({"response": parsed["error"] + " Try: *Add Standup at 9 AM tomorrow*."})

        created = create_google_event(
            email=email,
            summary=parsed["title"],
            start=parsed["start"],
            end=parsed["end"]
        )
        if created:
            dt_obj = dateparser.parse(parsed["start"])
            return Response({"response": f" Scheduled *{parsed['title']}* at {dt_obj.strftime('%I:%M %p, %A')}."})
        else:
            return Response({"response": " Couldn’t create the event."})


    elif parsed.get("intent") == "fetch_events":

        all_events = fetch_google_events(email)

        if not all_events or not all_events.get("items"):
            return Response({"response": " No events found."})

        filtered_events = []

        target_date = parsed.get("date")

        for item in all_events["items"]:

            summary = item.get("summary", "No title")

            raw_time = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")

            dt = dateparser.parse(raw_time)


            if target_date:

                if not dt or dt.date().isoformat() != target_date:
                    continue

            formatted = dt.strftime('%A, %d %b at %I:%M %p') if dt else raw_time

            filtered_events.append(f"• {summary} — {formatted}")

        if filtered_events:

            label = f" Events for {dateparser.parse(target_date).strftime('%A')}" if target_date else " Upcoming events:"

            return Response({"response": f"{label}\n" + "\n".join(filtered_events[:5])})

        else:

            return Response({"response": " No events match your request."})
