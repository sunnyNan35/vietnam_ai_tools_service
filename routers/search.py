from fastapi import APIRouter, Query, HTTPException
from database import get_supabase
from models.schemas import ToolOut

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=list[ToolOut])
def search_tools(q: str = Query(..., min_length=1)):
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
