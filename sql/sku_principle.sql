-- =====================================================================
-- MASTER KODE SKU PRINCIPLE  ->  dihubungkan ke id_product di data stok
-- Supabase > SQL Editor > New query > paste semua > Run  (aman dijalankan berulang)
-- Prasyarat: sql/schema.sql sudah dijalankan & data stok sudah pernah di-upload
-- (karena id_product diambil dari view master_sku).
-- =====================================================================

-- 1) Master dari file principle -----------------------------------------
create table if not exists public.sku_principle (
    kode_sku         varchar(50) primary key,     -- kode yang dikenal sales (no_category_new)
    short_sku        varchar(50),                 -- TIDAK unik (Yoasobi memakai short_sku yang sama dgn reguler)
    produk           text,
    own_comp         varchar(20),
    brand            varchar(100),
    sub_brand        varchar(255) not null,       -- nama pencocok ke master_sku.product
    category         varchar(100),
    sub_category     varchar(100),
    size             varchar(100),
    grouping_size_new varchar(100),
    actual_size      varchar(50),
    display_category varchar(50),
    id_product       bigint,                      -- diisi otomatis oleh langkah 3
    kode_sementara   boolean not null default false,  -- true = kode TMP-..., ganti dgn kode resmi
    updated_at       timestamptz not null default now()
);
create unique index if not exists ux_sku_principle_id_product
    on public.sku_principle (id_product) where id_product is not null;

-- 2) Isi data (upsert: menimpa atribut, TIDAK menimpa id_product / kode yang sudah Anda ganti) ----
insert into public.sku_principle
  (kode_sku, short_sku, produk, own_comp, brand, sub_brand, category, sub_category,
   size, grouping_size_new, actual_size, display_category, kode_sementara)
