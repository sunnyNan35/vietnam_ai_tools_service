import hashlib
import secrets
import time
from fastapi import APIRouter, HTTPException, Request, status
from database import get_supabase
from config import settings
from models.schemas import AdminLoginRequest, AdminLoginResponse, ToolCreateUpdate, ToolOut
from middleware import verify_admin_token, add_admin_token, require_admin_auth

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_TOKEN_EXPIRES_IN = 1800  # 30 minutes


def _verify_password(password: str) -> bool:
    input_hash = hashlib.sha256(password.encode()).hexdigest()
    expected_hash = hashlib.sha256(settings.admin_password.encode()).hexdigest()
    return input_hash == expected_hash


@router.post("/login", response_model=AdminLoginResponse)
def admin_login(req: AdminLoginRequest):
    if not _verify_password(req.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    token = secrets.token_urlsafe(32)
    expires_at_seconds = time.time() + ADMIN_TOKEN_EXPIRES_IN
    add_admin_token(token, expires_at_seconds)

    # Return milliseconds timestamp (13 digits) for easier frontend comparison
    expires_at_ms = int(expires_at_seconds * 1000)
    return AdminLoginResponse(
        token=token,
        expires_at=expires_at_ms
    )


@router.get("/tools", response_model=list[ToolOut])
async def get_admin_tools(request: Request):
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")
    token = auth_header[7:]
    if not verify_admin_token(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired or invalid")

    sb = get_supabase()
    result = sb.table("tools").select("*, tool_categories(categories(slug, name_vi, icon))").execute()
    return result.data or []


@router.post("/tools", response_model=ToolOut)
async def create_tool(tool: ToolCreateUpdate, request: Request):
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")
    token = auth_header[7:]
    if not verify_admin_token(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired or invalid")

    sb = get_supabase()

    # Check if slug already exists
    existing = sb.table("tools").select("id").eq("slug", tool.slug).execute()
    if existing.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug already exists")

    # Insert tool (exclude category_ids from tool data)
    tool_data = tool.model_dump(exclude={"category_ids"})
    result = sb.table("tools").insert(tool_data).execute()

    if not result.data:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create tool")

    tool_id = result.data[0]["id"]

    # Insert category relationships
    if tool.category_ids:
        category_links = [{"tool_id": tool_id, "category_id": cat_id} for cat_id in tool.category_ids]
        sb.table("tool_categories").insert(category_links).execute()

    # Fetch and return created tool
    created = sb.table("tools").select("*, tool_categories(categories(slug, name_vi, icon))").eq("id", tool_id).single().execute()
    return created.data


@router.put("/tools/{tool_id}", response_model=ToolOut)
async def update_tool(tool_id: str, tool: ToolCreateUpdate, request: Request):
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")
    token = auth_header[7:]
    if not verify_admin_token(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired or invalid")

    sb = get_supabase()

    # Check if tool exists
    existing = sb.table("tools").select("id", "slug").eq("id", tool_id).single().execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")

    # Check if new slug conflicts with existing tool (different ID)
    if tool.slug != existing.data["slug"]:
        slug_conflict = sb.table("tools").select("id").eq("slug", tool.slug).execute()
        if slug_conflict.data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug already exists")

    # Update tool (exclude category_ids from tool data)
    tool_data = tool.model_dump(exclude={"category_ids"})
    sb.table("tools").update(tool_data).eq("id", tool_id).execute()

    # Delete old category relationships
    sb.table("tool_categories").delete().eq("tool_id", tool_id).execute()

    # Insert new category relationships
    if tool.category_ids:
        category_links = [{"tool_id": tool_id, "category_id": cat_id} for cat_id in tool.category_ids]
        sb.table("tool_categories").insert(category_links).execute()

    # Fetch and return updated tool
    updated = sb.table("tools").select("*, tool_categories(categories(slug, name_vi, icon))").eq("id", tool_id).single().execute()
    return updated.data


@router.delete("/tools/{tool_id}")
async def delete_tool(tool_id: str, request: Request):
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")
    token = auth_header[7:]
    if not verify_admin_token(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired or invalid")

    sb = get_supabase()

    # Check if tool exists
    existing = sb.table("tools").select("id").eq("id", tool_id).execute()
    if not existing.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found")

    # Delete category relationships
    sb.table("tool_categories").delete().eq("tool_id", tool_id).execute()

    # Delete tool
    sb.table("tools").delete().eq("id", tool_id).execute()

    return {"message": "Tool deleted successfully"}
