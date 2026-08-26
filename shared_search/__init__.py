"""Universal search gateway shared by Personal Agent and ASPA."""

from .gateway import SearchGateway
from .models import PageContent, SearchQuery, SearchResult
from .policy import SearchPolicy

__all__ = ["PageContent", "SearchGateway", "SearchPolicy", "SearchQuery", "SearchResult"]
