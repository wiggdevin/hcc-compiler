-- hcc-compiler: client-viewer share tokens + coach brand fields
-- Target: Supabase Postgres 15

-- ─── extend coaches with brand fields ────────────────────────────────────────
-- The existing coaches row already carries display_name + practice_name from 0001;
-- add the three fields needed by the public client viewer's coach header.
alter table public.coaches
  add column if not exists headshot_url   text,
  add column if not exists contact_label  text,
  add column if not exists contact_url    text;

-- ─── share_tokens ────────────────────────────────────────────────────────────
-- One row per "Send to client" action. The row id IS the token surfaced in the URL.
-- Random UUID, unguessable, single-use semantically but reusable from URL until revoked or expired.
create table public.share_tokens (
  id            uuid        primary key default uuid_generate_v4(),
  pack_id       uuid        not null references public.packs(id)    on delete cascade,
  coach_id      uuid        not null references public.coaches(id)  on delete cascade,
  client_email  text,
  expires_at    timestamptz,
  revoked_at    timestamptz,
  sent_at       timestamptz,
  created_at    timestamptz not null default now()
);

create index share_tokens_pack_id_idx    on public.share_tokens (pack_id);
create index share_tokens_coach_id_idx   on public.share_tokens (coach_id, created_at desc);

-- ─── Row-Level Security ───────────────────────────────────────────────────────
-- Coach can manage own tokens. Anonymous public reads are intentionally NOT a policy;
-- /p/<token> hits use the service-role key from the Next.js server and bypass RLS.
alter table public.share_tokens enable row level security;

create policy "coach reads own share tokens" on public.share_tokens
  for select using (coach_id = auth.uid());
create policy "coach inserts own share tokens" on public.share_tokens
  for insert with check (coach_id = auth.uid());
create policy "coach updates own share tokens" on public.share_tokens
  for update using (coach_id = auth.uid()) with check (coach_id = auth.uid());
