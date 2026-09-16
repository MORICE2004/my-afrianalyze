import os
import logging

logger = logging.getLogger(__name__)

class BackendTelemetry:
    """
    Sentry and PostHog abstraction for the API layer.
    Allows total disablement and ensures no sensitive data leakage.
    """
    def __init__(self):
        self.sentry_enabled = os.getenv("SENTRY_ENABLED", "false").lower() == "true"
        self.posthog_enabled = os.getenv("POSTHOG_ENABLED", "false").lower() == "true"
        
        if self.sentry_enabled:
            # Dummy init for Sentry
            logger.info("Sentry initialized with DSN.")
            
        if self.posthog_enabled:
            # Dummy init for PostHog
            logger.info(f"PostHog initialized to {os.getenv('POSTHOG_HOST', 'app.posthog.com')}.")

    def _scrub_data(self, data: dict) -> dict:
        """
        Never send API keys, passwords, full source docs, or raw financial data.
        """
        scrubbed = {}
        sensitive_keys = {"password", "api_key", "secret", "financial_data", "source_doc"}
        
        for k, v in data.items():
            if any(s in k.lower() for s in sensitive_keys):
                scrubbed[k] = "[SCRUBBED]"
            elif isinstance(v, dict):
                scrubbed[k] = self._scrub_data(v)
            else:
                scrubbed[k] = v
        return scrubbed

    def capture_exception(self, error: Exception, context: dict = None):
        if not self.sentry_enabled:
            return
        
        safe_context = self._scrub_data(context or {})
        logger.error(f"[Sentry] Captured Exception: {error}. Context: {safe_context}")

    def capture_event(self, event_name: str, properties: dict = None):
        if not self.posthog_enabled:
            return
            
        safe_props = self._scrub_data(properties or {})
        logger.info(f"[PostHog] Captured Event: {event_name}. Properties: {safe_props}")

api_telemetry = BackendTelemetry()
