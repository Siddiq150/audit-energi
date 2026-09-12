# ============================================================
# APLIKASI AUDIT ENERGI LISTRIK RUMAH TANGGA
# File: aplikasi_audit_energi.py
# ============================================================
import streamlit as st
import pandas as pd

# ---------- KONFIGURASI HALAMAN ----------
st.set_page_config(
    page_title="Audit Energi Listrik Rumah Tangga",
    page_icon="⚡",
    layout="wide"
)

# ---------- KONSTANTA ----------
TEGANGAN = 220
FAKTOR_AMAN = 0.8
MAKS_ALAT = 50
TARIF_PER_KWH = 1444.70


# ============================================================
# FORMATTER
# ============================================================
def format_rupiah(angka):
    return "Rp " + f"{int(round(angka)):,}".replace(",", ".")


def format_kwh(angka):
    return f"{angka:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " kWh"


def format_watt(angka):
    return f"{angka:,.0f}".replace(",", ".") + " Watt"


# ============================================================
# SESSION STATE INIT
# ============================================================
if "data_alat" not in st.session_state:
    st.session_state.data_alat = []


# ============================================================
# HEADER
# ============================================================
st.title("⚡ Kalkulator Audit Energi Listrik Rumah Tangga")
st.caption("Hitung konsumsi energi & biaya listrik rumah tangga, sekaligus cek kapasitas Ampere rumah.")
st.divider()


# ============================================================
# SIDEBAR — KAPASITAS
# ============================================================
with st.sidebar:
    st.header("🏠 Data Rumah")

    kapasitas_ampere = st.number_input(
        "Kapasitas Rumah (Ampere)",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=0.5,
        format="%.2f",
        key="input_kapasitas_ampere",
        help="Contoh: 6 A, 10 A, 20 A"
    )

    st.info(f"**Tarif listrik (otomatis)**\n\n{format_rupiah(TARIF_PER_KWH)} / kWh")
    st.caption(f"Tegangan: {TEGANGAN} V · Faktor aman: {int(FAKTOR_AMAN*100)}%")

    st.divider()

    if kapasitas_ampere > 0:
        kapasitas_max = kapasitas_ampere * TEGANGAN
        batas_aman = kapasitas_max * FAKTOR_AMAN
        st.metric("Kapasitas Max", format_watt(kapasitas_max))
        st.metric("Batas Aman (80%)", format_watt(batas_aman))

    st.divider()

    if st.button("🗑️ Reset Semua Data", use_container_width=True):
        st.session_state.data_alat = []
        if "input_kapasitas_ampere" in st.session_state:
            del st.session_state["input_kapasitas_ampere"]
        st.success("Semua data berhasil direset!")
        st.rerun()


# ============================================================
# FORM TAMBAH ALAT
# ============================================================
st.subheader("➕ Tambah Alat Listrik")

if len(st.session_state.data_alat) >= MAKS_ALAT:
    st.warning(f"⚠️ Maksimal {MAKS_ALAT} alat sudah tercapai.")
