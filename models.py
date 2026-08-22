import re
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator

class TicketStatusRequest(BaseModel):
    raw_input: str

class MobileValidationModel(BaseModel):
    mobile: str

    @field_validator("mobile")
    def validate_indian_mobile(cls, v: str) -> str:
        cleaned = re.sub(r"\D", "", v)
        if not re.match(r"^[6-9]\d{9}$", cleaned):
            raise ValueError("कृपया एक वैध 10-अंकों का मोबाइल नंबर प्रदान करें (Must be a valid 10-digit mobile number starting with 6-9).")
        return cleaned

class ComplaintState(BaseModel):
    session_id: str
    current_step: str = "SUMMARY"
    summary: Optional[str] = None
    full_name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    scheme_id: Optional[str] = None
    scheme_name: Optional[str] = None
    ticket_type_id: Optional[str] = None
    category_id: Optional[str] = None
    sub_category_id: Optional[str] = None
    district_id: Optional[str] = None
    block_id: Optional[str] = None
    panchayat_id: Optional[str] = None
    village: Optional[str] = None
    ward: Optional[str] = None
    full_address: Optional[str] = None
    attachment_url: Optional[str] = None
    otp_verified: bool = False