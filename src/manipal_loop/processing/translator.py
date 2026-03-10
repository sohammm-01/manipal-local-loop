"""Translation helper — wraps googletrans with graceful fallback."""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def translate_if_needed(text: str) -> Tuple[str, str]:
    """Translate *text* to English if the detected language is not English.

    Uses the ``googletrans`` library when available.  On any error the
    original text is returned unchanged.

    Args:
        text: Input string, possibly in a non-English language.

    Returns:
        A tuple of (translated_or_original_text, detected_language_code).
    """
    if not text or not text.strip():
        return text, "en"

    try:
        from googletrans import Translator  # type: ignore

        translator = Translator()
        result = translator.translate(text, dest="en")
        detected = result.src if result.src else "en"
        translated = result.text if result.text else text
        return translated, detected
    except ImportError:
        logger.debug("googletrans not installed; returning text as-is")
        return text, "en"
    except Exception as exc:
        logger.warning("Translation failed: %s", exc)
        return text, "en"
