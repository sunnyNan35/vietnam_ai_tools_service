from fastapi import APIRouter, Query, HTTPException, Request
from database import get_supabase
from models.schemas import ToolOut
from middleware import limiter

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=list[ToolOut])
@limiter.limit("30/minute")
def search_tools(request: Request, q: str = Query(..., min_length=1)):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    sb = get_supabase()
    term = f"%{q.strip()}%"
    result = (
        sb.table("tools")
        .select("*")
        .eq("status", "published")
        .ilike("name", term)
        .execute()
    )
    return result.data
