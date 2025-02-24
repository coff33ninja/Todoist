import cv2
import pytesseract
from datetime import datetime
import re

class ReceiptProcessor:
    def __init__(self, tesseract_path=None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

    def preprocess_image(self, image_path):
        """Preprocess image for better OCR results"""
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Apply thresholding
        _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        return processed

    def extract_text(self, image_path):
        """Extract text from receipt image"""
        processed_image = self.preprocess_image(image_path)
        text = pytesseract.image_to_string(processed_image)
        return text

    def parse_receipt(self, image_path):
        """Parse receipt text into structured data"""
        text = self.extract_text(image_path)
        
        # Extract date
        date_pattern = r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
        dates = re.findall(date_pattern, text)
        purchase_date = dates[0] if dates else datetime.now().strftime('%Y-%m-%d')
        
        # Extract items and prices
        item_pattern = r'([A-Za-z\s]+)\s+(\d+\.\d{2})'
        items = re.findall(item_pattern, text)
        
        parsed_data = {
            'date': purchase_date,
            'items': [{'name': item[0].strip(), 'price': float(item[1])} 
                     for item in items]
        }
        return parsed_data
