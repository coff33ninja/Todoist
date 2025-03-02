from typing import Dict, Any
import sqlite3
from .model_manager import ModelManager
from .intent_classifier import IntentClassifier
from .filter_extractor import FilterExtractor
from .database_handler import DatabaseHandler, DatabaseError
from .context_manager import ContextManager
from .error_logger import ErrorLogger
from .metadata_manager import MetadataManager
from .intent_handlers import (
    handle_search,
    handle_count,
    handle_value,
    handle_price_range,
    handle_repair,
    handle_purchase_history,
)


class NLUProcessor:
    def __init__(self,
                 model_path: str = "ai_models/nlu_model",
                 db_path: str = "inventory.db",
                 max_retries: int = 3,
                 retry_delay: int = 1):
        """Initialize the NLUProcessor with model and database connections.

        Args:
            model_path: Path to the NLU model
            db_path: Path to the SQLite database
            max_retries: Maximum number of retries for operations
            retry_delay: Delay between retries in seconds
        """
        self.model_manager = ModelManager(model_path)
        self.intent_classifier = IntentClassifier()
        self.filter_extractor = FilterExtractor()
        self.database_handler = DatabaseHandler(db_path, max_retries, retry_delay)
        self.context_manager = ContextManager()
        self.error_logger = ErrorLogger()
        self.metadata_manager = MetadataManager(model_path)

        # Initialize performance tracking
        self._prediction_stats = {
            'total': 0,
            'by_intent': {},
            'confidence_sum': 0,
            'low_confidence_count': 0,
            'errors': 0,
            'last_evaluation': None
        }

        # Define supported intents as a class attribute for easy modification
        self.intents = [
            "search",
            "count",
            "value",
            "price_range",
            "repair",
            "purchase_history",
        ]

    def process_natural_language_query(self, query: str, db_conn=None) -> dict:
        """Process a natural language query and return the result.

        Args:
            query: The natural language query to process
            db_conn: Optional database connection (for testing)

        Returns:
            A dictionary containing the result and intent
        """
        if not query:
            return {"error": "Empty query", "intent": "unknown"}

        # Use provided database connection or default with retry mechanism
        try:
            cursor = self.database_handler.get_database_cursor(db_conn)
        except Exception as e:
            self.error_logger.log_error("Database connection error", e)
            self._prediction_stats['errors'] += 1
            return {"error": str(e), "intent": "unknown"}

        # Get the final intent using both ML and rule-based approaches
        try:
            predicted_intent, confidence = self.intent_classifier.get_intent(query)

            # Monitor prediction
            self._monitor_prediction(query, predicted_intent, confidence)

        except Exception as e:
            self.error_logger.log_error("Intent classification error", e)
            self._prediction_stats['errors'] += 1
            return {"error": "Failed to classify intent", "intent": "unknown"}

        # Extract and merge filters with context
        try:
            filters = self.filter_extractor.get_filters_with_context(query, self.context_manager)
        except Exception as e:
            self.error_logger.log_error("Filter extraction error", e)
            self._prediction_stats['errors'] += 1
            return {"error": "Failed to extract filters", "intent": predicted_intent}

        # Intent handlers with proper error handling
        try:
            result = self._handle_intent(predicted_intent, cursor, filters)
            result["intent"] = predicted_intent
            result["confidence"] = confidence
            result["model_version"] = self.metadata_manager.get_version()

            # Update context for multi-turn conversations
            self.context_manager.set_context({"previous_filters": filters})

            return result
        except Exception as e:
            self.error_logger.log_error(f"Error handling intent '{predicted_intent}'", e)
            self._prediction_stats['errors'] += 1
            return {
                "error": "Failed to process query",
                "intent": predicted_intent,
                "confidence": confidence,
                "model_version": self.metadata_manager.get_version()
            }

    def _handle_intent(
        self, intent: str, cursor: sqlite3.Cursor, filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle intent with proper error handling."""
        handlers = {
            "search": handle_search,
            "count": handle_count,
            "value": handle_value,
            "price_range": handle_price_range,
            "repair": handle_repair,
            "purchase_history": handle_purchase_history,
        }

        handler = handlers.get(
            intent, lambda _: {"message": "I'm not sure how to handle that."}
        )

        try:
            return handler(cursor, filters)
        except sqlite3.Error as e:
            self.error_logger.log_error(f"Database error handling intent '{intent}'", e)
            raise DatabaseError(f"Database error: {str(e)}")
        except Exception as e:
            self.error_logger.log_error(f"Error handling intent '{intent}'", e)
            raise

    def _monitor_prediction(self, query: str, predicted_intent: str, confidence: float) -> None:
        """Monitor and log prediction statistics."""
        self._prediction_stats['total'] += 1
        self._prediction_stats['confidence_sum'] += confidence
        if confidence < 0.5:
            self._prediction_stats['low_confidence_count'] += 1
        if predicted_intent not in self._prediction_stats['by_intent']:
            self._prediction_stats['by_intent'][predicted_intent] = 0
        self._prediction_stats['by_intent'][predicted_intent] += 1

        print(
            "Processed query: '%s' | Intent: '%s' | Confidence: %.2f",
            query, predicted_intent, confidence
        )

    def get_context(self) -> Dict[str, Any]:
        """Get the current context."""
        return self.context_manager.get_context()
