from django.urls import path
from . import views
from .views import google_login, google_callback, calendar_events,chatbot_interpreter

urlpatterns = [
    path('google/login/', google_login),
    path('google/callback/', google_callback),
    path('events/', calendar_events, name='calendar_events'),
    path('chatbot/', chatbot_interpreter),
]
