from models import ComplaintState, MobileValidationModel
from helpdesk_client import HelpdeskAPIClient

STEPS = [
    "SUMMARY", "NAME", "MOBILE", "EMAIL", "SCHEME_CONFIRM",
    "TICKET_TYPE", "CLASSIFICATION_CONFIRM", "DISTRICT",
    "BLOCK", "PANCHAYAT", "VILLAGE", "WARD", "ADDRESS",
    "DOCUMENT", "OTP_VERIFY", "SUBMIT"
]

class ComplaintWizard:
    def __init__(self, state: ComplaintState, api_client: HelpdeskAPIClient):
        self.state = state
        self.api = api_client

    async def advance(self, user_input: str) -> dict:
        step = self.state.current_step

        if step == "SUMMARY":
            self.state.summary = user_input
            self.state.current_step = "NAME"
            return {"reply": "कृपया अपना पूरा नाम दर्ज करें (Please enter your full name):"}

        elif step == "NAME":
            self.state.full_name = user_input
            self.state.current_step = "MOBILE"
            return {"reply": "कृपया अपना 10-अंकों का मोबाइल नंबर दर्ज करें (Enter 10-digit mobile number):"}

        elif step == "MOBILE":
            try:
                valid_mobile = MobileValidationModel(mobile=user_input).mobile
                self.state.mobile = valid_mobile
                self.state.current_step = "EMAIL"
                return {"reply": "ईमेल पता दर्ज करें, या आगे बढ़ने के लिए 'SKIP' लिखें (Enter email or type SKIP):"}
            except Exception as e:
                return {"reply": str(e)}

        elif step == "EMAIL":
            if user_input.strip().lower() != "skip":
                self.state.email = user_input
            self.state.current_step = "SCHEME_CONFIRM"
            return {"reply": "क्या आपकी शिकायत MGNREGA योजना से संबंधित है? (हां / नहीं)"}

        elif step == "SCHEME_CONFIRM":
            if "ह" in user_input.lower() or "yes" in user_input.lower():
                self.state.scheme_id = "SCH_MGNREGA"
                self.state.current_step = "CLASSIFICATION_CONFIRM"
                return {"reply": "अनुमानित श्रेणी: 'मजबूरी भुगतान' (Wage Payment)। पुष्टि करें (हां/नहीं)?"}
            self.state.current_step = "DISTRICT"
            return {"reply": "कृपया अपना जिला (District) चुनें:"}

        elif step == "CLASSIFICATION_CONFIRM":
            self.state.current_step = "DISTRICT"
            return {"reply": "कृपया अपना जिला (District) चुनें:"}

        elif step == "DISTRICT":
            self.state.district_id = user_input
            self.state.current_step = "BLOCK"
            return {"reply": "कृपया अपना ब्लॉक (Block) दर्ज करें:"}

        elif step == "BLOCK":
            # Hierarchy Check: Block belongs to selected District
            is_valid = await self.api.validate_location_hierarchy(self.state.district_id, user_input)
            if not is_valid:
                return {"reply": "अमान्य ब्लॉक! कृपया सही ब्लॉक नाम दर्ज करें जो चुने गए जिले के अंतर्गत आता है।"}
            self.state.block_id = user_input
            self.state.current_step = "PANCHAYAT"
            return {"reply": "कृपया अपनी पंचायत का नाम दर्ज करें:"}

        elif step == "PANCHAYAT":
            self.state.panchayat_id = user_input
            self.state.current_step = "VILLAGE"
            return {"reply": "कृपया अपना गांव (Village) दर्ज करें:"}

        elif step == "VILLAGE":
            self.state.village = user_input
            self.state.current_step = "WARD"
            return {"reply": "कृपया अपना वार्ड नंबर दर्ज करें:"}

        elif step == "WARD":
            self.state.ward = user_input
            self.state.current_step = "ADDRESS"
            return {"reply": "कृपया अपना पूरा पता दर्ज करें:"}

        elif step == "ADDRESS":
            self.state.full_address = user_input
            result = await self.api.create_ticket(self.state.model_dump())
            self.state.current_step = "SUBMIT"
            return {"reply": result["message"], "ticket_number": result["ticket_number"]}

        # Additional steps follow the same pattern...
        return {"reply": "प्रक्रिया जारी है..."}