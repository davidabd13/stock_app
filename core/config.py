"""Konfigurasi & aturan bisnis. Ubah angka threshold di sini, tidak perlu menyentuh logika lain."""

APP_TITLE = "Stock Dashboard & Analysis"
HARI_BERJALAN_DEFAULT = 12     # pembagi SPD
DSI_CAP = 999                  # DSI untuk barang ada stok tapi tidak bergerak (SPD = 0)

# 22 kolom wajib file Upload Stock (urutan sama dengan CSV raw_oos)
REQUIRED_COLUMNS = [
    "week", "periode", "date", "user", "jabatan", "area", "area_fix",
    "dc_mm", "channel", "account", "id_outlet", "outlet", "ket_prioritas",
    "id_product", "product", "stock_pajang", "stock_gudang", "total_stock",
    "stock_kosong", "index_oos", "oos_reason", "skam",
]
INT_COLUMNS = ["periode", "id_product", "stock_pajang", "stock_gudang", "total_stock", "index_oos"]
TEXT_COLUMNS = [c for c in REQUIRED_COLUMNS if c not in INT_COLUMNS + ["date"]]

MASTER_OUTLET_COLUMNS = ["id_outlet", "outlet", "account", "channel", "area", "area_fix",
                         "ket_prioritas", "user", "jabatan", "skam"]

SELLIN_COLUMNS = ["date", "id_outlet", "id_product", "qty", "notes"]

# ---- Status PO ------------------------------------------------------------
STATUS_HIJAU = "Hijau - Push PO"
STATUS_KUNING = "Kuning - Normal"
STATUS_MERAH = "Merah - Manage PO"
STATUS_COLORS = {STATUS_HIJAU: "#10B981", STATUS_KUNING: "#F59E0B", STATUS_MERAH: "#EF4444"}

# (batas_hijau, batas_merah):  DSI < hijau -> Hijau | hijau <= DSI < merah -> Kuning | DSI >= merah -> Merah
# Dibuat tanpa celah (mis. DSI 20,5) supaya semua nilai desimal tetap terklasifikasi.
DSI_RULES = {
    "HARI HARI": (20, 50),
    "TIP TOP": (14, 21),
    "NAGA": (14, 21),
}
DEFAULT_RULE = (14, 21)   # account di luar daftar di atas
