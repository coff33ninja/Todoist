from typing import Dict, Any
from .error_logger import ErrorLogger

class ContextManager:
    def __init__(self):
        self.context = {}
        self.error_logger = ErrorLogger()

    def set_context(self, context: Dict[str, Any]) -> None:
        """Set conversation context with validation."""
        if not isinstance(context, dict):
            self.error_logger.log_warning("Invalid context type", type(context))
            return

        # Validate and clean context
        cleaned_context = {}
        if "previous_filters" in context:
            if isinstance(context["previous_filters"], dict):
                # Only keep valid filter types
                cleaned_filters = {}
                for k, v in context["previous_filters"].items():
                    if isinstance(k, str) and v is not None:
                        cleaned_filters[k] = v
                cleaned_context["previous_filters"] = cleaned_filters

        self.context = cleaned_context

    def get_context(self) -> Dict[str, Any]:
        """Get the current context."""
        return self.context
