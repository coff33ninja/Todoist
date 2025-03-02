import re
import spacy
from typing import Dict, Any
from .error_logger import ErrorLogger

class FilterExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.error_logger = ErrorLogger()

    def extract_filters(self, query: str) -> Dict[str, Any]:
        """Extract filters from the query using spaCy and regex."""
        filters = {}
        doc = self.nlp(query)
        for ent in doc.ents:
            if ent.label_ == "GPE":  # Location
                filters["location"] = ent.text
            elif ent.label_ == "MONEY":  # Price
                filters["price"] = ent.text

        # Regex-based filter extraction
        m = re.search(r"in\s+(?:the\s+)?([\w\s]+)", query, re.IGNORECASE)
        if m:
            filters["location"] = m.group(1).strip()

        # Look for specific locations mentioned
        if re.search(r"\b(?:garage|kitchen|closet|living\s*room)\b", query, re.IGNORECASE):
            for loc in ["garage", "kitchen", "closet", "living room"]:
                if re.search(r"\b" + loc + r"\b", query, re.IGNORECASE):
                    filters["location"] = loc

        # Look for specific categories
        if re.search(r"\b(?:tools|clothing|electronics|appliances)\b", query, re.IGNORECASE):
            for cat in ["tools", "clothing", "electronics", "appliances"]:
                if re.search(r"\b" + cat + r"\b", query, re.IGNORECASE):
                    filters["category"] = cat

        m = re.search(r"category\s+([\w\s]+)", query, re.IGNORECASE)
        if m:
            filters["category"] = m.group(1).strip()

        m = re.search(r"tag[s]?\s+([\w\s,]+)", query, re.IGNORECASE)
        if m:
            filters["tags"] = m.group(1).strip()

        m = re.search(r"purchased\s+on\s+([\d/-]+)", query, re.IGNORECASE)
        if m:
            filters["purchase_date"] = m.group(1).strip()

        if re.search(r"\b(gifts?|free)\b", query, re.IGNORECASE):
            filters["is_gift"] = True

        m = re.search(r"stored\s+in\s+([\w\s]+)", query, re.IGNORECASE)
        if m:
            filters["storage_location"] = m.group(1).strip()

        m = re.search(r"used\s+in\s+([\w\s]+)", query, re.IGNORECASE)
        if m:
            filters["usage_location"] = m.group(1).strip()

        m = re.search(
            r"cost\s+(more|less)\s+than\s+(\d+(?:\.\d{2})?)", query, re.IGNORECASE
        )
        if m:
            filters["comparison"] = m.group(1)
            filters["price"] = m.group(2)

        m = re.search(r"last\s+(\w+)", query, re.IGNORECASE)
        if m:
            filters["time_period"] = m.group(1)

        # Check for repair-related terms
        if re.search(r"\b(?:fix|repair|broken|needs?\s+fixing|needs?\s+repair)\b", query, re.IGNORECASE):
            filters["needs_repair"] = True

        return filters

    def get_filters_with_context(self, query: str, context_manager) -> Dict[str, Any]:
        """Extract filters and merge with context."""
        # Extract new filters
        new_filters = self.extract_filters(query)

        # Merge with context if available
        if context_manager.get_context() and "previous_filters" in context_manager.get_context():
            filters = context_manager.get_context()["previous_filters"].copy()
            # Override previous filters with new ones
            filters.update(new_filters)
        else:
            filters = new_filters

        return filters