values
  ('5300927', 'UMCHOC1L', '5300927 ULTRA MILK CHOCOLATE 1000 ML/12 (HELICAP)', 'OWN', 'ULTRA MILK', 'ULTRA MILK CHOCOLATE 1000 ML', 'MILK', 'REGULER', 'SIZE 1 LITER REGULER', '946 ml - 1000 ml MILK', '1 LITER', 'REGULER', false),
  ('5300926', 'UMFC1L', '5300926 ULTRA MILK FULL CREAM 1000 ML/12 (HELICAP)', 'OWN', 'ULTRA MILK', 'ULTRA MILK FULL CREAM 1000 ML', 'MILK', 'REGULER', 'SIZE 1 LITER REGULER', '946 ml - 1000 ml MILK', '1 LITER', 'REGULER', false),
  ('5300929', 'UFCHOC1L', '5300929 ULTRA MILK LOW FAT CHOCOLATE 1000 ML/12 (HELICAP)', 'OWN', 'ULTRA MILK', 'ULTRA MILK LOW FAT CHOCOLATE 1000 ML', 'MILK', 'LOW FAT', 'SIZE 1 LITER LOW FAT', '946 ml - 1000 ml MILK', '1 LITER', 'REGULER', false),
  ('5300928', 'UFPLAIN1L', '5300928 ULTRA MILK LOW FAT PLAIN 1000 ML/12 (HELICAP)', 'OWN', 'ULTRA MILK', 'ULTRA MILK LOW FAT PLAIN 1000 ML', 'MILK', 'LOW FAT', 'SIZE 1 LITER LOW FAT', '946 ml - 1000 ml MILK', '1 LITER', 'REGULER', false),
  ('5300938', 'UMCHOC750', '5300938 ULTRA MILK CHOCOLATE 750 ML/12', 'OWN', 'ULTRA MILK', 'ULTRA MILK CHOCOLATE 750 ML', 'MILK', 'REGULER', 'SIZE 750ML REGULER', '750 ml MILK', '750 ML', 'REGULER', false),
  ('5300937', 'UMFC750', '5300937 ULTRA MILK FULL CREAM 750 ML/12', 'OWN', 'ULTRA MILK', 'ULTRA MILK FULL CREAM 750 ML', 'MILK', 'REGULER', 'SIZE 750ML REGULER', '750 ml MILK', '750 ML', 'REGULER', false),
  ('5300947', 'UMMOCCA750', '5300947 ULTRA MILK MOCCA 750 ML/12', 'OWN', 'ULTRA MILK', 'ULTRA MILK MOCCA 750 ML', 'MILK', 'REGULER', 'SIZE 750ML REGULER', '750 ml MILK', '750 ML', 'REGULER', false),
  ('5300946', 'UMSTRAW750', '5300946 ULTRA MILK STRAWBERRY 750 ML/12', 'OWN', 'ULTRA MILK', 'ULTRA MILK STRAWBERRY 750 ML', 'MILK', 'REGULER', 'SIZE 750ML REGULER', '750 ml MILK', '750 ML', 'REGULER', false),
  ('5300457', 'UMCHOC250', '5300457 ULTRA MILK CHOCOLATE 250 ML/24', 'OWN', 'ULTRA MILK', 'ULTRA MILK CHOCOLATE 250 ML', 'MILK', 'REGULER', 'SIZE 250 ML REGULER', '225 ml - 250 ml MILK', '250 ML', 'REGULER', false),
  ('5300456', 'UMFC250', '5300456 ULTRA MILK FULL CREAM 250 ML/24', 'OWN', 'ULTRA MILK', 'ULTRA MILK FULL CREAM 250 ML', 'MILK', 'REGULER', 'SIZE 250 ML REGULER', '225 ml - 250 ml MILK', '250 ML', 'REGULER', false),
  ('5300459', 'UMMOCCA250', '5300459 ULTRA MILK MOCCA 250 ML/24', 'OWN', 'ULTRA MILK', 'ULTRA MILK MOCCA 250 ML', 'MILK', 'REGULER', 'SIZE 250 ML REGULER', '225 ml - 250 ml MILK', '250 ML', 'REGULER', false),
  ('5300458', 'UMSTRAW250', '5300458 ULTRA MILK STRAWBERRY 250 ML/24', 'OWN', 'ULTRA MILK', 'ULTRA MILK STRAWBERRY 250 ML', 'MILK', 'REGULER', 'SIZE 250 ML REGULER', '225 ml - 250 ml MILK', '250 ML', 'REGULER', false),
  ('5300446', 'UMLFCHOC250', '5300446 ULTRA MILK LFHC CHOCOLATE 250 ML/24', 'OWN', 'ULTRA MILK', 'ULTRA MILK LOW FAT CHOCOLATE 250 ML', 'MILK', 'LOW FAT', 'SIZE 250 ML LOW FAT', '225 ml - 250 ml MILK', '250 ML', 'REGULER', false),
  ('5300460', 'UMLFPLAIN250', '5300460 ULTRA MILK LFHC PLAIN 250 ML/24', 'OWN', 'ULTRA MILK', 'ULTRA MILK LOW FAT PLAIN 250 ML', 'MILK', 'LOW FAT', 'SIZE 250 ML LOW FAT', '225 ml - 250 ml MILK', '250 ML', 'REGULER', false),
  ('TMP-UMBLUEBERRY200', 'UMBLUEBERRY200', 'ULTRA MILK BLUEBERRY 200 ML', 'OWN', 'ULTRA MILK', 'ULTRA MILK BLUEBERRY 200 ML', 'MILK', 'REGULER', 'SIZE 200 ML REGULER', '180 ml - 200 ml MILK', '200 ML', 'REGULER', true),
  ('5300912', 'UMCARAMEL200', '5300912 ULTRA MILK CARAMEL 200 ML/24', 'OWN', 'ULTRA MILK', 'ULTRA MILK CARAMEL 200 ML', 'MILK', 'REGULER', 'SIZE 200 ML REGULER', '180 ml - 200 ml MILK', '200 ML', 'REGULER', false),
  ('5300462', 'UMCHOC200', '5300462 ULTRA MILK CHOCOLATE 200 ML/24', 'OWN', 'ULTRA MILK', 'ULTRA MILK CHOCOLATE 200 ML', 'MILK', 'REGULER', 'SIZE 200 ML REGULER', '180 ml - 200 ml MILK', '200 ML', 'REGULER', false),
  ('5300461', 'UMFC200', '5300461 ULTRA MILK FULL CREAM 200 ML/24', 'OWN', 'ULTRA MILK', 'ULTRA MILK FULL CREAM 200 ML', 'MILK', 'REGULER', 'SIZE 200 ML REGULER', '180 ml - 200 ml MILK', '200 ML', 'REGULER', false),
  ('5300464', 'UMMOCCA200', '5300464 ULTRA MILK MOCCA 200 ML/24', 'OWN', 'ULTRA MILK', 'ULTRA MILK MOCCA 200 ML', 'MILK', 'REGULER', 'SIZE 200 ML REGULER', '180 ml - 200 ml MILK', '200 ML', 'REGULER', false),
  ('5300463', 'UMSTRAW200', '5300463 ULTRA MILK STRAWBERRY 200 ML/24', 'OWN', 'ULTRA MILK', 'ULTRA MILK STRAWBERRY 200 ML', 'MILK', 'REGULER', 'SIZE 200 ML REGULER', '180 ml - 200 ml MILK', '200 ML', 'REGULER', false),
  ('5300914', 'UMTARO200', '5300914 ULTRA MILK TARO 200 ML/24', 'OWN', 'ULTRA MILK', 'ULTRA MILK TARO 200 ML', 'MILK', 'REGULER', 'SIZE 200 ML REGULER', '180 ml - 200 ml MILK', '200 ML', 'REGULER', false),
  ('5300465', 'UMCHOC125', '5300465 ULTRA MILK CHOCOLATE 125 ML/40', 'OWN', 'ULTRA MILK', 'ULTRA MILK CHOCOLATE 125 ML', 'MILK', 'REGULER', 'SIZE 125 ML REGULER', '105 ml - 125 ml MILK', '125 ML', 'REGULER', false),
  ('5300934', 'UMFC125', '5300934 ULTRA MILK FULL CREAM 125 ML/40', 'OWN', 'ULTRA MILK', 'ULTRA MILK FULL CREAM 125 ML', 'MILK', 'REGULER', 'SIZE 125 ML REGULER', '105 ml - 125 ml MILK', '125 ML', 'REGULER', false),
  ('5300466', 'UMSTRAW125', '5300466 ULTRA MILK STRAWBERRY 125 ML/40', 'OWN', 'ULTRA MILK', 'ULTRA MILK STRAWBERRY 125 ML', 'MILK', 'REGULER', 'SIZE 125 ML REGULER', '105 ml - 125 ml MILK', '125 ML', 'REGULER', false),
  ('5300602', 'MIMICHOC125', '5300602 MIMI CHOCOLATE 125 ML/40', 'OWN', 'ULTRA MIMI', 'ULTRA MIMI CHOCOLATE 125 ML', 'MILK', 'REGULER', 'SIZE 125 ML REGULER', '105 ml - 125 ml MILK', '125 ML', 'REGULER', false),
  ('5300884', 'MIMIFC125', '5300884 MIMI FULL CREAM 125 ML/40', 'OWN', 'ULTRA MIMI', 'ULTRA MIMI FULL CREAM 125 ML', 'MILK', 'REGULER', 'SIZE 125 ML REGULER', '105 ml - 125 ml MILK', '125 ML', 'REGULER', false),
  ('5300603', 'MIMISTRAW125', '5300603 MIMI STRAWBERRY 125 ML/40', 'OWN', 'ULTRA MIMI', 'ULTRA MIMI STRAWBERRY 125 ML', 'MILK', 'REGULER', 'SIZE 125 ML REGULER', '105 ml - 125 ml MILK', '125 ML', 'REGULER', false),
  ('5300877', 'MIMIVAN125', '5300877 MIMI VANILLA 125 ML/40', 'OWN', 'ULTRA MIMI', 'ULTRA MIMI VANILA 125 ML', 'MILK', 'REGULER', 'SIZE 125 ML REGULER', '105 ml - 125 ml MILK', '125 ML', 'REGULER', false),
  ('5300945', 'TK1L', '5300945 TEH KOTAK JASMINE CB8 1000 ML/12', 'OWN', 'TEH KOTAK', 'TEH KOTAK JASMINE 1000 ML', 'TEA DRINK', 'REGULER', 'SIZE 1 LITER REGULER', '750 ml - 1300 ml TEA DRINK', '1 LITER', 'REGULER', false),
  ('5300943', 'TK500', '5300943 TEH KOTAK JASMINE CB8 500 ML/12', 'OWN', 'TEH KOTAK', 'TEH KOTAK JASMINE 500 ML', 'TEA DRINK', 'REGULER', 'SIZE 300 ML REGULER', '200 ml - 500 ml TEA DRINK', '300 ML', 'REGULER', false),
  ('5300572', 'TK300', '5300572 TEH KOTAK JASMINE 300 ML/24', 'OWN', 'TEH KOTAK', 'TEH KOTAK JASMINE 300 ML', 'TEA DRINK', 'REGULER', 'SIZE 300 ML REGULER', '200 ml - 500 ml TEA DRINK', '300 ML', 'REGULER', false),
  ('TMP-TK200', 'TK200', 'TEH KOTAK JASMINE 200 ML', 'OWN', 'TEH KOTAK', 'TEH KOTAK JASMINE 200 ML', 'TEA DRINK', 'REGULER', 'SIZE 200 ML REGULER', '200 ml - 500 ml TEA DRINK', '200 ML', 'REGULER', true),
  ('5300944', 'TKLS750', '5300944 TEH KOTAK LESS SUGAR CB3 750 ML/12', 'OWN', 'TEH KOTAK', 'TEH KOTAK JASMINE LESS SUGAR 750 ML', 'TEA DRINK', 'REGULER', 'SIZE 750ML REGULER', '750 ml - 1300 ml TEA DRINK', '750 ML', 'REGULER', false),
  ('5300886', 'TKLS300', '5300886 TEH KOTAK JASMINE LESS SUGAR 300 ML/24', 'OWN', 'TEH KOTAK', 'TEH KOTAK JASMINE LESS SUGAR 300 ML', 'TEA DRINK', 'REGULER', 'SIZE 300 ML REGULER', '200 ml - 500 ml TEA DRINK', '300 ML', 'REGULER', false),
  ('5300949', 'TKMANGGA300', '5300949 TEH KOTAK RASA MANGO 300 ML/24', 'OWN', 'TEH KOTAK', 'Teh Kotak 300 Ml Rasa Mangga', 'TEA DRINK', 'REGULER', 'SIZE 300 ML REGULER', '200 ml - 500 ml TEA DRINK', '300 ML', 'REGULER', false),
  ('5300905', 'TKAPEL300', '5300905 TEH KOTAK RASA APPLE 300 ML/24', 'OWN', 'TEH KOTAK', 'TEH KOTAK RASA APPLE 300 ML', 'TEA DRINK', 'REGULER', 'SIZE 300 ML REGULER', '200 ml - 500 ml TEA DRINK', '300 ML', 'REGULER', false),
  ('5300904', 'TKBLACKCURRANT300', '5300904 TEH KOTAK RASA BLACKCURRANT 300 ML/24', 'OWN', 'TEH KOTAK', 'TEH KOTAK RASA BLACKCURRANT 300 ML', 'TEA DRINK', 'REGULER', 'SIZE 300 ML REGULER', '200 ml - 500 ml TEA DRINK', '300 ML', 'REGULER', false),
  ('5300950', 'TKLECI300', '5300950 TEH KOTAK RASA LYCHEE 300 ML/24', 'OWN', 'TEH KOTAK', 'Teh Kotak Rasa Leci 300 ml', 'TEA DRINK', 'REGULER', 'SIZE 300 ML REGULER', '200 ml - 500 ml TEA DRINK', '300 ML', 'REGULER', false),
  ('5300906', 'TKLEMON300', '5300906 TEH KOTAK RASA LEMON 300 ML/24', 'OWN', 'TEH KOTAK', 'TEH KOTAK RASA LEMON 300 ML', 'TEA DRINK', 'REGULER', 'SIZE 300 ML REGULER', '200 ml - 500 ml TEA DRINK', '300 ML', 'REGULER', false),
  ('5300821', 'USKI250', '5300821 SARI KACANG IJO 250 ML/24', 'OWN', 'SARI KACANG IJO', 'ULTRA SARI KACANG IJO 250 ML', 'JUICE (HEALTH DRINK)', 'REGULER', 'SIZE 250 ML REGULER', '250 ml JUICE (HEALTH DRINK)', '250 ML', 'REGULER', false),
  ('5300897', 'USKI150', '5300897 SARI KACANG IJO 150 ML/24', 'OWN', 'SARI KACANG IJO', 'ULTRA SARI KACANG IJO 150 ML', 'JUICE (HEALTH DRINK)', 'REGULER', 'SIZE 150 ML REGULER', '250 ml JUICE (HEALTH DRINK)', '150 ML', 'REGULER', false),
  ('5300819', 'USAA250', '5300819 SARI ASEM ASLI 250 ML/24', 'OWN', 'SARI ASEM ASLI', 'ULTRA SARI ASEM ASLI 250 ML', 'HEALTH JUICE (SAA)', 'REGULER', 'SIZE 250 ML REGULER', '250 ml HEALTH JUICE (SAA)', '250 ML', 'REGULER', false),
  ('TMP-YOASOBI-UMCHOC750', 'UMCHOC750', 'YOASOBI ULTRA MILK CHOCOLATE 750 ML', 'OWN', 'ULTRA MILK', 'YOASOBI ULTRA MILK CHOCOLATE 750 ML', 'MILK', 'REGULER', 'SIZE 750ML REGULER', '750 ml MILK', '750 ML', 'REGULER', true),
  ('TMP-YOASOBI-UMFC750', 'UMFC750', 'YOASOBI ULTRA MILK FULL CREAM 750 ML', 'OWN', 'ULTRA MILK', 'YOASOBI ULTRA MILK FULL CREAM 750 ML', 'MILK', 'REGULER', 'SIZE 750ML REGULER', '750 ml MILK', '750 ML', 'REGULER', true),
  ('TMP-YOASOBI-UMMOCCA750', 'UMMOCCA750', 'YOASOBI ULTRA MILK MOCCA 750 ML', 'OWN', 'ULTRA MILK', 'YOASOBI ULTRA MILK MOCCA 750 ML', 'MILK', 'REGULER', 'SIZE 750ML REGULER', '750 ml MILK', '750 ML', 'REGULER', true),
  ('TMP-YOASOBI-UMSTRAW750', 'UMSTRAW750', 'YOASOBI ULTRA MILK STRAWBERRY 750 ML', 'OWN', 'ULTRA MILK', 'YOASOBI ULTRA MILK STRAWBERRY 750 ML', 'MILK', 'REGULER', 'SIZE 750ML REGULER', '750 ml MILK', '750 ML', 'REGULER', true),
  ('5300900', null, 'SCM CREAMER CAP SAPI 375 GR', 'OWN', 'ULTRA MILK', 'SCM CREAMER CAP SAPI 375 GR', 'MILK', 'REGULER', 'SIZE 375ML REGULER', null, null, null, false),
  ('TMP-SCM-CAPSAPI-CHOC-375', null, 'SCM CAP SAPI CHOCOLATE 375 GR', 'OWN', 'ULTRA MILK', 'SCM CAP SAPI CHOCOLATE 375 GR', 'MILK', 'REGULER', 'SIZE 375ML REGULER', null, null, null, true)
