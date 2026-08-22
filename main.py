
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from models import TicketStatusRequest, ComplaintState
from stt_normalizer import normalize_spoken_ticket
from helpdesk_client import HelpdeskAPIClient
from state_machine import ComplaintWizard
import uuid

app = FastAPI(title="RDD CGRS Conversational AI Backend", version="1.0.0")
allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000"
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Idempotency-Key"],
)
api_client = HelpdeskAPIClient()

# In-memory session store (Replace with Redis in production)
SESSIONS: dict[str, ComplaintState] = {}

@app.post("/api/v1/ticket-status")
async def get_ticket_status(req: TicketStatusRequest):
    """Voice/Text multi-lingual ticket lookup."""
    ticket_no = normalize_spoken_ticket(req.raw_input)
    
    if not ticket_no:
        return {
            "success": False,
            "message": "वैध शिकायत / टिकट नंबर नहीं मिला (Valid ticket number not recognized)."
        }
    
    result = await api_client.get_ticket_status(ticket_no)
    return result

@app.post("/api/v1/complaint/message")
async def handle_complaint_flow(
    session_id: str,
    user_input: str
):
    """Sequential wizard engine for step-by-step grievance submission."""
    if session_id not in SESSIONS:
        SESSIONS[session_id] = ComplaintState(session_id=session_id)
        
    state = SESSIONS[session_id]
    wizard = ComplaintWizard(state, api_client)
    
    response = await wizard.advance(user_input)
    return {"session_id": session_id, "current_step": state.current_step, **response}

@app.post("/api/v1/complaint/upload-document")
async def upload_document(
    session_id: str,
    file: UploadFile = File(...)
):
    """File attachment validation with size and format checks."""
    allowed_types = ["application/pdf", "image/jpeg", "image/png"]
    max_bytes = 5 * 1024 * 1024  # 5MB Limit

    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="केवल PDF, JPG या PNG फाइलों की अनुमति है।")

    contents = await file.read()
    if len(contents) > max_bytes:
        raise HTTPException(status_code=400, detail="फ़ाइल का आकार 5MB से अधिक नहीं होना चाहिए।")

    # Save to storage or forward to Helpdesk API file service
    return {"success": True, "filename": file.filename, "size": len(contents)}

@app.post("/api/v1/complaint/verify-otp-submit")
async def verify_and_submit(
    session_id: str,
    otp: str,
    idempotency_key: str = Header(default_factory=lambda: str(uuid.uuid4()))
):
    """Verifies OTP and creates ticket using Idempotency-Key."""
    state = SESSIONS.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="सत्र समाप्त हो गया (Session expired).")

    is_verified = await api_client.verify_otp(state.mobile, otp)
    if not is_verified:
        return {"success": False, "message": "गलत OTP! कृपया पुनः प्रयास करें।"}

    state.otp_verified = True
    payload = state.model_dump()
    
    ticket_result = await api_client.create_ticket(payload, idempotency_key=idempotency_key)
    return ticket_result
    #return ticket_resultfrom fastapi import FastAPI, HTTPException, UploadFile, File, Header
from models import TicketStatusRequest, ComplaintState
from stt_normalizer import normalize_spoken_ticket
from helpdesk_client import HelpdeskAPIClient
from state_machine import ComplaintWizard
import uuid

app = FastAPI(title="RDD CGRS Conversational AI Backend", version="1.0.0")
api_client = HelpdeskAPIClient()
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Idempotency-Key"],
)

# In-memory session store (Replace with Redis in production)
SESSIONS: dict[str, ComplaintState] = {}

@app.post("/api/v1/ticket-status")
async def get_ticket_status(req: TicketStatusRequest):
    """Voice/Text multi-lingual ticket lookup."""
    ticket_no = normalize_spoken_ticket(req.raw_input)
    
    if not ticket_no:
        return {
            "success": False,
            "message": "वैध शिकायत / टिकट नंबर नहीं मिला (Valid ticket number not recognized)."
        }
    
    result = await api_client.get_ticket_status(ticket_no)
    return result

