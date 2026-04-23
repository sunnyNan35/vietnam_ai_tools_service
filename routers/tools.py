from fastapi import APIRouter, HTTPException, Query, Request
from database import get_supabase
from models.schemas import ToolOut, ToolDetailOut, ClickResponse, ToolListResponse
from middleware import limiter, is_duplicate_click
from slowapi.util import get_remote_address

router = APIRouter(prefix="/api/tools", tags=["tools"])

# Join string: fetch categories via junction table
_TOOL_SELECT = "*, tool_categories(categories(slug, name_vi, icon))"


def _resolve_category_ids(sb, category_slug: str) -> list[str]:
    """Return all tool IDs that belong to a given category slug."""
    cat = sb.table("categories").select("id").eq("slug", category_slug).single().execute()
    if not cat.data:
        return []
    cat_id = cat.data["id"]
    rows = sb.table("tool_categories").select("tool_id").eq("category_id", cat_id).execute()
    return [r["tool_id"] for r in (rows.data or [])]


@router.get("/featured", response_model=list[ToolOut])
#@limiter.limit("60/minute")
def get_featured_tools(request: Request):
    sb = get_supabase()
    result = (
        sb.table("tools")
        .select(_TOOL_SELECT)
        .eq("status", "published")
        .eq("featured", True)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


@router.get("", response_model=ToolListResponse)
#@limiter.limit("60/minute")
def list_tools(
    request: Request,
    category: str | None = Query(None),
    pricing: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=100),
):
    sb = get_supabase()
    offset = (page - 1) * limit
    q = (
        sb.table("tools")
        .select(_TOOL_SELECT, count="exact")
        .eq("status", "published")
    )
    if category:
        tool_ids = _resolve_category_ids(sb, category)
        if not tool_ids:
            return ToolListResponse(items=[], total=0, page=page, limit=limit)
        q = q.in_("id", tool_ids)
    if pricing:
        q = q.eq("pricing", pricing)
    q = q.order("created_at", desc=True).range(offset, offset + limit - 1)
    result = q.execute()
    return ToolListResponse(
        items=result.data,
        total=result.count or 0,
        page=page,
        limit=limit,
    )


@router.get("/{slug}", response_model=ToolDetailOut)
#@limiter.limit("60/minute")
def get_tool(request: Request, slug: str):
    sb = get_supabase()
    result = (
        sb.table("tools")
        .select(_TOOL_SELECT)
        .eq("slug", slug)
        .eq("status", "published")
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Tool not found")
    return result.data


@router.post("/{tool_id}/click", response_model=ClickResponse)
# @limiter.limit("20/minute")
def track_click(request: Request, tool_id: str):
    ip = get_remote_address(request)
    """
    if is_duplicate_click(ip, tool_id):
        raise HTTPException(status_code=429, detail="Duplicate click")
    """
    sb = get_supabase()
    result = (
        sb.table("tools")
        .select("website_url, click_count")
        .eq("id", tool_id)
        .single()
        .execute()
    )
    if not result.data or not result.data.get("website_url"):
        raise HTTPException(status_code=404, detail="Tool not found or no website URL")
    new_count = (result.data.get("click_count") or 0) + 1
    sb.table("tools").update({"click_count": new_count}).eq("id", tool_id).execute()
    return ClickResponse(affiliate_url=result.data["website_url"])
