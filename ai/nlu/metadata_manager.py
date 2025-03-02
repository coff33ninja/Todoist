import os
import json
from datetime import datetime
from typing import Dict, Any
from .error_logger import ErrorLogger

class MetadataManager:
    def __init__(self, model_path: str):
        self.metadata_path = os.path.join(model_path, "metadata.json")
        self.error_logger = ErrorLogger()
        self.metadata = self._init_or_load_metadata()

    def _init_or_load_metadata(self) -> Dict[str, Any]:
        """Initialize or load model metadata."""
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.error_logger.log_warning("Failed to load metadata", e)

        # Create new metadata
        metadata = {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "last_trained": datetime.now().isoformat(),
            "num_intents": len(self.get_intents()),
            "training_samples": 0,
            "accuracy": 0.0,
            "parameters": {
                "model_type": "distilbert",
                "max_length": 512,
                "batch_size": 16,
                "learning_rate": 2e-5
            }
        }

        # Save metadata
        self._save_metadata(metadata)
        return metadata

    def _save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save model metadata to file."""
        try:
            os.makedirs(os.path.dirname(self.metadata_path), exist_ok=True)
            with open(self.metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            self.error_logger.log_error("Failed to save metadata", e)

    def get_version(self) -> str:
        """Get the current model version."""
        return self.metadata.get("version", "unknown")

    def get_intents(self) -> list:
        """Get the list of supported intents."""
        return [
            "search",
            "count",
            "value",
            "price_range",
            "repair",
            "purchase_history",
        ]
