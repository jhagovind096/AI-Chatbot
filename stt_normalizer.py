# stt_normalizer.py
import re
from typing import Optional

HINDI_NUMBER_MAP = {
    "शून्य": "0", "zero": "0",
    "एक": "1", "one": "1", "ek": "1",
    "दो": "2", "two": "2", "do": "2",
    "तीन": "3", "three": "3", "teen": "3",
    "चार": "4", "four": "4", "chaar": "4",
    "पांच": "5", "five": "5", "paanch": "5",
    "छह": "6", "six": "6", "chhe": "6",
    "सात": "7", "seven": "7", "saat": "7",
    "आठ": "8", "eight": "8", "aath": "8",
    "नौ": "9", "nine": "9", "nau": "9",
}

def normalize_spoken_ticket(input_text: str) -> Optional[str]:
    if not input_text:
        return None
        
    text = input_text.lower()
    
    # 1. Convert spoken Hindi/Hinglish words to digits
    for word, digit in HINDI_NUMBER_MAP.items():
        text = re.sub(rf"\b{word}\b", digit, text)
        
    # 2. Extract ticket pattern, preserving the TKT_ prefix for local tickets.
    match = re.search(r"(tkt[-_\s]?\d{5})|([a-z]{2,5}[-_\s]?\d{3,6}[-_\s]?\d{3,8})|(\d{5,12})", text, re.IGNORECASE)
    
    if match:
        extracted = match.group(0).upper().replace(" ", "")
        return extracted
        
    # Fallback: strip non-alphanumeric characters if user typed directly
    cleaned = re.sub(r"[^\w-]", "", input_text)
    return cleaned.upper() if len(cleaned) >= 4 else None