@app.post("/api/v1/complaint/message")
async def handle_complaint_flow(
    session_id: str,
    user_input: str
):
    """Sequential wizard engine for step-by-step grievance submission."""
    if session_id not in SESSIONS:
        SESSIONS[session_id] = ComplaintState(session_id=session_id)
        
    state = SESSIONS[session_id]
    wizard = ComplaintWizard(state, api_client)
    
    response = await wizard.advance(user_input)
    return {"session_id": session_id, "current_step": state.current_step, **response}

@app.post("/api/v1/complaint/upload-document")
async def upload_document(
    session_id: str,
    file: UploadFile = File(...)
):
    """File attachment validation with size and format checks."""
    allowed_types = ["application/pdf", "image/jpeg", "image/png"]
    max_bytes = 5 * 1024 * 1024  # 5MB Limit

    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="केवल PDF, JPG या PNG फाइलों की अनुमति है।")

    contents = await file.read()
    if len(contents) > max_bytes:
        raise HTTPException(status_code=400, detail="फ़ाइल का आकार 5MB से अधिक नहीं होना चाहिए।")

    # Save to storage or forward to Helpdesk API file service
    return {"success": True, "filename": file.filename, "size": len(contents)}

@app.post("/api/v1/complaint/verify-otp-submit")
async def verify_and_submit(
    session_id: str,
    otp: str,
    idempotency_key: str = Header(default_factory=lambda: str(uuid.uuid4()))
):
    """Verifies OTP and creates ticket using Idempotency-Key."""
    state = SESSIONS.get(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="सत्र समाप्त हो गया (Session expired).")

    is_verified = await api_client.verify_otp(state.mobile, otp)
    if not is_verified:
        return {"success": False, "message": "गलत OTP! कृपया पुनः प्रयास करें।"}

    state.otp_verified = True
    payload = state.model_dump()
    
    ticket_result = await api_client.create_ticket(payload, idempotency_key=idempotency_key)
    return ticket_result

@app.get("/")
async def serve_widget():
    """Serves the Chat Widget frontend HTML page."""
    return FileResponse("index.html")
    

# snippet in main.py
@app.post("/api/v1/ticket-status")
async def get_ticket_status(req: TicketStatusRequest):
    """
    Fetches official Helpdesk status and wraps it in a citizen-friendly message.
    """
    ticket_no = normalize_spoken_ticket(req.raw_input)
    
    if not ticket_no:
        return {
            "success": False,
            "message": "कृपया एक वैध टिकट संख्या प्रदान करें (उदा: TKT_00001)।"
        }
    
    # Query live REST JSON API
    result = await api_client.get_ticket_status(ticket_no)
    
    if result.get("success"):
        official = result["officialData"]
        # Explicit distinction between Official Helpdesk Data and Conversational UI
        response_text = (
            f"📋 **आधिकारिक शिकायत स्थिति (Official Ticket Details)**\n\n"
            f"• **टिकट संख्या:** {official['ticketNumber']}\n"
            f"• **वर्तमान स्थिति:** {official['currentStatus']}\n"
            f"• **संबंधित विभाग:** {official['assignedDepartment']}\n"
            f"• **प्रभारी अधिकारी:** {official['assignedOfficer']}\n"
            f"• **योजना:** {official['scheme']}\n"
            f"• **श्रेणी:** {official['category']} ({official['subCategory']})\n"
            f"• **कार्रवाई / विवरण:** {official['actionTaken']}\n"
            f"• **टिप्पणी:** {official['resolutionRemarks']}"
        )
        return {
            "success": True,
            "officialData": official,
            "message": response_text
        }
    else:
        return {
            "success": False,
            "message": result.get("message", "सर्वर से स्थिति प्राप्त करने में असमर्थ।")
        }
        
@app.get("/api/v1/debug-raw-ticket/{ticket_id}")
async def debug_raw_ticket(ticket_id: str):
    """Directly returns the raw unparsed JSON payload from rddcgrs.in"""
    import httpx
    from config import settings
    
    url = f"{settings.HELPDESK_BASE_URL.rstrip('/')}/tickets/{ticket_id}"
    headers = {"Authorization": f"Bearer {settings.HELPDESK_API_KEY}"}
    
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        return {
            "http_status": res.status_code,
            "raw_payload": res.json() if res.status_code == 200 else res.text
        }