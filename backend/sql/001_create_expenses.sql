-- Run once in the Supabase SQL editor.

create extension if not exists pgcrypto;

create table if not exists public.expenses (
    id          uuid primary key default gen_random_uuid(),
    title       varchar(100)   not null check (length(btrim(title)) > 0),
    amount      numeric(12, 2) not null check (amount > 0),
    category    text           not null check (category in ('food', 'travel', 'bills', 'other')),
    "date"      date           not null default current_date,
    created_at  timestamptz    not null default now()
);

create index if not exists expenses_date_created_idx on public.expenses ("date" desc, created_at desc);
create index if not exists expenses_category_date_idx on public.expenses (category, "date" desc);

-- Only the backend (secret key, which bypasses RLS) may touch this table; no public policies.
alter table public.expenses enable row level security;

-- Count + sum over ALL rows matching the filters (not just the current page).
create or replace function public.expense_totals(
    p_category text default null,
    p_from     date default null,
    p_to       date default null
)
returns table (total_count bigint, total_amount numeric)
language sql
stable
as $$
    select count(*), coalesce(sum(amount), 0)
    from public.expenses
    where (p_category is null or category = p_category)
      and (p_from is null or "date" >= p_from)
      and (p_to   is null or "date" <= p_to);
$$;

-- Per-category totals for a date range (used for the monthly summary).
create or replace function public.expense_category_totals(p_from date, p_to date)
returns table (category text, total numeric)
language sql
stable
as $$
    select category, coalesce(sum(amount), 0)
    from public.expenses
    where "date" between p_from and p_to
    group by category;
$$;

revoke execute on function public.expense_totals(text, date, date) from public, anon, authenticated;
revoke execute on function public.expense_category_totals(date, date) from public, anon, authenticated;
grant execute on function public.expense_totals(text, date, date) to service_role;
grant execute on function public.expense_category_totals(date, date) to service_role;
