import re
import torch
from torch.nn.functional import softmax
from .error_logger import ErrorLogger

class IntentClassifier:
    def __init__(self):
        self.error_logger = ErrorLogger()

    def get_intent(self, query: str, model, tokenizer, intents) -> tuple[str, float]:
        """Get the final intent using both ML and rule-based approaches.

        Args:
            query: The input query string
            model: The ML model for intent classification
            tokenizer: The tokenizer for the model
            intents: List of supported intents

        Returns:
            Tuple of (final_intent, confidence_score)
        """
        # Get ML-based intent
        ml_intent, confidence = self._get_intent_confidence(query, model, tokenizer, intents)

        # Check if we should use rule-based override
        if self._should_override_intent(query, ml_intent, confidence):
            rule_based_intent = self._get_rule_based_intent(query)
            if rule_based_intent:
                self.error_logger.log_info(
                    "Overriding ML intent '%s' (conf: %.2f) with rule-based intent '%s'",
                    ml_intent, confidence, rule_based_intent
                )
                return rule_based_intent, 1.0

        return ml_intent, confidence

    def _get_intent_confidence(self, query: str, model, tokenizer, intents) -> tuple[str, float]:
        """Get intent and confidence score for a query using the ML model.

        Args:
            query: The input query string
            model: The ML model for intent classification
            tokenizer: The tokenizer for the model
            intents: List of supported intents

        Returns:
            Tuple of (predicted_intent, confidence_score)
        """
        # Prepare input
        inputs = tokenizer(
            query,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512
        )

        try:
            # Get model prediction
            with torch.no_grad():
                outputs = model(**inputs)
                logits = outputs.logits
                probabilities = softmax(logits, dim=1)
                confidence = torch.max(probabilities, dim=1).values.item()
                predicted_label = int(torch.argmax(probabilities, dim=1).item())

            # Handle out-of-range predictions
            if predicted_label >= len(intents):
                return "unknown", 0.0

            return intents[predicted_label], confidence

        except Exception as e:
            self.error_logger.log_error("Error in intent classification", e)
            return "unknown", 0.0

    def _get_rule_based_intent(self, query: str) -> Optional[str]:
        """Get intent using rule-based classification.

        Args:
            query: The input query string

        Returns:
            Predicted intent or None if no match
        """
        # Normalize query
        query = query.lower().strip()

        # Check each pattern
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return intent

        return None

    def _should_override_intent(self, query: str, ml_intent: str, confidence: float) -> bool:
        """Determine if rule-based intent should override ML intent.

        Args:
            query: The input query string
            ml_intent: The ML-predicted intent
            confidence: The confidence score from ML prediction

        Returns:
            True if should override, False otherwise
        """
        # Always override for very low confidence
        if confidence < 0.3:
            return True

        # Override for specific patterns regardless of confidence
        if re.search(r"^how\s+many\b", query, re.IGNORECASE):
            return True

        if re.search(r"^what\s+needs\s+(?:to\s+be\s+)?(?:fix|repair)", query, re.IGNORECASE):
            return True

        # Override if ML intent is unknown but confidence is not very high
        if ml_intent == "unknown" and confidence < 0.8:
            return True

        return False
