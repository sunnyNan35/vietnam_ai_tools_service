"""Run once to seed initial 10 tools. Usage: python -m seeds.seed_tools"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_supabase

TOOLS = [
    {
        "name": "ChatGPT",
        "slug": "chatgpt",
        "description_vi": "ChatGPT là trợ lý AI thông minh do OpenAI phát triển. Bạn có thể dùng để viết văn, trả lời câu hỏi, lập trình, dịch thuật và nhiều tác vụ khác. Phiên bản miễn phí đã rất mạnh mẽ cho người dùng hàng ngày.",
        "description_en": "ChatGPT is an AI assistant by OpenAI for writing, coding, Q&A and more.",
        "website_url": "https://chat.openai.com",
        "affiliate_url": "https://chat.openai.com",
        "thumbnail_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/ChatGPT_logo.svg/120px-ChatGPT_logo.svg.png",
        "pricing": "freemium",
        "tags": ["chat", "viết văn", "lập trình"],
        "featured": True,
        "status": "published",
        "source": "manual",
        "category_slug": "tien-ich",
    },
    {
        "name": "Midjourney",
        "slug": "midjourney",
        "description_vi": "Midjourney là công cụ tạo hình ảnh AI hàng đầu thế giới. Chỉ cần mô tả bằng chữ, Midjourney sẽ tạo ra hình ảnh chất lượng cao, phù hợp cho thiết kế, marketing và sáng tạo nội dung.",
        "description_en": "Midjourney creates stunning AI-generated images from text prompts.",
        "website_url": "https://midjourney.com",
        "affiliate_url": "https://midjourney.com",
        "thumbnail_url": "",
        "pricing": "paid",
        "tags": ["hình ảnh", "AI art", "thiết kế"],
        "featured": True,
        "status": "published",
        "source": "manual",
        "category_slug": "hinh-anh",
    },
    {
        "name": "Canva AI",
        "slug": "canva-ai",
        "description_vi": "Canva AI tích hợp trí tuệ nhân tạo vào nền tảng thiết kế phổ biến nhất thế giới. Tạo logo, banner, bài đăng mạng xã hội chỉ trong vài phút với gợi ý thông minh từ AI.",
        "description_en": "Canva AI brings AI-powered design tools to the world's most popular design platform.",
        "website_url": "https://canva.com",
        "affiliate_url": "https://canva.com",
        "thumbnail_url": "",
        "pricing": "freemium",
        "tags": ["thiết kế", "hình ảnh", "marketing"],
        "featured": True,
        "status": "published",
        "source": "manual",
        "category_slug": "hinh-anh",
    },
    {
        "name": "GitHub Copilot",
        "slug": "github-copilot",
        "description_vi": "GitHub Copilot là trợ lý lập trình AI của Microsoft và GitHub. Công cụ tự động gợi ý code, hoàn thiện hàm và giải thích code ngay trong IDE của bạn, giúp tăng tốc độ lập trình đáng kể.",
        "description_en": "GitHub Copilot is an AI pair programmer that offers code suggestions in your IDE.",
        "website_url": "https://github.com/features/copilot",
        "affiliate_url": "https://github.com/features/copilot",
        "thumbnail_url": "",
        "pricing": "paid",
        "tags": ["lập trình", "code", "IDE"],
        "featured": True,
        "status": "published",
        "source": "manual",
        "category_slug": "lap-trinh",
    },
    {
        "name": "Suno AI",
        "slug": "suno-ai",
        "description_vi": "Suno AI cho phép bạn tạo ra các bài hát hoàn chỉnh chỉ từ một đoạn mô tả. Nhập lời bài hát hoặc chủ đề, AI sẽ tự động tạo nhạc và giọng hát chất lượng cao trong vài giây.",
        "description_en": "Suno AI generates complete songs with vocals from text descriptions.",
        "website_url": "https://suno.com",
        "affiliate_url": "https://suno.com",
        "thumbnail_url": "",
        "pricing": "freemium",
        "tags": ["âm nhạc", "tạo nhạc", "AI music"],
        "featured": False,
        "status": "published",
        "source": "manual",
        "category_slug": "am-nhac",
    },
    {
        "name": "Jasper AI",
        "slug": "jasper-ai",
        "description_vi": "Jasper AI là công cụ viết nội dung AI chuyên nghiệp dành cho doanh nghiệp. Tạo blog, email marketing, quảng cáo và nội dung SEO nhanh gấp 10 lần so với viết tay.",
        "description_en": "Jasper AI is the professional AI content writing platform for businesses.",
        "website_url": "https://jasper.ai",
        "affiliate_url": "https://jasper.ai",
        "thumbnail_url": "",
        "pricing": "paid",
        "tags": ["viết văn", "marketing", "SEO"],
        "featured": False,
        "status": "published",
        "source": "manual",
        "category_slug": "viet-van",
    },
    {
        "name": "Runway ML",
        "slug": "runway-ml",
        "description_vi": "Runway ML là nền tảng sáng tạo video AI hàng đầu. Chỉnh sửa video bằng ngôn ngữ tự nhiên, tạo video từ văn bản, và áp dụng hiệu ứng AI chuyên nghiệp dễ dàng.",
        "description_en": "Runway ML is a creative AI platform for video generation and editing.",
        "website_url": "https://runwayml.com",
        "affiliate_url": "https://runwayml.com",
        "thumbnail_url": "",
        "pricing": "freemium",
        "tags": ["video", "sáng tạo", "AI video"],
        "featured": False,
        "status": "published",
        "source": "manual",
        "category_slug": "video",
    },
    {
        "name": "Notion AI",
        "slug": "notion-ai",
        "description_vi": "Notion AI tích hợp trợ lý AI trực tiếp vào ứng dụng ghi chú Notion. Tóm tắt tài liệu, tạo nội dung, dịch thuật và cải thiện văn bản ngay trong workspace của bạn.",
        "description_en": "Notion AI brings AI writing assistance directly into your Notion workspace.",
        "website_url": "https://notion.so",
        "affiliate_url": "https://notion.so",
        "thumbnail_url": "",
        "pricing": "freemium",
        "tags": ["tiện ích", "ghi chú", "năng suất"],
        "featured": False,
        "status": "published",
        "source": "manual",
        "category_slug": "tien-ich",
    },
    {
        "name": "Duolingo Max",
        "slug": "duolingo-max",
        "description_vi": "Duolingo Max là gói học ngôn ngữ cao cấp với AI, bao gồm tính năng giải thích lỗi sai bằng AI và luyện hội thoại trực tiếp với nhân vật AI. Phù hợp cho học sinh, sinh viên Việt Nam muốn học tiếng Anh.",
        "description_en": "Duolingo Max uses AI to explain mistakes and enable roleplay conversations for language learning.",
        "website_url": "https://duolingo.com",
        "affiliate_url": "https://duolingo.com",
        "thumbnail_url": "",
        "pricing": "paid",
        "tags": ["học tập", "ngôn ngữ", "tiếng Anh"],
        "featured": False,
        "status": "published",
        "source": "manual",
        "category_slug": "hoc-tap",
    },
    {
        "name": "Grammarly",
        "slug": "grammarly",
        "description_vi": "Grammarly là công cụ kiểm tra ngữ pháp và viết lách AI mạnh mẽ nhất hiện nay. Phát hiện lỗi chính tả, cải thiện văn phong và đề xuất cách diễn đạt tốt hơn cho văn bản tiếng Anh.",
        "description_en": "Grammarly is an AI writing assistant that checks grammar, clarity and tone.",
        "website_url": "https://grammarly.com",
        "affiliate_url": "https://grammarly.com",
        "thumbnail_url": "",
        "pricing": "freemium",
        "tags": ["viết văn", "ngữ pháp", "tiếng Anh"],
        "featured": False,
        "status": "published",
        "source": "manual",
        "category_slug": "viet-van",
    },
]


def seed():
    sb = get_supabase()
    cats = sb.table("categories").select("id, slug").execute()
    cat_map = {row["slug"]: row["id"] for row in cats.data}

    for tool in TOOLS:
        category_slug = tool.pop("category_slug")
        tool["category_id"] = cat_map.get(category_slug)
        existing = sb.table("tools").select("id").eq("slug", tool["slug"]).execute()
        if existing.data:
            print(f"Skip (exists): {tool['name']}")
            continue
        sb.table("tools").insert(tool).execute()
        print(f"Inserted: {tool['name']}")


if __name__ == "__main__":
    seed()
    print("Seed complete.")
