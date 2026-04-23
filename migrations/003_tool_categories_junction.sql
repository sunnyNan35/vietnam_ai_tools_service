-- Many-to-many junction table between tools and categories
-- A tool can belong to multiple categories

create table if not exists tool_categories (
  tool_id uuid not null references tools(id) on delete cascade,
  category_id uuid not null references categories(id) on delete cascade,
  primary key (tool_id, category_id)
);

-- RLS
alter table tool_categories enable row level security;

create policy "Public can read tool_categories"
  on tool_categories for select
  using (true);

-- Backfill: migrate existing category_id into the junction table
insert into tool_categories (tool_id, category_id)
select id, category_id
from tools
where category_id is not null
on conflict do nothing;

-- Index for reverse lookup (category -> tools)
create index if not exists idx_tool_categories_category_id on tool_categories(category_id);
