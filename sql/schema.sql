-- =====================================================================
-- SCHEMA SUPABASE - Stock Dashboard & Analysis  (aman dijalankan berulang)
-- Supabase > SQL Editor > New query > paste semua > Run
-- =====================================================================

-- 1) DATA STOK HARIAN (struktur sama dengan CSV raw_oos) ---------------
create table if not exists public.raw_stock_oos (
    id            bigserial primary key,
    week          varchar(100),
    periode       int,
    date          date         not null,
    "user"        varchar(150),
    jabatan       varchar(100),
    area          varchar(100),
    area_fix      varchar(100),
    dc_mm         varchar(100),
    channel       varchar(100),
    account       varchar(100) not null,
    id_outlet     varchar(100) not null,
    outlet        varchar(255) not null,
    ket_prioritas varchar(100),
    id_product    bigint       not null,
    product       varchar(255) not null,
    stock_pajang  int default 0,
    stock_gudang  int default 0,
    total_stock   int default 0,
    stock_kosong  varchar(10),
    index_oos     int default 0,
    oos_reason    text,
    skam          varchar(150),
    uploaded_at   timestamptz default now(),
    -- agar data tidak dobel saat upsert
    constraint unique_daily_outlet_product unique (date, id_outlet, id_product)
);
create index if not exists idx_raw_stock_date    on public.raw_stock_oos (date);
create index if not exists idx_raw_stock_account on public.raw_stock_oos (account);
create index if not exists idx_raw_stock_outlet  on public.raw_stock_oos (id_outlet);
create index if not exists idx_raw_stock_product on public.raw_stock_oos (id_product);

-- 2) MASTER OUTLET & MASTER SKU = VIEW OTOMATIS dari raw_stock_oos -----
-- Jika sebelumnya sudah ada TABEL bernama sama (desain lama), hapus dulu.
do $$
declare t text;
begin
  foreach t in array array['master_outlet', 'master_sku'] loop
    if exists (select 1 from pg_class c join pg_namespace n on n.oid = c.relnamespace
               where n.nspname = 'public' and c.relname = t and c.relkind = 'r') then
      execute format('drop table public.%I cascade', t);
    end if;
  end loop;
end $$;

-- Satu baris unik per outlet (memakai data TERBARU)
create or replace view public.master_outlet with (security_invoker = true) as
select distinct on (id_outlet)
       id_outlet, outlet, account, channel, area, area_fix, ket_prioritas, "user", jabatan, skam
from public.raw_stock_oos
order by id_outlet, date desc;

-- Satu baris unik per SKU
create or replace view public.master_sku with (security_invoker = true) as
select distinct on (id_product)
       id_product, product
from public.raw_stock_oos
order by id_product, date desc;

-- (Opsional) tabel desain lama yang tidak dipakai aplikasi. Hapus jika masih kosong:
-- drop table if exists public.inventory_log, public.master_toko;

-- 3) SELL-IN (barang masuk) -------------------------------------------
-- Tanpa foreign key karena master berupa view; ID divalidasi oleh aplikasi.
create table if not exists public.sell_in (
    id          bigserial primary key,
    date        date        not null,
    id_outlet   varchar(100) not null,
    id_product  bigint      not null,
    qty         int         not null check (qty >= 0),
    notes       text,
    source      varchar(20) not null default 'manual',   -- manual | excel
    created_by  varchar(100),
    created_at  timestamptz not null default now(),
    constraint uq_sell_in unique (date, id_outlet, id_product)
);
create index if not exists ix_sell_in_date on public.sell_in (date);

-- 4) KEAMANAN & HAK AKSES ---------------------------------------------
alter table public.raw_stock_oos enable row level security;
alter table public.sell_in       enable row level security;   -- tanpa policy = anon/publishable key terkunci

grant usage on schema public to service_role;
grant all on all tables    in schema public to service_role;
grant all on all sequences in schema public to service_role;
alter default privileges in schema public grant all on tables    to service_role;
alter default privileges in schema public grant all on sequences to service_role;

revoke all on public.master_outlet, public.master_sku from anon, authenticated;
