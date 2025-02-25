import cv2
import pytesseract
from PIL import Image
import numpy as np
import re
from datetime import datetime


class ReceiptProcessor:
    def __init__(self):
        # Configure Tesseract path if needed
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass

    def preprocess_image(self, image_path):
        """Preprocess the receipt image for better OCR results"""
        try:
            # Load image
            img = cv2.imread(image_path)

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Apply adaptive thresholding
            processed = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # Deskew if needed
            angle = self.get_skew_angle(processed)
            if abs(angle) > 0.5:
                processed = self.rotate_image(processed, angle)

            return processed
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return None

    def get_skew_angle(self, image):
        """Calculate skew angle of the image"""
        coords = np.column_stack(np.where(image > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        return -angle

    def rotate_image(self, image, angle):
        """Rotate the image by given angle"""
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )
        return rotated

    def extract_text(self, image_path):
        """Extract text from receipt image"""
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image_path)

            if processed_image is None:
                print("Processed image is None")  # Debug statement
                return None

            # Perform OCR with custom configuration
            custom_config = r"--oem 3 --psm 6"
            text = pytesseract.image_to_string(processed_image, config=custom_config)
            return text
        except Exception as e:
            print(f"Error extracting text: {e}")
            return None

    def parse_receipt(self, text):
        """Parse extracted text to extract relevant information"""
        try:
            result = {
                "items": [],
                "total": None,
                "date": None,
                "store_name": None,
                "warranty_info": None,
                "payment_method": None,
            }

            # Extract date
            date_patterns = [
                r"\d{2}[-/]\d{2}[-/]\d{2,4}",  # DD-MM-YYYY or DD/MM/YYYY
                r"\d{4}[-/]\d{2}[-/]\d{2}",  # YYYY-MM-DD
                r"\w{3}\s+\d{1,2},?\s+\d{4}",  # MMM DD, YYYY
            ]

            for pattern in date_patterns:
                date_match = re.search(pattern, text)
                if date_match:
                    try:
                        date_str = date_match.group(0)
                        # Try different date formats
                        for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%b %d, %Y"]:
                            try:
                                result["date"] = datetime.strptime(
                                    date_str, fmt
                                ).strftime("%Y-%m-%d")
                                break
                            except ValueError:
                                continue
                        if result["date"]:
                            break
                    except Exception:
                        continue

            print(f"Extracted Text for Parsing: {text}")  # Debug statement
            print("Checking lines for store name...")  # Debug statement
            # Extract store name (usually at the top of receipt)
            lines = text.split("\n")
            for line in lines[:3]:  # Check first 3 lines
                if line.strip() and not any(char.isdigit() for char in line):
                    result["store_name"] = line.strip()
                    break

            # Extract total amount
            total_patterns = [
                r"(?:total|balance|amount|sum)\s*:?\s*\$?\s*(\d+\.\d{2})",
                r"(?:total|balance|amount|sum)\s*\$?\s*(\d+\.\d{2})",
                r"\$\s*(\d+\.\d{2})\s*$",
            ]

            for pattern in total_patterns:
                total_match = re.search(pattern, text, re.IGNORECASE)
                if total_match:
                    result["total"] = float(total_match.group(1))
                    break

            # Extract payment method
            payment_patterns = [
                r"paid\s+(?:by|via|using)\s+(\w+)",
                r"payment\s+method\s*:?\s*(\w+)",
                r"(?:visa|mastercard|amex|cash|credit|debit)",
            ]

            for pattern in payment_patterns:
                payment_match = re.search(pattern, text, re.IGNORECASE)
                if payment_match:
                    result["payment_method"] = (
                        payment_match.group(1)
                        if payment_match.groups()
                        else payment_match.group(0)
                    )
                    break

            # Extract warranty information
            warranty_patterns = [
                r"warranty\s*:?\s*(\d+\s*(?:year|month|day)s?)",
                r"guarantee\s*:?\s*(\d+\s*(?:year|month|day)s?)",
            ]

            for pattern in warranty_patterns:
                warranty_match = re.search(pattern, text, re.IGNORECASE)
                if warranty_match:
                    result["warranty_info"] = warranty_match.group(1)
                    break

            # Extract items (looking for patterns like "1 x Item $10.99" or "Item........$10.99")
            item_patterns = [
                r"(\d+)\s*x\s*([\w\s-]+?)\s*\$?\s*(\d+\.\d{2})",  # Quantity x Item $Price
                r"([\w\s-]+?)\s*\.+\s*\$?\s*(\d+\.\d{2})",  # Item.....$Price
                r"(\d+)\s*([\w\s-]+?)\s*@\s*\$?\s*(\d+\.\d{2})",  # Quantity Item @ $Price
            ]

            for line in text.split("\n"):
                for pattern in item_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        if len(match.groups()) == 3:  # Pattern with quantity
                            quantity = int(match.group(1))
                            description = match.group(2).strip()
                            price = float(match.group(3))
                        else:  # Pattern without quantity
                            quantity = 1
                            description = match.group(1).strip()
                            price = float(match.group(2))

                        # Try to determine if item was traded or gifted
                        acquisition_type = "purchase"
                        if any(
                            word in description.lower()
                            for word in ["trade", "traded", "exchange"]
                        ):
                            acquisition_type = "trade"
                        elif any(
                            word in description.lower()
                            for word in ["gift", "free", "complimentary"]
                        ):
                            acquisition_type = "gift"

                        result["items"].append(
                            {
                                "quantity": quantity,
                                "description": description,
                                "price": price,
                                "acquisition_type": acquisition_type,
                            }
                        )

            return result
        except Exception as e:
            print(f"Error parsing receipt: {e}")
            return None
