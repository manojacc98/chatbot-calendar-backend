#  Calendar Assistant Backend (Django)

This is the backend of the **Chatbot Calendar Assistant** project, built with **Django** and integrated with **Google Calendar API** using OAuth2. It exposes REST API endpoints to authenticate users, fetch calendar events, create new events, and handle natural language chatbot requests.

---

##  Tech Stack

- **Framework**: Django 
- **API**: Django REST Framework
- **Auth**: Google OAuth2
- **Database**: SQLite (dev), PostgreSQL (recommended for prod)
- **Hosting**: Render
- **Frontend**: [Vercel Deployment](https://chatbot-calendar-frontend.vercel.app)

---

##  Features

- Google OAuth2 login
- Read and write to Google Calendar
- Secure access token storage
- Chatbot-compatible REST endpoints
- CORS enabled for frontend integration

---

##  Project Structure

calendar_project/
├── calendar_project/ # Django settings and project config
├── api/ # Views, URLs, Models, Serializers
│ ├── views.py
│ ├── models.py
│ ├── urls.py
│ ├── serializers.py
├── manage.py

yaml
Copy
Edit

---

##  Local Setup Instructions

### 1. Clone the Repository

git clone https://github.com/manojacc98/chatbot-calendar-backend.git
cd chatbot-calendar-backend
2. Create a Virtual Environment
bash
Copy
Edit
python3 -m venv venv
source venv/bin/activate
3. Install Dependencies
bash
Copy
Edit
pip install -r requirements.txt
4. Set Up Environment Variables
Create a .env file:

env
Copy
Edit
SECRET_KEY=your-django-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
FRONTEND_URL=https://chatbot-calendar-frontend.vercel.app
5. Run Migrations
bash
Copy
Edit
python manage.py migrate
6. Start Local Server
bash
Copy
Edit
python manage.py runserver
 Deployment (Render)
This project is deployed on Render. The backend URL is:

Live Backend: https://chatbot-calendar-backend.onrender.com

 Deployment Steps (Render)
Go to Render Dashboard

Create a new web service

Connect to your GitHub repo

Set the root directory to the Django project folder

Add Build Command:

pip install -r requirements.txt && python manage.py migrate
Start Command:
gunicorn calendar_project.wsgi
Add environment variables in Render:

SECRET_KEY

GOOGLE_CLIENT_ID

GOOGLE_CLIENT_SECRET

FRONTEND_URL
 API Endpoints
Method	Endpoint	Description
GET	/api/google/login/	Start Google OAuth2 flow
GET	/api/google/callback/	Handle Google redirect
GET	/api/calendar/events?email=	Fetch user’s events
POST	/api/calendar/events?email=	Create a new calendar event

Frontend Project
https://chatbot-calendar-backend.onrender.com


 Author
Built by Manoj R




