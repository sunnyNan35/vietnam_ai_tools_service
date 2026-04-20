from fastapi import APIRouter
from database import get_supabase
from models.schemas import CategoryOut

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories():
    sb = get_supabase()
    result = sb.table("categories").select("*").order("sort_order").execute()
    return result.data