else:
    with st.form("form_tambah_alat", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns([3, 1, 2, 2])
        with col1:
            nama = st.text_input("Nama Alat", placeholder="contoh: AC, Lampu, Kulkas")
        with col2:
            unit = st.number_input("Jumlah Unit", min_value=1, value=1, step=1)
        with col3:
            daya = st.number_input("Daya per Unit (Watt)", min_value=0.0, value=0.0, step=10.0)
        with col4:
            jam = st.number_input("Lama Pemakaian (jam/hari)", min_value=0.0, value=0.0, step=0.5)

        submitted = st.form_submit_button("Tambah Alat", use_container_width=True)

        if submitted:
            error = False
            if not nama.strip():
                st.error("❌ Nama alat tidak boleh kosong.")
                error = True
            if daya <= 0:
                st.error("❌ Daya harus lebih dari 0 Watt.")
                error = True
            if jam <= 0:
                st.error("❌ Lama pemakaian harus lebih dari 0 jam.")
                error = True

            if not error:
                energi_harian = (daya * unit * jam) / 1000
                st.session_state.data_alat.append({
                    "nama": nama.strip(),
                    "unit": int(unit),
                    "daya": float(daya),
                    "jam": float(jam),
                    "energi_harian": energi_harian,
                })
                st.success(f"✅ Alat '{nama}' ditambahkan. Energi harian: {format_kwh(energi_harian)}")
                st.rerun()


# ============================================================
# TABEL DATA ALAT
# ============================================================
if st.session_state.data_alat:
    st.divider()
    st.subheader(f"📋 Daftar Alat ({len(st.session_state.data_alat)}/{MAKS_ALAT})")
    st.caption("🔽 Diurutkan berdasarkan: Nama Alat → Jam/hari → Biaya Tahunan")

    # ---------- Bangun rows ----------
    rows = []
    for alat in st.session_state.data_alat:
        e_harian = alat["energi_harian"]
        e_bulanan = e_harian * 30
        e_tahunan = e_harian * 365
        biaya_harian = e_harian * TARIF_PER_KWH
        biaya_bulanan = e_bulanan * TARIF_PER_KWH
        biaya_tahunan = e_tahunan * TARIF_PER_KWH
        daya_total = alat["daya"] * alat["unit"]

        rows.append({
            "Nama Alat": alat["nama"],
            "Unit": alat["unit"],
            "Daya (W/unit)": alat["daya"],
            "Jam/hari": alat["jam"],
            "Daya Total (W)": daya_total,
            "Energi Harian (kWh)": round(e_harian, 2),
            "Energi Bulanan (kWh)": round(e_bulanan, 2),
            "Energi Tahunan (kWh)": round(e_tahunan, 2),
            "Biaya Harian (Rp)": int(round(biaya_harian)),
            "Biaya Bulanan (Rp)": int(round(biaya_bulanan)),
            "Biaya Tahunan (Rp)": int(round(biaya_tahunan)),
        })

    df = pd.DataFrame(rows)

    # ---------- SORTIR 3 TINGKAT ----------
    # 1. Nama Alat (A → Z)
    # 2. Jam/hari (besar → kecil)
    # 3. Biaya Tahunan (besar → kecil)
    df_sorted = df.sort_values(
        by=["Nama Alat", "Jam/hari", "Biaya Tahunan (Rp)"],
        ascending=[True, False, False],
        kind="mergesort"
    ).reset_index(drop=True)

    # ---------- INSERT "No" SETELAH SORTIR ----------
    df_sorted.insert(0, "No", range(1, len(df_sorted) + 1))

    # ---------- TAMPILKAN ----------
    st.dataframe(
        df_sorted.style.format({
            "Daya (W/unit)": "{:,.0f}",
            "Jam/hari": "{:g}",
            "Daya Total (W)": "{:,.0f}",
            "Energi Harian (kWh)": "{:,.2f}",
            "Energi Bulanan (kWh)": "{:,.2f}",
            "Energi Tahunan (kWh)": "{:,.2f}",
            "Biaya Harian (Rp)": "Rp {:,.0f}",
            "Biaya Bulanan (Rp)": "Rp {:,.0f}",
            "Biaya Tahunan (Rp)": "Rp {:,.0f}",
        }),
        use_container_width=True,
        hide_index=True
    )

    # ---------- HAPUS ALAT ----------
    with st.expander("🗑️ Hapus Alat"):
        st.caption("ℹ️ Daftar di bawah mengikuti urutan asli input.")
        nama_list = [f"{i}. {a['nama']} ({a['jam']} jam)" for i, a in enumerate(st.session_state.data_alat, 1)]
        pilihan = st.selectbox("Pilih alat yang ingin dihapus:", ["— pilih —"] + nama_list, key="pilih_hapus")
        if st.button("Hapus", key="btn_hapus"):
            if pilihan != "— pilih —":
                idx = int(pilihan.split(".")[0]) - 1
                removed = st.session_state.data_alat.pop(idx)
                st.success(f"✅ '{removed['nama']}' berhasil dihapus.")
                st.rerun()
            else:
                st.warning("Pilih alat terlebih dahulu.")

    st.divider()

    # ============================================================
    # RINGKASAN TOTAL
    # ============================================================
    st.subheader("📊 Total Keseluruhan")

    total_energi_bulanan = sum(r["Energi Bulanan (kWh)"] for r in rows)
    total_energi_tahunan = sum(r["Energi Tahunan (kWh)"] for r in rows)
    total_biaya_bulanan = sum(r["Biaya Bulanan (Rp)"] for r in rows)
    total_biaya_tahunan = sum(r["Biaya Tahunan (Rp)"] for r in rows)
    total_daya = sum(r["Daya Total (W)"] for r in rows)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Daya Terpakai", format_watt(total_daya))
    c2.metric("Total Energi Bulanan", format_kwh(total_energi_bulanan))
    c3.metric("Total Energi Tahunan", format_kwh(total_energi_tahunan))

    c4, c5 = st.columns(2)
    c4.metric("💰 Biaya Bulanan", format_rupiah(total_biaya_bulanan))
    c5.metric("💰 Biaya Tahunan", format_rupiah(total_biaya_tahunan))

    st.divider()

    # ============================================================
    # CEK KAPASITAS AMPERE
    # ============================================================
    st.subheader("⚡ Cek Kapasitas Rumah")

    if kapasitas_ampere > 0:
        kapasitas_max = kapasitas_ampere * TEGANGAN
        batas_aman = kapasitas_max * FAKTOR_AMAN

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Kapasitas Rumah", f"{kapasitas_ampere:g} A")
        col_b.metric("Kapasitas Max", format_watt(kapasitas_max))
        col_c.metric("Batas Aman (80%)", format_watt(batas_aman))

        persen = min(total_daya / batas_aman, 1.0) if batas_aman > 0 else 0
        st.progress(persen)

        if total_daya <= batas_aman:
            st.success(f"✅ **AMAN** — Total daya terpakai {format_watt(total_daya)} masih dalam batas aman {format_watt(batas_aman)}.")
        else:
            kelebihan = total_daya - batas_aman
            st.error(
                f"❌ **KAPASITAS AMPERE RUMAH TIDAK CUKUP**\n\n"
                f"Total daya terpakai: {format_watt(total_daya)}\n\n"
                f"Batas aman: {format_watt(batas_aman)}\n\n"
                f"Kelebihan: {format_watt(kelebihan)}\n\n"
                f"💡 Saran: Naikkan kapasitas MCB rumah atau kurangi pemakaian alat."
            )
    else:
        st.warning("⚠️ Isi **Kapasitas Rumah (Ampere)** di sidebar untuk mengecek status keamanan.")

    st.divider()

    # ============================================================
    # EXPORT CSV
    # ============================================================
    st.subheader("📥 Export Data")
    st.caption("File CSV mengikuti urutan sortir yang sedang aktif.")

    csv = df_sorted.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")

    st.download_button(
        label="⬇️ Download CSV (Excel-friendly)",
        data=csv,
        file_name="audit_energi_listrik.csv",
        mime="text/csv",
        use_container_width=True
    )

else:
    st.info("📭 Belum ada alat. Silakan tambahkan alat melalui form di atas.")