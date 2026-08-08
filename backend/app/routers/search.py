"""POST /search/web — explicit web search trigger (section 3.1).

This is read-only (no state changes), so unlike other agent tools it never
goes through the confirmation gate — it just returns results directly.
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.agent.tools import get_tool
from app.models import Device
from app.schemas import WebSearchRequest, WebSearchResponse, WebSearchResult
from app.security import get_current_device

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/web", response_model=WebSearchResponse)
def search_web(
    req: WebSearchRequest,
    device: Device = Depends(get_current_device),
) -> WebSearchResponse:
    tool = get_tool("web_search")
    if tool is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Web search unavailable")

    try:
        raw = tool.executor(query=req.query, max_results=req.max_results)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Search failed: {exc}") from exc

    results = []
    for line in raw.splitlines():
        line = line.lstrip("- ").strip()
        if not line:
            continue
        title, _, rest = line.partition(":")
        url, _, snippet = rest.strip().partition(" — ")
        results.append(WebSearchResult(title=title.strip(), url=url.strip(), snippet=snippet.strip()))

    return WebSearchResponse(query=req.query, results=results)
