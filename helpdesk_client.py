# helpdesk_client.py (Updated lookup function)
import httpx
import json
from typing import Dict, Any
from config import settings
from db import get_connection, generate_ticket_number, init_db

class HelpdeskAPIClient:
    def __init__(self):
        self.base_url = settings.HELPDESK_BASE_URL.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {settings.HELPDESK_API_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    async def create_ticket(self, payload: Dict[str, Any], idempotency_key: str | None = None) -> Dict[str, Any]:
        """Create a ticket locally when the external helpdesk is not configured."""
        init_db()
        conn = get_connection()
        ticket_number = generate_ticket_number(conn)
        conn.execute(
            """
            INSERT INTO tickets (ticket_number, name, contact, category, description, details_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_number,
                payload.get("full_name"),
                payload.get("mobile") or payload.get("email"),
                payload.get("category_id") or payload.get("scheme_name"),
                payload.get("summary") or "Grievance submitted through the chatbot",
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        conn.commit()
        conn.close()
        return {
            "success": True,
            "ticket_number": ticket_number,
            "message": f"शिकायत सफलतापूर्वक दर्ज हो गई। आपकी टिकट संख्या: {ticket_number}",
        }

    async def validate_location_hierarchy(self, district_id: str | None, block_id: str) -> bool:
        """Accept location values locally when no hierarchy service is configured."""
        return bool(district_id and block_id.strip())

    async def get_ticket_status(self, ticket_number: str) -> Dict[str, Any]:
        init_db()
        conn = get_connection()
        local_ticket = conn.execute(
            "SELECT * FROM tickets WHERE ticket_number = ?", (ticket_number,)
        ).fetchone()
        conn.close()

        if local_ticket is not None:
            data = dict(local_ticket)
            details = json.loads(data.get("details_json") or "{}")
            return {
                "success": True,
                "officialData": {
                    "ticketNumber": data["ticket_number"],
                    "currentStatus": data["status"],
                    "assignedDepartment": data.get("category") or "N/A",
                    "assignedOfficer": "Unassigned",
                    "scheme": "N/A",
                    "category": data.get("category") or "N/A",
                    "subCategory": "N/A",
                    "grievanceDescription": data["description"],
                    "actionTaken": data.get("resolution") or "Under Evaluation",
                    "resolutionRemarks": data.get("resolution") or "None",
                    "name": data.get("name") or details.get("full_name") or "N/A",
                    "contact": data.get("contact") or details.get("mobile") or "N/A",
                    "email": details.get("email") or "N/A",
                    "district": details.get("district_id") or "N/A",
                    "block": details.get("block_id") or "N/A",
                    "panchayat": details.get("panchayat_id") or "N/A",
                    "village": details.get("village") or "N/A",
                    "ward": details.get("ward") or "N/A",
                    "address": details.get("full_address") or "N/A",
                },
            }

        url = f"{self.base_url}/tickets/{ticket_number}"
        
        async with httpx.AsyncClient(timeout=10.0, verify=True) as client:
            try:
                response = await client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    res_json = response.json()
                    
                    # Target inner data object if present
                    data = res_json.get("data") if isinstance(res_json.get("data"), dict) else res_json
                    
                    # Multi-alias extraction for ticket number
                    resolved_ticket_id = (
                        data.get("ticket_number") or 
                        data.get("ticket_no") or 
                        data.get("reference_no") or 
                        data.get("name") or 
                        data.get("id") or 
                        ticket_number
                    )

                    return {
                        "success": True,
                        "officialData": {
                            "ticketNumber": str(resolved_ticket_id),
                            "currentStatus": data.get("status") or data.get("stage_id") or "Registered",
                            "assignedDepartment": data.get("department_name") or data.get("team_id") or "N/A",
                            "assignedOfficer": data.get("officer_name") or data.get("user_id") or "Unassigned",
                            "scheme": data.get("scheme_name") or data.get("scheme") or "N/A",
                            "category": data.get("category_name") or data.get("category") or "N/A",
                            "subCategory": data.get("sub_category_name") or data.get("sub_category") or "N/A",
                            "grievanceDescription": data.get("description") or "N/A",
                            "actionTaken": data.get("action_taken") or "Under Evaluation",
                            "resolutionRemarks": data.get("remarks") or "None"
                        }
                    }
                elif response.status_code == 404:
                    return {"success": False, "message": f"शिकायत संख्या '{ticket_number}' हेल्पडेस्क सिस्टम में नहीं मिली।"}
                else:
                    return {"success": False, "message": f"सर्वर त्रुटि (Status: {response.status_code})"}
            except httpx.RequestError as e:
                return {"success": False, "message": f"Network Error: {str(e)}"}