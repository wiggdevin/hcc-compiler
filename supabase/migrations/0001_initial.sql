-- hcc-compiler: initial schema
-- Target: Supabase Postgres 15

create extension if not exists "uuid-ossp";

-- ─── coaches ──────────────────────────────────────────────────────────────────
-- One row per signed-in user. id = auth.uid() so RLS is trivial.
create table public.coaches (
  id              uuid        primary key references auth.users(id) on delete cascade,
  email           text        not null,
  display_name    text,
  practice_name   text,
  specialty       text,
  created_at      timestamptz not null default now(),
  onboarded_at    timestamptz
);

-- ─── intakes ──────────────────────────────────────────────────────────────────
-- One row per ClientIntake submitted by a coach.
create table public.intakes (
  id              uuid        primary key default uuid_generate_v4(),
  coach_id        uuid        not null references public.coaches(id) on delete cascade,
  client_id       text        not null,
  library_version text        not null,
  payload         jsonb       not null,         -- full ClientIntake JSON
  yaml_path       text,                         -- storage bucket 'intakes', e.g. <coach_id>/intake_<client_id>.yaml
  status          text        not null default 'pending', -- pending | compiling | compiled | failed
  error           text,
  created_at      timestamptz not null default now(),
  compiled_at     timestamptz,
  unique (coach_id, client_id)
);

create index intakes_coach_id_idx on public.intakes (coach_id, created_at desc);

-- ─── packs ────────────────────────────────────────────────────────────────────
-- One row per successful compile. Written by service role (compiler API).
create table public.packs (
  id               uuid   primary key default uuid_generate_v4(),
  intake_id        uuid   not null unique references public.intakes(id) on delete cascade,
  coach_id         uuid   not null references public.coaches(id) on delete cascade,
  library_version  text   not null,
  json_path        text   not null,  -- storage bucket 'packs'
  md_path          text   not null,
  pdf_path         text,
  overall_confidence real,
  pattern_count    int,
  atom_count       int,
  warnings_count   int,
  created_at       timestamptz not null default now()
);

create index packs_coach_id_idx on public.packs (coach_id, created_at desc);

-- ─── Row-Level Security ───────────────────────────────────────────────────────
alter table public.coaches enable row level security;
alter table public.intakes  enable row level security;
alter table public.packs    enable row level security;

-- coaches: read + update own row only
create policy "coach reads own row" on public.coaches
  for select using (id = auth.uid());
create policy "coach updates own row" on public.coaches
  for update using (id = auth.uid()) with check (id = auth.uid());

-- intakes: coaches see + write only their own
create policy "coach reads own intakes" on public.intakes
  for select using (coach_id = auth.uid());
create policy "coach inserts own intakes" on public.intakes
  for insert with check (coach_id = auth.uid());
create policy "coach updates own intakes" on public.intakes
  for update using (coach_id = auth.uid()) with check (coach_id = auth.uid());

-- packs: coaches read their own; service role writes (no coach insert/update policy)
create policy "coach reads own packs" on public.packs
  for select using (coach_id = auth.uid());

-- ─── Auto-create coach row on signup ─────────────────────────────────────────
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.coaches (id, email)
  values (new.id, new.email)
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ─── Storage bucket RLS (storage.objects) ────────────────────────────────────
-- Bucket 'intakes': coaches read + write objects under their own UUID prefix.
-- Bucket 'packs':   coaches read objects under their own UUID prefix; service role writes.

-- intakes bucket policies
create policy "coach insert intake objects" on storage.objects
  for insert with check (
    bucket_id = 'intakes'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "coach select intake objects" on storage.objects
  for select using (
    bucket_id = 'intakes'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "coach update intake objects" on storage.objects
  for update using (
    bucket_id = 'intakes'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "coach delete intake objects" on storage.objects
  for delete using (
    bucket_id = 'intakes'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

-- packs bucket policies (read-only for coaches; service role handles inserts)
create policy "coach select pack objects" on storage.objects
  for select using (
    bucket_id = 'packs'
    and (storage.foldername(name))[1] = auth.uid()::text
  );
