"""Book V presentation adapter package."""

from .adapter import PresentationAdapter, PresentationRejectionError
from .model import BookVInterfaceResponse
from .versions import (
    BOOK_V_PRESENTATION_CONTRACT_V1,
    BOOK_V_PRESENTATION_SCHEMA_V1,
)

__all__ = [
    "PresentationAdapter",
    "PresentationRejectionError",
    "BookVInterfaceResponse",
    "BOOK_V_PRESENTATION_CONTRACT_V1",
    "BOOK_V_PRESENTATION_SCHEMA_V1",
]