on conflict (kode_sku) do update set
  short_sku = excluded.short_sku, produk = excluded.produk, own_comp = excluded.own_comp,
  brand = excluded.brand, sub_brand = excluded.sub_brand, category = excluded.category,
  sub_category = excluded.sub_category, size = excluded.size,
  grouping_size_new = excluded.grouping_size_new, actual_size = excluded.actual_size,
  display_category = excluded.display_category, updated_at = now();

-- 3) Hubungkan ke id_product berdasarkan NAMA (sub_brand = master_sku.product) ----------------
--    Jalankan ulang setiap ada SKU baru masuk di data stok.
update public.sku_principle p
   set id_product = m.id_product, updated_at = now()
  from public.master_sku m
 where p.id_product is null
   and upper(regexp_replace(btrim(p.sub_brand), '\s+', ' ', 'g'))
     = upper(regexp_replace(btrim(m.product),   '\s+', ' ', 'g'));

-- 4) Keamanan (sama dengan tabel lain: hanya service_role) --------------------------------------
alter table public.sku_principle enable row level security;
grant all on public.sku_principle to service_role;

-- 5) CEK HASIL -----------------------------------------------------------------------------
-- a) SKU principle yang belum terhubung ke data stok (wajar bila SKU memang belum pernah ada di stok)
-- select kode_sku, sub_brand from public.sku_principle where id_product is null order by 2;
-- b) SKU di data stok yang belum punya kode principle (harus kosong)
-- select m.id_product, m.product from public.master_sku m
--  left join public.sku_principle p on p.id_product = m.id_product where p.kode_sku is null;
-- c) Kode sementara yang masih harus diganti
-- select kode_sku, sub_brand from public.sku_principle where kode_sementara;
-- Contoh mengganti kode sementara (riwayat sell-in aman karena disimpan per id_product):
-- update public.sku_principle set kode_sku = '5300xxx', kode_sementara = false where kode_sku = 'TMP-UMBLUEBERRY200';
