from fastapi import APIRouter, Request
from database import get_supabase
from models.schemas import CategoryOut
from middleware import limiter

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
# @limiter.limit("60/minute")
def list_categories(request: Request):
    sb = get_supabase()
    result = sb.table("categories").select("*").order("sort_order").execute()
    return result.data
