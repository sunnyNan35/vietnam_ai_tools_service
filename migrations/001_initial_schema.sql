-- Enable UUID generation
create extension if not exists "pgcrypto";

-- Categories
create table if not exists categories (
  id uuid primary key default gen_random_uuid(),
  slug text unique not null,
  name_vi text not null,
  name_en text not null,
  icon text not null,
  sort_order int not null default 0
);

-- Tools
create table if not exists tools (
  id uuid primary key default gen_random_uuid(),
  slug text unique not null,
  name text not null,
  category_id uuid references categories(id),
  description_vi text,
  description_en text,
  website_url text not null,
  affiliate_url text,
  thumbnail_url text,
  pricing text check (pricing in ('free', 'paid', 'freemium')) default 'free',
  tags text[] default '{}',
  featured boolean default false,
  status text check (status in ('published', 'pending', 'rejected')) default 'pending',
  source text default 'manual',
  click_count int default 0,
  created_at timestamptz default now()
);

-- Row Level Security
alter table tools enable row level security;
alter table categories enable row level security;

create policy "Public can read published tools"
  on tools for select
  using (status = 'published');

create policy "Public can read categories"
  on categories for select
  using (true);

-- Seed categories
insert into categories (slug, name_vi, name_en, icon, sort_order) values
  ('viet-van',   'Viết văn',   'Writing',      '✍️',  1),
  ('hinh-anh',   'Hình ảnh',   'Images',       '🎨',  2),
  ('lap-trinh',  'Lập trình',  'Coding',       '💻',  3),
  ('video',      'Video',      'Video',        '🎬',  4),
  ('am-nhac',    'Âm nhạc',    'Music',        '🎵',  5),
  ('kinh-doanh', 'Kinh doanh', 'Business',     '💼',  6),
  ('hoc-tap',    'Học tập',    'Education',    '📚',  7),
  ('tien-ich',   'Tiện ích',   'Productivity', '⚡',  8)
on conflict (slug) do nothing;
