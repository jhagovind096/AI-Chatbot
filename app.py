import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from db import init_db, get_connection, generate_ticket_number

load_dotenv()

app = Flask(__name__)

# Only allow requests from your website's domain in production
allowed_origin = os.getenv("ALLOWED_ORIGIN", "*")
CORS(app, resources={r"/api/*": {"origins": allowed_origin}})

init_db()


@app.route("/api/tickets", methods=["POST"])
def create_ticket():
    """
    CREATE a new grievance ticket.
    Called by your chatbot when a user reports an issue.
    Body: { "name": ..., "contact": ..., "category": ..., "description": ... }
    """
    data = request.get_json(silent=True) or {}
    description = (data.get("description") or "").strip()

    if not description:
        return jsonify({"error": "description is required"}), 400

    conn = get_connection()
    ticket_number = generate_ticket_number(conn)

    conn.execute(
        """
        INSERT INTO tickets (ticket_number, name, contact, category, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            ticket_number,
            data.get("name"),
            data.get("contact"),
            data.get("category"),
            description,
        ),
    )
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Ticket created successfully",
        "ticket_number": ticket_number
    }), 201


@app.route("/api/tickets/<ticket_number>", methods=["GET"])
def get_ticket(ticket_number):
    """
    FETCH a ticket's status/info by ticket number.
    Called by your chatbot when a user asks "what's the status of GRV-00001?"
    """
    conn = get_connection()
    ticket = conn.execute(
        "SELECT * FROM tickets WHERE ticket_number = ?", (ticket_number,)
    ).fetchone()
    conn.close()

    if ticket is None:
        return jsonify({"error": "Ticket not found"}), 404

    return jsonify(dict(ticket))


@app.route("/api/tickets/<ticket_number>", methods=["PATCH"])
def update_ticket(ticket_number):
    """
    UPDATE a ticket's status/resolution (for your admin/staff side, not the chatbot).
    Body: { "status": ..., "resolution": ... }
    """
    data = request.get_json(silent=True) or {}

    conn = get_connection()
    existing = conn.execute(
        "SELECT * FROM tickets WHERE ticket_number = ?", (ticket_number,)
    ).fetchone()

    if existing is None:
        conn.close()
        return jsonify({"error": "Ticket not found"}), 404

    status = data.get("status", existing["status"])
    resolution = data.get("resolution", existing["resolution"])

    conn.execute(
        """
        UPDATE tickets
        SET status = ?, resolution = ?, updated_at = datetime('now')
        WHERE ticket_number = ?
        """,
        (status, resolution, ticket_number),
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Ticket updated successfully"})


@app.route("/api/tickets", methods=["GET"])
def list_tickets():
    """LIST all tickets (useful for an admin dashboard)."""
    conn = get_connection()
    tickets = conn.execute(
        "SELECT * FROM tickets ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    return jsonify([dict(t) for t in tickets])


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=True)
