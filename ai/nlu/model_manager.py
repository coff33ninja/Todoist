import os
from typing import Tuple
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from .error_logger import ErrorLogger
from .metadata_manager import MetadataManager


class ModelError(Exception):
    """Raised when there is an error related to model loading, creation, or configuration.

    This exception is typically raised when:
    - The model cannot be loaded from the specified path.
    - The model cannot be created due to configuration issues.
    - There is a mismatch between the model's configuration and the metadata.

    The exception message will provide details about the specific error.
    """


class ModelManager:
    def __init__(self, model_path: str):
        """Initialize the ModelManager with a specified model path.

        Args:
            model_path (str): Path to store/load the model and related files.
        """
        self.model_path = model_path
        self.checkpoint_dir = os.path.join(model_path, "checkpoints")
        self.metadata_path = os.path.join(model_path, "metadata.json")
        os.makedirs(self.checkpoint_dir, exist_ok=True)

        self.error_logger = ErrorLogger()
        self.metadata_manager = MetadataManager(model_path)

        self.model, self.tokenizer = self._load_or_create_model()

    def _load_or_create_model(
        self,
    ) -> Tuple[AutoModelForSequenceClassification, AutoTokenizer]:
        """Load an existing model or create a new one if it doesn’t exist.

        Returns:
            Tuple[AutoModelForSequenceClassification, AutoTokenizer]: The loaded or created model and tokenizer.

        Raises:
            ModelError: If model loading or creation fails due to file issues, configuration errors, or unexpected exceptions.
        """
        model_name = "distilbert-base-uncased"

        try:
            # Load tokenizer with fallback
            try:
                self.error_logger.log_info("Loading fast tokenizer for %s", model_name)
                tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
            except Exception as e:
                self.error_logger.log_warning(
                    "Fast tokenizer unavailable, falling back to regular: %s", str(e)
                )
                tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)

            # Get number of intents with validation
            try:
                intents = self.metadata_manager.get_intents()
                if not isinstance(intents, (list, set, tuple)):
                    raise ValueError(
                        "Intents must be a collection (list, set, or tuple)"
                    )
                num_labels = len(intents)
                self.error_logger.log_info(
                    "Retrieved %d intents from metadata", num_labels
                )
            except Exception as e:
                self.error_logger.log_error(
                    "Failed to retrieve intents from metadata", e
                )
                raise ModelError(f"Failed to retrieve intents: {str(e)}") from e

            # Load or create model
            model_exists = os.path.exists(self.model_path) and os.path.exists(
                os.path.join(self.model_path, "config.json")
            )
            if model_exists:
                self.error_logger.log_info(
                    "Loading existing model from %s", self.model_path
                )
                try:
                    model = AutoModelForSequenceClassification.from_pretrained(
                        self.model_path,
                        num_labels=num_labels,
                        problem_type="single_label_classification",
                    )
                except OSError as e:
                    self.error_logger.log_error("Failed to load model from disk", e)
                    raise ModelError(
                        f"Failed to load model from {self.model_path}: {str(e)}"
                    ) from e
            else:
                self.error_logger.log_info(
                    "Creating new model based on %s with %d labels",
                    model_name,
                    num_labels,
                )
                try:
                    model = AutoModelForSequenceClassification.from_pretrained(
                        model_name,
                        num_labels=num_labels,
                        problem_type="single_label_classification",
                    )
                    model.save_pretrained(self.model_path)
                    tokenizer.save_pretrained(self.model_path)
                    self.error_logger.log_info(
                        "New model and tokenizer saved to %s", self.model_path
                    )
                except Exception as e:
                    self.error_logger.log_error(
                        "Failed to create and save new model", e
                    )
                    raise ModelError(f"Failed to create new model: {str(e)}") from e

            # Verify model configuration
            if model.config.num_labels != num_labels:
                self.error_logger.log_warning(
                    "Model labels (%d) don’t match intents (%d), recreating model",
                    model.config.num_labels,
                    num_labels,
                )
                model = AutoModelForSequenceClassification.from_pretrained(
                    model_name,
                    num_labels=num_labels,
                    problem_type="single_label_classification",
                )
                model.save_pretrained(self.model_path)
                tokenizer.save_pretrained(self.model_path)
                self.error_logger.log_info(
                    "Recreated model and tokenizer saved to %s", self.model_path
                )

            return model, tokenizer

        except ModelError:
            raise
        except Exception as e:
            self.error_logger.log_error(
                "Unexpected error during model loading/creation", e
            )
            raise ModelError(f"Unexpected error in model setup: {str(e)}") from e
