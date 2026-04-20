from fastapi import APIRouter, HTTPException, Query
from database import get_supabase
from models.schemas import ToolOut, ToolDetailOut, ClickResponse, ToolListResponse

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("/featured", response_model=list[ToolOut])
def get_featured_tools():
    sb = get_supabase()
    result = (
        sb.table("tools")
        .select("*, categories(slug, name_vi, icon)")
        .eq("status", "published")
        .eq("featured", True)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


@router.get("", response_model=ToolListResponse)
def list_tools(
    category: str | None = Query(None),
    pricing: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=100),
):
    sb = get_supabase()
    offset = (page - 1) * limit
    q = (
        sb.table("tools")
        .select("*, categories(slug, name_vi, icon)", count="exact")
        .eq("status", "published")
    )
    if category:
        cat = sb.table("categories").select("id").eq("slug", category).single().execute()
        if cat.data:
            q = q.eq("category_id", cat.data["id"])
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
def get_tool(slug: str):
    sb = get_supabase()
    result = (
        sb.table("tools")
        .select("*, categories(slug, name_vi, icon)")
        .eq("slug", slug)
        .eq("status", "published")
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Tool not found")
    return result.data


@router.post("/{tool_id}/click", response_model=ClickResponse)
def track_click(tool_id: str):
    sb = get_supabase()
    result = (
        sb.table("tools")
        .select("affiliate_url, click_count")
        .eq("id", tool_id)
        .single()
        .execute()
    )
    if not result.data or not result.data.get("affiliate_url"):
        raise HTTPException(status_code=404, detail="Tool not found or no affiliate URL")
    new_count = (result.data.get("click_count") or 0) + 1
    sb.table("tools").update({"click_count": new_count}).eq("id", tool_id).execute()
    return ClickResponse(affiliate_url=result.data["affiliate_url"])
