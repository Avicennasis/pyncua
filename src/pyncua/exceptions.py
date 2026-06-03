class NCUAError(Exception):
    """Base exception for all pyncua errors."""


class NCUANotFoundError(NCUAError):
    """Charter number not found (API returned isError=true)."""


class NCUAValidationError(NCUAError):
    """Invalid request parameters (400 or client-side validation)."""


class NCUAServerError(NCUAError):
    """NCUA API returned a 5xx error."""
