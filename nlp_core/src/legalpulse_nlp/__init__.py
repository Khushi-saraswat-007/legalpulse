"""LegalPulse NLP core (Part B): Module 1 clause/entity extraction + Module 2 contradiction detection."""
from .extractor import extract, extract_detailed, extract_from_text, validate_contract
from .contradiction import detect_contradictions
from .nli import HFNLIBackend, RuleBasedNLIBackend

__all__ = ["extract", "extract_detailed", "extract_from_text", "validate_contract",
           "detect_contradictions", "HFNLIBackend", "RuleBasedNLIBackend"]
