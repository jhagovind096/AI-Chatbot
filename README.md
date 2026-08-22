# Grievance Redressal Backend (Python / Flask)

A minimal Flask + SQLite backend that stores grievance tickets and lets your
chatbot create tickets and look them up by ticket number.

## 1. Run it locally

```bash
python -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Server starts on `http://localhost:3000`. A file called `grievances.db`
will appear in this folder automatically — that's your SQLite database.

## 2. API endpoints

### Create a ticket
```
POST /api/tickets
Content-Type: application/json

{
  "name": "Ravi Kumar",
  "contact": "ravi@example.com",
  "category": "Water Supply",
  "description": "No water supply in Sector 5 for 3 days"
}
```
Response:
```json
{ "message": "Ticket created successfully", "ticket_number": "TKT_00001" }
```

### Fetch a ticket by number
```
GET /api/tickets/TKT_00001
```
Response:
```json
{
  "id": 1,
  "ticket_number": "TKT_00001",
  "name": "Ravi Kumar",
  "contact": "ravi@example.com",
  "category": "Water Supply",
  "description": "No water supply in Sector 5 for 3 days",
  "status": "Open",
  "resolution": null,
  "created_at": "2026-08-22 10:15:00",
  "updated_at": "2026-08-22 10:15:00"
}
```

### Update ticket status (for staff/admin, not the chatbot)
```
PATCH /api/tickets/TKT_00001
Content-Type: application/json

{ "status": "Resolved", "resolution": "Water supply restored on 24 Aug" }
```

### List all tickets (for an admin dashboard)
```
GET /api/tickets
```

## 3. Wiring this into your chatbot

Wherever your chatbot's Python code decides "user wants to file a complaint,"
call the create endpoint (or, if your chatbot is also in Python and lives
in the same process, you can import and call the `db.py` functions directly
instead of going through HTTP):

```python
import requests

response = requests.post(
    "https://your-backend-domain.com/api/tickets",
    json={
        "name": name,
        "contact": contact,
        "category": category,
        "description": description,
    },
)
data = response.json()
ticket_number = data["ticket_number"]  # tell this to the user
```

And wherever it detects "user is asking about ticket TKT_XXXXX":

```python
response = requests.get(f"https://your-backend-domain.com/api/tickets/{ticket_number}")
if response.status_code == 404:
    # tell user ticket not found
else:
    ticket = response.json()
    # tell user ticket["status"], ticket["resolution"], etc.
```

## 4. Deploying so your live website can reach it

You need this running somewhere with a public URL, not just on your machine.
Easiest options:
- **Render** (render.com) — connect your GitHub repo, set the start command
  to `gunicorn app:app`, it builds and hosts automatically
- **Railway** (railway.app) — similar, very quick to deploy
- **PythonAnywhere** — simple for small Flask apps
- **A VPS** (DigitalOcean, AWS EC2) — more control, more setup

For production, don't use Flask's built-in dev server (`app.run(debug=True)`).
Use a proper WSGI server:
```bash
pip install gunicorn
gunicorn app:app --bind 0.0.0.0:3000
```

Once deployed:
1. Set `ALLOWED_ORIGIN` in your environment variables to your actual website
   domain (e.g. `https://mywebsite.com`) instead of `*`.
2. Update your chatbot's request URLs to point at the deployed backend URL.
3. Make sure your site is served over HTTPS — browsers block a mix of
   HTTP and HTTPS requests.

## 5. Notes on the database

This uses SQLite (a single file, `grievances.db`), which is fine for
low-to-medium traffic. If you expect heavy concurrent traffic or want to run
multiple backend instances, switch to PostgreSQL (e.g. via Supabase or Neon,
both have free tiers) — you'd swap the `sqlite3` calls in `db.py` for
`psycopg2`, and the rest of the logic stays almost the same.
