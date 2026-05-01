from pydantic import BaseModel, model_validator
from typing import Optional, Any
from datetime import datetime


class CategoryOut(BaseModel):
    id: str
    slug: str
    name_vi: str
    name_en: str
    icon: str
    sort_order: int


class CategoryBrief(BaseModel):
    slug: str
    name_vi: str
    icon: str


class ToolOut(BaseModel):
    id: str
    slug: str
    name: str
    category_id: Optional[str] = None
    categories: list[CategoryBrief] = []
    description_vi: Optional[str] = None
    description_en: Optional[str] = None
    thumbnail_url: Optional[str] = None
    pricing: str
    tags: list[str]
    featured: bool
    status: str
    source: str
    website_url: str
    affiliate_url: Optional[str] = None
    click_count: int
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def extract_categories_from_junction(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        # Supabase nested join: tool_categories: [{categories: {slug, name_vi, icon}}, ...]
        junction_rows = data.get("tool_categories") or []
        categories = []
        for row in junction_rows:
            if isinstance(row, dict):
                cat = row.get("categories")
                if cat:
                    categories.append(cat)
        data["categories"] = categories
        return data


class ToolDetailOut(ToolOut):
    website_url: str


class ClickResponse(BaseModel):
    affiliate_url: str


class ToolListResponse(BaseModel):
    items: list[ToolOut]
    total: int
    page: int
    limit: int


class AdminLoginRequest(BaseModel):
    password: str


class AdminLoginResponse(BaseModel):
    token: str
    expires_at: datetime


class ToolCreateUpdate(BaseModel):
    name: str
    slug: str
    description_vi: str
    category_ids: list[str] = []
    website_url: str
    pricing: str = "unknown"
    tags: list[str] = []
    status: str = "draft"
    featured: bool = False
    affiliate_url: Optional[str] = None
    description_en: Optional[str] = None
    source: str = "manual"
    thumbnail_url: Optional[str] = None
