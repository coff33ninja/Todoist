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

    def extract_text(self, text):
        """Extract text from receipt input"""
        try:
            # Directly use the text input for parsing
            text = text.strip()

            if not text:
                print("Input text is empty")  # Debug statement
                return None

            return text
        except Exception as e:
            print(f"Error extracting text: {e}")
            return None

    def parse_receipt(self, text):
        """Parse extracted text to extract relevant information"""
        try:
            print("Starting receipt parsing...")
            print(f"Input text:\n{text}")

            result = {
                "items": [],
                "total": None,
                "date": None,
                "store_name": None,
                "warranty_info": None,
                "payment_method": None,
                "currency": None,
                "tax_details": [],
            }

            # Split text into lines and remove empty lines
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            print(f"Processed lines: {len(lines)}")

            # Extract store name (first non-empty line)
            if lines:
                result["store_name"] = lines[0].strip()
                print(f"Found store name: {result['store_name']}")

            # Detect currency symbol/code
            currency_patterns = [
                r"(?:[\$\£\€\¥\₹\R])\s*\d+[.,]\d{2}",  # Common currency symbols
                r"\d+[.,]\d{2}\s*(?:USD|EUR|GBP|JPY|INR|ZAR|AUD|CAD|NZD|BRL)",  # Currency codes
                r"\d+[.,]\d{2}\s*€",  # Specific Euro pattern
            ]

            for line in lines:
                for pattern in currency_patterns:
                    currency_match = re.search(pattern, line)
                    if currency_match:
                        print(f"Currency line found: {line}")
                        currency_symbol = re.search(
                            r"[\$\£\€\¥\₹\R]|(?:USD|EUR|GBP|JPY|INR|ZAR|AUD|CAD|NZD|BRL)|€",
                            currency_match.group(),
                        )
                        if currency_symbol:
                            result["currency"] = currency_symbol.group()
                            print(f"Found currency: {result['currency']}")
                            break
                if result["currency"]:
                    break

            # Extract date with international formats
            date_patterns = [
                r"(?:Date|Datum|Fecha|Data|日付|तारीख):\s*(\d{2}/\d{2}/\d{4})",  # DD/MM/YYYY
                r"(?:Date|Datum|Fecha|Data|日付|तारीख):\s*(\d{4}-\d{2}-\d{2})",  # YYYY-MM-DD
                r"(?:Date|Datum|Fecha|Data|日付|तारीख):\s*(\d{2}-\d{2}-\d{2,4})",  # DD-MM-YYYY
                r"(?:Date|Datum|Fecha|Data|日付|तारीख):\s*(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})",  # DD Mon YYYY
            ]

            for line in lines:
                for pattern in date_patterns:
                    date_match = re.search(pattern, line, re.IGNORECASE)
                    if date_match:
                        result["date"] = date_match.group(1)
                        print(f"Found date: {result['date']}")
                        break
                if result["date"]:
                    break

            # Extract total amount with international number formats
            total_patterns = [
                r"Total:\s*(\d+[.,]\d{2})\s*€",  # Specific Euro format
                r"Total:\s*€\s*(\d+[.,]\d{2})",  # Alternative Euro format
                r"(?:Total|Totaal|Total|Gesamt|合計|कुल):\s*(?:[\$\£\€\¥\₹\R])?\s*([\d.,]+)",
                r"(?:Sum|Summe|Suma|総額|राशि):\s*(?:[\$\£\€\¥\₹\R])?\s*([\d.,]+)",
                r"(?:Amount|Bedrag|Monto|Betrag|金額|रकम):\s*(?:[\$\£\€\¥\₹\R])?\s*([\d.,]+)",
            ]

            for line in lines:
                print(f"Checking total in line: {line}")
                for pattern in total_patterns:
                    total_match = re.search(pattern, line, re.IGNORECASE)
                    if total_match:
                        print(f"Total match found: {total_match.group()}")
                        # Handle different decimal separators
                        amount_str = total_match.group(1)
                        print(f"Amount string before processing: {amount_str}")
                        # Convert to standard format (period as decimal separator)
                        amount_str = re.sub(
                            r"[.,](?=\d{3})", "", amount_str
                        )  # Remove thousand separators
                        amount_str = amount_str.replace(
                            ",", "."
                        )  # Convert decimal comma to point
                        try:
                            result["total"] = float(amount_str)
                            print(f"Parsed total amount: {result['total']}")
                            break
                        except ValueError as e:
                            print(f"Failed to parse amount {amount_str}: {e}")
                            continue
                if result["total"]:
                    break

            # Extract items with flexible price formats
            item_patterns = [
                r"(\d+)\s*x\s*(.*?)\s+(\d+[.,]\d{2})€",  # "2 x Item 7,98€"
                r"(\d+)\s*x\s*(.*?)\s+€\s*(\d+[.,]\d{2})",  # "2 x Item €7,98"
                r"(\d+)\s*(?:x|×|х|\*)\s*(.*?)\s*(?:[\$\£\€\¥\₹\R])?\s*([\d.,]+)",
                r"(\d+)\s*(.*?)\s*(?:@|at|á)?\s*(?:[\$\£\€\¥\₹\R])?\s*([\d.,]+)",
            ]

            print("Searching for items...")
            for line in lines:
                print(f"Checking line for items: {line}")
                for pattern in item_patterns:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        print(f"Item match found: {match.group()}")
                        if len(match.groups()) == 3:
                            quantity = int(match.group(1))
                            description = match.group(2).strip()
                            price_str = match.group(3)

                            # Clean up description
                            description = re.sub(
                                r"\s+", " ", description
                            )  # Normalize spaces
                            description = re.sub(
                                r"\.+\s*$", "", description
                            )  # Remove trailing dots

                            # Handle different price formats
                            price_str = re.sub(
                                r"[.,](?=\d{3})", "", price_str
                            )  # Remove thousand separators
                            price_str = price_str.replace(
                                ",", "."
                            )  # Convert decimal comma to point
                            try:
                                price = float(price_str)
                                result["items"].append(
                                    {
                                        "quantity": quantity,
                                        "description": description,
                                        "price": price,
                                        "acquisition_type": "purchase",
                                    }
                                )
                                print(
                                    f"Added item: {quantity}x {description} @ {price}"
                                )
                            except ValueError as e:
                                print(f"Failed to parse price {price_str}: {e}")
                                continue

            # Extract payment method
            payment_patterns = [
                r"(?:Payment|Paiement):\s*((?:CARTE\s+)?VISA)",
                r"(?:Payment|Betaling|Pago|Zahlung|支払|भुगतान)\s+(?:Method|Methode|Método|方法|विधि):\s*(\w+)",
                r"(?:Paid|Betaald|Pagado|Bezahlt|支払済|भुगतान)\s+(?:by|via|using|met|por|mit|で|द्वारा)\s+(\w+)",
                r"(?:VISA|MASTERCARD|AMEX|CASH|CREDIT|DEBIT|MAESTRO|UNIONPAY|JCB|現金|नकद|KONTANT)(?:\s|$)",
            ]

            for line in lines:
                print(f"Checking payment method in line: {line}")
                for pattern in payment_patterns:
                    payment_match = re.search(pattern, line, re.IGNORECASE)
                    if payment_match:
                        result["payment_method"] = (
                            payment_match.group(1)
                            if payment_match.groups()
                            else payment_match.group(0)
                        )
                        result["payment_method"] = result["payment_method"].upper()
                        print(f"Found payment method: {result['payment_method']}")
                        break
                if result["payment_method"]:
                    break

            # Extract tax information
            tax_patterns = [
                r"TVA\s*\((\d+(?:[.,]\d+)?%)\):\s*(\d+[.,]\d{2})\s*€",  # French VAT
                r"(?:VAT|GST|Tax|BTW|IVA|消費税|कर)\s*(?:\(?\s*(\d+(?:[.,]\d+)?%)\)?)?:\s*(?:[\$\£\€\¥\₹\R])?\s*([\d.,]+)",
            ]

            for line in lines:
                print(f"Checking tax info in line: {line}")
                for pattern in tax_patterns:
                    tax_match = re.search(pattern, line, re.IGNORECASE)
                    if tax_match:
                        print(f"Tax match found: {tax_match.group()}")
                        tax_rate = tax_match.group(1) if tax_match.group(1) else "N/A"
                        tax_amount_str = tax_match.group(2)
                        if tax_amount_str:
                            tax_amount_str = re.sub(
                                r"[.,](?=\d{3})", "", tax_amount_str
                            )
                            tax_amount_str = tax_amount_str.replace(",", ".")
                            try:
                                tax_amount = float(tax_amount_str)
                                result["tax_details"].append(
                                    {"rate": tax_rate, "amount": tax_amount}
                                )
                                print(f"Added tax detail: {tax_rate} - {tax_amount}")
                            except ValueError as e:
                                print(
                                    f"Failed to parse tax amount {tax_amount_str}: {e}"
                                )
                                continue

            print("Final result:", result)
            if not result["items"]:
                print("Warning: No items found in receipt")
            if not result["total"]:
                print("Warning: No total amount found in receipt")

            return result
        except Exception as e:
            print(f"Error parsing receipt: {e}")
            import traceback

            traceback.print_exc()
            return None
