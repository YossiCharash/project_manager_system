"""
Error notifier service - sends WhatsApp alerts for critical errors.
Falls back gracefully if configuration is missing.
"""
import logging

logger = logging.getLogger(__name__)


def send_whatsapp_alert(
    error_message: str,
    traceback_str: str = "",
    path: str = "",
    error_type: str = "",
) -> None:
    """
    Send a WhatsApp alert via CallMeBot API.
    Requires CALLMEBOT_PHONE and CALLMEBOT_API_KEY environment variables.
    Silently skips if not configured.
    """
    try:
        from backend.core.config import settings
        phone = getattr(settings, "CALLMEBOT_PHONE", None)
        api_key = getattr(settings, "CALLMEBOT_API_KEY", None)

        if not phone or not api_key:
            return

        import requests
        from urllib.parse import quote

        # Build message (truncated to avoid URL length limits)
        parts = [f"[{error_type}]" if error_type else "[ERROR]"]
        if path:
            parts.append(f"Path: {path}")
        parts.append(error_message[:500])
        if traceback_str:
            parts.append(traceback_str[:300])

        message = "\n".join(parts)
        encoded_message = quote(message)

        url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_message}&apikey={api_key}"
        requests.get(url, timeout=10)
    except Exception:
        logger.debug("Failed to send WhatsApp alert", exc_info=True)
