"""Custom exceptions so callers (backend) can show meaningful messages."""


class NLPCoreError(Exception):
    """Base class for all nlp_core errors."""


class UnsupportedFormatError(NLPCoreError):
    """File extension is not .pdf, .docx or .txt."""


class EmptyDocumentError(NLPCoreError):
    """File opened fine but contains no usable text."""


class ScannedPDFError(NLPCoreError):
    """PDF seems to be scanned images: text layer is missing, OCR is required."""


class NoClausesFoundError(NLPCoreError):
    """Text was read but no clause could be segmented."""


class SchemaValidationError(NLPCoreError):
    """Output does not match schemas/contract.schema.json."""


class NLIModelError(NLPCoreError):
    """NLI model could not be loaded or run."""
