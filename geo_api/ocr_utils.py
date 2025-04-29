import cv2
import pytesseract
import numpy as np
import os
import re

# Update if needed
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

def preprocess_image_for_ocr(image_path):
    image = cv2.imread(image_path)

    # Upscale first: 3x bigger
    scale_percent = 300
    width = int(image.shape[1] * scale_percent / 100)
    height = int(image.shape[0] * scale_percent / 100)
    resized = cv2.resize(image, (width, height), interpolation=cv2.INTER_CUBIC)

    # Convert to grayscale
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 9
    )

    # Remove small noise
    kernel = np.ones((1, 1), np.uint8)
    denoised = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return denoised

def extract_text_from_image(image_path: str) -> str:
    try:
        processed_image = preprocess_image_for_ocr(image_path)
        raw_text = pytesseract.image_to_string(processed_image, config="--psm 6")
        utf8_text = raw_text.encode('utf-8', errors='ignore').decode('utf-8')
        return utf8_text.strip()
    except Exception as e:
        print("[ERROR] OCR failed:", e)
        return ""

def extract_address_from_text(text: str) -> str:
    match = re.search(r'\d{3,5}\s+[A-Za-z]+\s+(University|Main|Park|Cherry|6th|1st|2nd|Street|Avenue|Blvd|St)[^\n,]*', text)
    if match:
        return match.group(0).strip()
    else:
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if re.search(r'\d{3,5}', line) and any(keyword in line for keyword in ["University", "Street", "Blvd", "Avenue", "Park", "St"]):
                return line.strip()
    return None

def extract_building_info(text: str):
    lines = text.splitlines()
    name_candidate = ""
    number_candidate = ""

    for i, line in enumerate(lines):
        lower = line.lower()

        if "building number" in lower or "bldg" in lower:
            match = re.search(r"\d{1,4}", line)
            if match:
                number_candidate = match.group()

        if re.search(r"\d{3,5}\s+.*(University|Blvd|Street|Avenue|Road|St)", line, re.IGNORECASE):
            if i > 0 and len(lines[i - 1].strip()) > 3:
                name_candidate = lines[i - 1].strip()

    return name_candidate.strip(), number_candidate.strip()
