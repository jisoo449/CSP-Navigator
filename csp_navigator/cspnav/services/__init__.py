"""서비스 기능 영역. UI(Streamlit·FastAPI)는 get_service()로만 서비스를 얻는다. (NF2005)"""

from __future__ import annotations

from functools import lru_cache

from cspnav.errors import ServiceError


@lru_cache(maxsize=1)
def get_service():
    """실제 RAG 서비스(NavigatorService) 1개를 만들어 재사용한다. (NF2005)"""
    from cspnav.services.navigator import NavigatorService

    return NavigatorService()


__all__ = ["get_service", "ServiceError"]
