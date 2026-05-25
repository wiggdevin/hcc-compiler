-- Phase 4 billing tables: subscriptions, credits, billing_events.
-- Depends on: 0001_initial.sql (public.coaches table must exist first).

create table public.subscriptions (
  coach_id              uuid        primary key references public.coaches(id) on delete cascade,
  stripe_customer_id    text        not null,
  stripe_subscription_id text       not null,
  status                text        not null,  -- active | trialing | past_due | canceled | incomplete | unpaid
  plan                  text        not null,  -- 'active_coach'
  current_period_end    timestamptz not null,
  cancel_at_period_end  boolean     not null default false,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now()
);

create table public.credits (
  coach_id    uuid        primary key references public.coaches(id) on delete cascade,
  balance     int         not null default 0,
  updated_at  timestamptz not null default now()
);

create table public.billing_events (
  id               uuid        primary key default gen_random_uuid(),
  coach_id         uuid        references public.coaches(id) on delete set null,
  stripe_event_id  text        not null unique,  -- idempotency key
  event_type       text        not null,         -- 'checkout.session.completed' etc
  payload          jsonb       not null,
  processed_at     timestamptz not null default now()
);

create index billing_events_coach_idx on public.billing_events (coach_id, processed_at desc);

-- RLS: coaches can only read their own rows; writes are service-role only.
alter table public.subscriptions enable row level security;
alter table public.credits        enable row level security;
alter table public.billing_events enable row level security;

create policy "coach reads own subscription"
  on public.subscriptions for select
  using (coach_id = auth.uid());

create policy "coach reads own credits"
  on public.credits for select
  using (coach_id = auth.uid());

-- billing_events intentionally has no SELECT policy — service role only.

-- Atomic credit decrement. Returns true if a credit was consumed, false if balance was 0.
-- Called from the compile gate via admin client (bypasses RLS).
create or replace function public.consume_credit(p_coach_id uuid)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare
  consumed boolean;
begin
  update public.credits
     set balance    = balance - 1,
         updated_at = now()
   where coach_id = p_coach_id
     and balance > 0
   returning true into consumed;
  return coalesce(consumed, false);
end;
$$;
