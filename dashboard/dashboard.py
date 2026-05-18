import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinanceTrack",
    page_icon="💸",
    layout="wide",
)

# ── CUSTOM CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.stApp { background-color: #0f1117; color: #e8eaf0; }

[data-testid="stSidebar"] {
    background-color: #161b27;
    border-right: 1px solid #1e2535;
}
[data-testid="stSidebar"] * { color: #c9cdd8 !important; }

[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1a2030 0%, #1e2840 100%);
    border: 1px solid #2a3550;
    border-radius: 16px;
    padding: 20px 24px;
}
[data-testid="stMetricLabel"]  { color: #8b92a5 !important; font-size: 12px !important; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; }
[data-testid="stMetricValue"]  { color: #e8eaf0 !important; font-size: 26px !important; font-weight: 800; }
[data-testid="stMetricDelta"]  { font-size: 12px !important; font-weight: 600; }

.chart-card {
    background: #161b27;
    border: 1px solid #1e2535;
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 16px;
}
.chart-title    { font-size: 15px; font-weight: 700; color: #e8eaf0; margin-bottom: 2px; }
.chart-subtitle { font-size: 12px; color: #5b6880; margin-bottom: 14px; }
.insight-box {
    background: rgba(110,231,183,0.05);
    border-left: 3px solid #6ee7b7;
    border-radius: 0 12px 12px 0;
    padding: 12px 16px;
    margin-top: 10px;
    font-size: 13px;
    color: #a0aec0;
    line-height: 1.7;
}
.badge-spike {
    display: inline-block;
    background: rgba(251,113,133,0.15);
    color: #fb7185;
    border: 1px solid rgba(251,113,133,0.3);
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 12px;
    font-weight: 600;
    margin: 3px;
}
hr { border-color: #1e2535; }
</style>
""", unsafe_allow_html=True)

# ── PALETTE ───────────────────────────────────────────────────────────────────
ACCENT     = "#6ee7b7"
ACCENT2    = "#818cf8"
ACCENT3    = "#fb7185"
CHART_BG   = "#161b27"
GRID_COLOR = "#1e2535"

CATEGORY_COLORS = {
    "Makanan & Minuman"   : "#6ee7b7",
    "Transportasi"        : "#818cf8",
    "Hiburan"             : "#fb7185",
    "Belanja"             : "#fbbf24",
    "Pendidikan"          : "#38bdf8",
    "Tagihan"             : "#a78bfa",
    "Tabungan & Investasi": "#34d399",
    "Hadiah & Amal"       : "#f472b6",
}

BASE_LAYOUT = dict(
    paper_bgcolor=CHART_BG,
    plot_bgcolor=CHART_BG,
    font=dict(family="Plus Jakarta Sans", color="#8b92a5", size=12),
    margin=dict(l=0, r=0, t=10, b=0),
)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def fmt_rp(val):
    if val >= 1_000_000_000:
        return f"Rp {val/1_000_000_000:.1f} M"
    elif val >= 1_000_000:
        return f"Rp {val/1_000_000:.1f} Jt"
    elif val >= 1_000:
        return f"Rp {val/1_000:.0f} Rb"
    return f"Rp {val:,.0f}"

def card(title, subtitle=""):
    st.markdown(
        f'<div class="chart-card">'
        f'<p class="chart-title">{title}</p>'
        f'<p class="chart-subtitle">{subtitle}</p>',
        unsafe_allow_html=True,
    )

def card_end():
    st.markdown('</div>', unsafe_allow_html=True)

def insight(text):
    st.markdown(f'<div class="insight-box">💡 {text}</div>', unsafe_allow_html=True)


# ── LOAD & PREPARE DATA ───────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("dashboard/main_data.csv")
    df["tanggal"] = pd.to_datetime(
        df["tanggal"],
        format="mixed",
        errors="coerce"
        )

    # ── Filter user "Tidak Diketahui" sesuai notebook ──────────────────────
    # Data sintetis: user yang tidak diketahui identitasnya digunakan
    # sebagai representasi pengguna individu di dashboard ini.
    df = df[df["user_id"] == "Tidak Diketahui"].copy()

    # ── Scaling nominal agar realistis (scaling_factor = 0.03) ─────────────
    # Identik dengan logika notebook: nominal diturunkan ke skala individu
    scaling_factor = 0.03
    df["harga_produk"] = (df["harga_produk"] * scaling_factor).astype(int)
    df["biaya_admin"]  = (df["biaya_admin"]  * scaling_factor).astype(int)
    df["cashback"]     = (df["cashback"]     * scaling_factor).astype(int)

    # ── Clip per kategori sesuai batas wajar ────────────────────────────────
    batas_kategori = {
        "Makanan & Minuman"   : 200_000,
        "Transportasi"        : 100_000,
        "Belanja"             : 1_000_000,
        "Hiburan"             : 300_000,
        "Tagihan"             : 1_500_000,
        "Pendidikan"          : 2_000_000,
        "Tabungan & Investasi": 3_000_000,
    }
    for kat, batas in batas_kategori.items():
        mask = df["kategori"] == kat
        df.loc[mask, "harga_produk"] = np.clip(
            df.loc[mask, "harga_produk"], 1_000, batas
        )

    # ── Filter hanya transaksi Berhasil ─────────────────────────────────────
    df = df[df["status_transaksi"] == "Berhasil"].copy()

    return df


df = load_data()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💸 FinanceTrack")
    st.caption("Digital Wallet · Personal Dashboard")
    st.markdown("---")

    page = st.radio(
        "Navigasi",
        [
            "🏠  Ringkasan Bulanan",
            "📊  Breakdown Kategori",
            "📈  Tren Harian",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("**Filter Kategori**")
    kat_opts = ["Semua"] + sorted(df["kategori"].unique().tolist())
    sel_kat  = st.selectbox("Kategori", kat_opts, label_visibility="collapsed")
    st.markdown("---")
    st.caption("© 2026 FinanceTrack")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 1 — RINGKASAN BULANAN  (Pertanyaan 1)
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠  Ringkasan Bulanan":

    st.markdown("# 🏠 Ringkasan Bulanan")
    st.markdown(
        "**Pertanyaan 1:** Berapa total pengeluaran Mei vs April 2026, "
        "dan kategori apa yang mengalami kenaikan persentase tertinggi?"
    )
    st.markdown("---")

    # Data Q1 — identik dengan notebook: filter tahun 2026, April & Mei
    bulan_compare = df[
        (df["tahun"] == 2026) &
        (df["bulan"].isin(["April", "Mei"]))
    ]

    total_bulanan = bulan_compare.groupby("bulan").agg(
        total_pengeluaran=("harga_produk", "sum"),
        jumlah_transaksi=("harga_produk", "count"),
        rata_rata=("harga_produk", "mean"),
    ).reset_index()

    total_mei   = total_bulanan.loc[total_bulanan["bulan"] == "Mei",   "total_pengeluaran"].values[0]
    total_april = total_bulanan.loc[total_bulanan["bulan"] == "April", "total_pengeluaran"].values[0]
    selisih     = total_mei - total_april
    pct_change  = (selisih / total_april) * 100 if total_april else 0
    trx_mei     = total_bulanan.loc[total_bulanan["bulan"] == "Mei",   "jumlah_transaksi"].values[0]
    avg_mei     = total_bulanan.loc[total_bulanan["bulan"] == "Mei",   "rata_rata"].values[0]

    # KPI Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Pengeluaran Mei",   fmt_rp(total_mei))
    c2.metric("Total Pengeluaran April", fmt_rp(total_april))
    c3.metric(
        "Selisih MoM",
        fmt_rp(abs(selisih)),
        delta=f"{'↑' if selisih > 0 else '↓'} {abs(pct_change):.1f}% vs April",
        delta_color="inverse",
    )
    c4.metric("Transaksi Mei", f"{int(trx_mei):,} trx")

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 2])

    # Bar chart total bulanan — identik visualisasi notebook (sns.barplot)
    with col_l:
        card(
            "Total Pengeluaran April vs Mei 2026",
            "Transaksi Berhasil · User Tidak Diketahui · Tahun 2026",
        )
        fig_total = go.Figure(go.Bar(
            x=["April", "Mei"],
            y=[total_april, total_mei],
            marker_color=[ACCENT2, ACCENT],
            text=[fmt_rp(total_april), fmt_rp(total_mei)],
            textposition="outside",
            textfont=dict(color="#e8eaf0", size=12),
            width=0.45,
        ))
        fig_total.update_layout(
            **BASE_LAYOUT,
            height=300,
            xaxis=dict(gridcolor=GRID_COLOR, showline=False),
            yaxis=dict(tickformat=".2s", gridcolor=GRID_COLOR, showline=False),
        )
        st.plotly_chart(fig_total, use_container_width=True)

        lbl = "naik" if selisih > 0 else "turun"
        insight(
            f"Pengeluaran Mei <b>{lbl} {abs(pct_change):.1f}%</b> dibanding April. "
            f"Rata-rata transaksi Mei: <b>{fmt_rp(avg_mei)}</b>."
        )
        card_end()

    # Pivot kenaikan per kategori — identik dengan notebook (pivot_table + persentase_kenaikan)
    with col_r:
        card(
            "Persentase Kenaikan Pengeluaran per Kategori",
            "Perbandingan total nominal April → Mei 2026",
        )
        kategori_growth = bulan_compare.pivot_table(
            index="kategori",
            columns="bulan",
            values="harga_produk",
            aggfunc="sum",
            fill_value=0,
        )
        kategori_growth = kategori_growth.reindex(
            columns=["April", "Mei"], fill_value=0
        )
        kategori_growth["persentase_kenaikan"] = (
            (kategori_growth["Mei"] - kategori_growth["April"])
            / kategori_growth["April"].replace(0, np.nan)
        ) * 100
        kategori_growth = kategori_growth.sort_values(
            "persentase_kenaikan", ascending=True
        )

        clr = [ACCENT3 if v > 0 else ACCENT for v in kategori_growth["persentase_kenaikan"]]
        fig_growth = go.Figure(go.Bar(
            x=kategori_growth["persentase_kenaikan"],
            y=kategori_growth.index,
            orientation="h",
            marker_color=clr,
            text=[f"{v:+.1f}%" for v in kategori_growth["persentase_kenaikan"]],
            textposition="outside",
            textfont=dict(color="#e8eaf0", size=11),
        ))
        fig_growth.update_layout(
            **BASE_LAYOUT,
            height=300,
            xaxis=dict(
                ticksuffix="%", gridcolor=GRID_COLOR, showline=False,
                zeroline=True, zerolinecolor=GRID_COLOR,
            ),
            yaxis=dict(gridcolor=GRID_COLOR, showline=False),
        )
        st.plotly_chart(fig_growth, use_container_width=True)

        top_naik  = kategori_growth.sort_values("persentase_kenaikan", ascending=False).iloc[0]
        top_turun = kategori_growth.iloc[0]
        insight(
            f"Kenaikan tertinggi: <b>{top_naik.name}</b> ({top_naik['persentase_kenaikan']:+.1f}%). "
            f"Penurunan terbesar: <b>{top_turun.name}</b> ({top_turun['persentase_kenaikan']:+.1f}%)."
        )
        card_end()

    # Tabel ringkasan bulanan
    st.markdown("### 📋 Ringkasan per Bulan")
    tbl = total_bulanan.copy()
    tbl.columns = ["Bulan", "Total Pengeluaran (Rp)", "Jumlah Transaksi", "Rata-rata Transaksi (Rp)"]
    tbl["Total Pengeluaran (Rp)"]   = tbl["Total Pengeluaran (Rp)"].apply(lambda x: f"Rp {x:,.0f}")
    tbl["Rata-rata Transaksi (Rp)"] = tbl["Rata-rata Transaksi (Rp)"].apply(lambda x: f"Rp {x:,.0f}")
    tbl = tbl.reset_index(drop=True)
    tbl.index += 1
    st.dataframe(tbl, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 2 — BREAKDOWN KATEGORI  (Pertanyaan 2)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊  Breakdown Kategori":

    st.markdown("# 📊 Breakdown Kategori")
    st.markdown(
        "**Pertanyaan 2:** Persentase pengeluaran tiap kategori Mei 2026 — "
        "kategori dengan frekuensi tertinggi dan nominal terbesar"
    )
    st.markdown("---")

    # Data Q2 — identik notebook: filter tahun 2026 & bulan Mei
    mei_df = df[(df["tahun"] == 2026) & (df["bulan"] == "Mei")]

    if sel_kat != "Semua":
        mei_df = mei_df[mei_df["kategori"] == sel_kat]

    # groupby kategori — identik notebook
    kategori_mei = mei_df.groupby("kategori").agg(
        total_pengeluaran=("harga_produk", "sum"),
        frekuensi=("harga_produk", "count"),
        rata_rata=("harga_produk", "mean"),
    )
    total_mei = kategori_mei["total_pengeluaran"].sum()
    kategori_mei["persentase"] = (
        kategori_mei["total_pengeluaran"] / total_mei
    ) * 100
    kategori_mei = kategori_mei.sort_values("total_pengeluaran", ascending=False)

    # KPI
    top_nom = kategori_mei.iloc[0]
    top_frk = kategori_mei.sort_values("frekuensi", ascending=False).iloc[0]
    bot_nom = kategori_mei.iloc[-1]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Pengeluaran Mei", fmt_rp(total_mei))
    c2.metric("Nominal Terbesar",      top_nom.name,
              delta=f"{top_nom['persentase']:.1f}% dari total")
    c3.metric("Frekuensi Tertinggi",   top_frk.name,
              delta=f"{int(top_frk['frekuensi'])} transaksi")
    c4.metric("Nominal Terkecil",      bot_nom.name,
              delta=f"{bot_nom['persentase']:.1f}% dari total")

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns([2, 3])

    # Pie Chart — identik notebook (plt.pie)
    with col_l:
        card(
            "Distribusi Pengeluaran per Kategori",
            "Mei 2026 · Persentase dari total pengeluaran",
        )
        fig_pie = go.Figure(go.Pie(
            labels=kategori_mei.index,
            values=kategori_mei["total_pengeluaran"],
            hole=0.40,
            marker=dict(
                colors=[CATEGORY_COLORS.get(k, "#888") for k in kategori_mei.index],
                line=dict(color=CHART_BG, width=2),
            ),
            textinfo="label+percent",
            textfont=dict(size=11, color="#e8eaf0"),
            hovertemplate="<b>%{label}</b><br>%{percent}<br>Rp %{value:,.0f}<extra></extra>",
        ))
        fig_pie.update_layout(
            **BASE_LAYOUT,
            height=360,
            showlegend=False,
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        insight(
            f"<b>{top_nom.name}</b> mendominasi pengeluaran Mei "
            f"dengan porsi <b>{top_nom['persentase']:.1f}%</b>. "
            f"Kategori dengan nominal besar belum tentu paling sering digunakan."
        )
        card_end()

    # Bar frekuensi + line nominal (dual axis) — dari frekuensi_tertinggi notebook
    with col_r:
        card(
            "Frekuensi & Total Nominal per Kategori",
            "Urut dari frekuensi tertinggi · dual-axis",
        )
        frek_sort = kategori_mei.sort_values("frekuensi", ascending=False)
        fig_frek = go.Figure()
        fig_frek.add_trace(go.Bar(
            name="Frekuensi Transaksi",
            x=frek_sort.index,
            y=frek_sort["frekuensi"],
            marker_color=[CATEGORY_COLORS.get(k, "#888") for k in frek_sort.index],
            yaxis="y1",
            text=frek_sort["frekuensi"].astype(int),
            textposition="outside",
            textfont=dict(size=11, color="#8b92a5"),
        ))
        fig_frek.add_trace(go.Scatter(
            name="Total Nominal (Rp)",
            x=frek_sort.index,
            y=frek_sort["total_pengeluaran"],
            mode="lines+markers",
            marker=dict(size=9, color=ACCENT3),
            line=dict(color=ACCENT3, width=2.5, dash="dot"),
            yaxis="y2",
            hovertemplate="%{x}<br>Rp %{y:,.0f}<extra></extra>",
        ))
        fig_frek.update_layout(
            **BASE_LAYOUT,
            height=360,
            yaxis=dict(title="Frekuensi", gridcolor=GRID_COLOR, showline=False),
            yaxis2=dict(
                title="Total (Rp)", overlaying="y", side="right",
                tickformat=".2s", gridcolor="rgba(0,0,0,0)", showline=False,
            ),
            xaxis=dict(gridcolor=GRID_COLOR, tickangle=-15),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig_frek, use_container_width=True)
        insight(
            f"<b>{top_frk.name}</b> paling sering digunakan "
            f"({int(top_frk['frekuensi'])} transaksi). "
            f"Kategori dengan nominal besar dan frekuensi tinggi menjadi "
            f"layanan utama pengguna digital wallet ini."
        )
        card_end()

    # Tabel ranking — identik output display(kategori_mei) di notebook
    st.markdown("### 📋 Tabel Ranking Kategori Mei 2026")
    tbl2 = kategori_mei[["total_pengeluaran", "frekuensi", "rata_rata", "persentase"]].copy()
    tbl2.columns = ["Total Pengeluaran (Rp)", "Frekuensi Transaksi", "Rata-rata (Rp)", "Persentase (%)"]
    tbl2["Total Pengeluaran (Rp)"] = tbl2["Total Pengeluaran (Rp)"].apply(lambda x: f"Rp {x:,.0f}")
    tbl2["Rata-rata (Rp)"]         = tbl2["Rata-rata (Rp)"].apply(lambda x: f"Rp {x:,.0f}")
    tbl2["Persentase (%)"]         = tbl2["Persentase (%)"].apply(lambda x: f"{x:.1f}%")
    tbl2["Frekuensi Transaksi"]    = tbl2["Frekuensi Transaksi"].astype(int)
    tbl2 = tbl2.reset_index()
    tbl2.index += 1
    st.dataframe(tbl2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 3 — TREN HARIAN  (Pertanyaan 3)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈  Tren Harian":

    st.markdown("# 📈 Tren Pengeluaran Harian")
    st.markdown(
        "**Pertanyaan 3:** Tren pengeluaran 30 hari terakhir "
        "dan deteksi hari dengan lonjakan pengeluaran"
    )
    st.markdown("---")

    # Data Q3 — identik notebook
    tanggal_akhir = df["tanggal"].max()
    tanggal_awal  = tanggal_akhir - pd.Timedelta(days=30)
    last30        = df[df["tanggal"] >= tanggal_awal]

    harian = last30.groupby(last30["tanggal"].dt.date).agg(
        total_pengeluaran=("harga_produk", "sum"),
        jumlah_transaksi=("harga_produk", "count"),
    ).reset_index()
    harian.columns = ["tanggal", "total_pengeluaran", "jumlah_transaksi"]
    harian["tanggal"] = pd.to_datetime(harian["tanggal"])

    # Threshold = mean + std — identik notebook
    mean_val  = harian["total_pengeluaran"].mean()
    std_val   = harian["total_pengeluaran"].std()
    threshold = mean_val + std_val

    harian["lonjakan"] = harian["total_pengeluaran"] > threshold
    harian["warna"]    = harian["lonjakan"].map({True: ACCENT3, False: ACCENT})
    spike_df  = harian[harian["lonjakan"]]
    max_day   = harian.loc[harian["total_pengeluaran"].idxmax()]
    min_day   = harian.loc[harian["total_pengeluaran"].idxmin()]

    # KPI
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rata-rata Harian",      fmt_rp(mean_val))
    c2.metric("Threshold Lonjakan",    fmt_rp(threshold),
              delta=f"mean + std ({fmt_rp(std_val)})")
    c3.metric("Pengeluaran Tertinggi", fmt_rp(max_day["total_pengeluaran"]),
              delta=max_day["tanggal"].strftime("%d %b %Y"))
    c4.metric("Hari Lonjakan",         f"{int(spike_df.shape[0])} hari")

    st.markdown("<br>", unsafe_allow_html=True)

    # Area + line chart — dari plt.plot notebook
    card(
        "Tren Total Pengeluaran 30 Hari Terakhir",
        f"Periode {tanggal_awal.strftime('%d %b')} – {tanggal_akhir.strftime('%d %b %Y')} "
        f"· Threshold = mean + std ({fmt_rp(threshold)})",
    )

    fig_line = go.Figure()

    # Area fill
    fig_line.add_trace(go.Scatter(
        x=harian["tanggal"],
        y=harian["total_pengeluaran"],
        fill="tozeroy",
        fillcolor="rgba(110,231,183,0.06)",
        line=dict(color=ACCENT, width=2.5),
        mode="lines+markers",
        marker=dict(size=5, color=ACCENT),
        name="Pengeluaran Harian",
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Rp %{y:,.0f}<extra></extra>",
    ))

    # Titik lonjakan
    if not spike_df.empty:
        fig_line.add_trace(go.Scatter(
            x=spike_df["tanggal"],
            y=spike_df["total_pengeluaran"],
            mode="markers",
            marker=dict(
                size=13, color=ACCENT3, symbol="diamond",
                line=dict(color="#fff", width=1.5),
            ),
            name="Lonjakan",
            hovertemplate="<b>⚠ LONJAKAN %{x|%d %b}</b><br>Rp %{y:,.0f}<extra></extra>",
        ))

    # Garis threshold
    fig_line.add_hline(
        y=threshold,
        line_dash="dash", line_color=ACCENT3, line_width=1.5,
        annotation_text=f"Threshold: {fmt_rp(threshold)}",
        annotation_font_color=ACCENT3,
        annotation_position="top left",
    )

    # Garis mean
    fig_line.add_hline(
        y=mean_val,
        line_dash="dot", line_color="#8b92a5", line_width=1,
        annotation_text=f"Rata-rata: {fmt_rp(mean_val)}",
        annotation_font_color="#8b92a5",
        annotation_position="bottom left",
    )

    fig_line.update_layout(
        **BASE_LAYOUT,
        height=380,
        xaxis=dict(gridcolor=GRID_COLOR, showline=False, tickformat="%d %b"),
        yaxis=dict(tickformat=".2s", gridcolor=GRID_COLOR, showline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, bgcolor="rgba(0,0,0,0)"),
        hovermode="x unified",
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # Badge hari lonjakan
    if not spike_df.empty:
        badges = " ".join([
            f'<span class="badge-spike">⚠ {r["tanggal"].strftime("%d %b")} · {fmt_rp(r["total_pengeluaran"])}</span>'
            for _, r in spike_df.iterrows()
        ])
        st.markdown(badges, unsafe_allow_html=True)

    insight(
        f"Lonjakan terdeteksi pada <b>{int(spike_df.shape[0])} hari</b> "
        f"di mana pengeluaran melebihi threshold <b>{fmt_rp(threshold)}</b> "
        f"(mean + std). Hari-hari ini menunjukkan aktivitas finansial lebih tinggi "
        f"dan dapat menjadi waktu strategis untuk program promosi."
    )
    card_end()

    st.markdown("<br>", unsafe_allow_html=True)

    # Bar chart harian — merah/hijau
    card(
        "Bar Chart Pengeluaran Harian",
        "🟥 Merah = lonjakan (> threshold) · 🟩 Hijau = normal",
    )
    fig_bar = go.Figure(go.Bar(
        x=harian["tanggal"],
        y=harian["total_pengeluaran"],
        marker_color=harian["warna"].tolist(),
        hovertemplate="<b>%{x|%d %b}</b><br>Rp %{y:,.0f}<extra></extra>",
    ))
    fig_bar.update_layout(
        **BASE_LAYOUT,
        height=230,
        xaxis=dict(gridcolor=GRID_COLOR, showline=False, tickformat="%d %b"),
        yaxis=dict(tickformat=".2s", gridcolor=GRID_COLOR, showline=False),
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    card_end()

    # Tabel lonjakan — identik output display(lonjakan) di notebook
    st.markdown("### 📋 Detail Hari dengan Lonjakan Pengeluaran")
    if not spike_df.empty:
        tbl3 = spike_df[["tanggal", "total_pengeluaran", "jumlah_transaksi"]].copy()
        tbl3.columns = ["Tanggal", "Total Pengeluaran (Rp)", "Jumlah Transaksi"]
        tbl3["Tanggal"]                = tbl3["Tanggal"].dt.strftime("%d %B %Y")
        tbl3["Total Pengeluaran (Rp)"] = tbl3["Total Pengeluaran (Rp)"].apply(
            lambda x: f"Rp {x:,.0f}"
        )
        tbl3 = tbl3.reset_index(drop=True)
        tbl3.index += 1
        st.dataframe(tbl3, use_container_width=True)
    else:
        st.info("Tidak ada lonjakan terdeteksi pada periode ini.")
