# Stock Dashboard & Analysis (Streamlit + Supabase)

## Struktur
```
app.py                    entry point + navigasi + login
core/                     logika (tanpa HTML)
  config.py               threshold DSI, kolom wajib, status
  auth.py                 login (user dari st.secrets)
  database.py             semua akses Supabase (+ pagination)
  calculations.py         Total Keluar, SPD, DSI, Status PO
  validators.py           validasi file upload stok & sell-in
  exports.py              Excel berwarna + template sell-in
  service.py              loader ter-cache
  snapshot.py             baris stok dari input 'Stok Akhir'
  ppt_export.py           Export PPT Dashboard
pages_views/              5 halaman (dashboard, input_sellin, report, mtd, upload_stock)
ui/
  templates/*.html        markup HTML (Jinja2)
  static/style.css        CSS
  render.py, filters.py   jembatan ke Streamlit
sql/schema.sql            query Postgres/Supabase
.streamlit/               config.toml + secrets.toml.example
```

## Langkah mulai
1. Supabase → SQL Editor → jalankan `sql/schema.sql`.
2. Salin `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml`, isi URL, **service_role key**, dan user/password.
3. `pip install -r requirements.txt`
4. `streamlit run app.py`
5. Login admin → menu **Upload Stock** → upload CSV raw_oos.
6. Supabase → SQL Editor → jalankan `sql/sku_principle.sql` (master kode SKU principle → id_product). Cek 3 query di bagian bawah file itu.
7. Mulai input sell-in di menu **Input Sell-in**. Template sell-in memakai **nama toko** (`outlet`, dropdown/bisa diketik) dan `kode_sku` (kode principle); kolom `id_outlet` terisi otomatis dari nama toko, dan sistem menerjemahkan `kode_sku` ke `id_product` saat upload. Bila ada nama toko kembar, isi `id_outlet` manual.
8. Di tampilan mobile, menu pindah halaman tersedia sebagai dropdown di bawah header.

## Rumus
- Total Keluar (per interval dua snapshot stok) = Stok sebelumnya + Sell-in − Stok berikutnya (min 0)
- SPD = Total Keluar / 12 hari (bisa diubah di filter)
- DSI = Stok Akhir / SPD (stok 0 → 0; ada stok tapi SPD 0 → 999)
- Status: HARI HARI <20 Hijau, 20–<50 Kuning, ≥50 Merah · TIP TOP & NAGA <14 Hijau, 14–<21 Kuning, ≥21 Merah
