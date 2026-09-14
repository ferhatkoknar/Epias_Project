"""
Kurumsal Koyu Tema CSS Stilleri (NFR-03)
Profesyonel finansal terminal estetiği — sade, temiz, kurumsal.
"""


def get_premium_css() -> str:
    """Kurumsal koyu tema CSS."""
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* ─── Global ─── */
    .stApp {
        background: #0c0f14 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    .stApp > header {
        background: transparent !important;
    }
    
    /* ─── Sidebar ─── */
    section[data-testid="stSidebar"] {
        background: #10141c !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #c8cdd6 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stSlider label,
    section[data-testid="stSidebar"] .stDateInput label,
    section[data-testid="stSidebar"] .stNumberInput label {
        color: #6b7280 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }
    
    /* ─── Metrik Kartları ─── */
    div[data-testid="stMetric"] {
        background: #141820 !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        border-radius: 8px !important;
        padding: 18px 20px !important;
        transition: border-color 0.2s ease !important;
    }
    
    div[data-testid="stMetric"]:hover {
        border-color: rgba(255, 255, 255, 0.08) !important;
    }
    
    div[data-testid="stMetric"] label {
        color: #6b7280 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.68rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
    }
    
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #e5e7eb !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600 !important;
        font-size: 1.45rem !important;
    }
    
    div[data-testid="stMetricDelta"] > div {
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 500 !important;
        font-size: 0.75rem !important;
    }
    
    /* ─── Sekmeler ─── */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06) !important;
        gap: 0 !important;
        padding: 0 !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: #6b7280 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.82rem !important;
        border-radius: 0 !important;
        padding: 12px 24px !important;
        border-bottom: 2px solid transparent !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0.01em !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #c8cdd6 !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #e5e7eb !important;
        border-bottom: 2px solid #3b82f6 !important;
        background: transparent !important;
    }
    
    .stTabs [data-baseweb="tab-border"],
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }
    
    /* ─── Butonlar ─── */
    .stButton > button {
        background: #1e2433 !important;
        color: #c8cdd6 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.8rem !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 6px !important;
        padding: 8px 20px !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background: #252d3d !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
    }
    
    .stDownloadButton > button {
        background: rgba(59, 130, 246, 0.08) !important;
        color: #60a5fa !important;
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
        border-radius: 6px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    .stDownloadButton > button:hover {
        background: rgba(59, 130, 246, 0.14) !important;
    }
    
    /* ─── Input ─── */
    .stSelectbox > div > div,
    .stDateInput > div > div,
    .stNumberInput > div > div {
        background: #141820 !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 6px !important;
        color: #e5e7eb !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stSelectbox > div > div:focus-within,
    .stDateInput > div > div:focus-within,
    .stNumberInput > div > div:focus-within {
        border-color: rgba(59, 130, 246, 0.4) !important;
    }
    
    /* ─── Slider ─── */
    .stSlider > div > div > div > div {
        background: #3b82f6 !important;
    }
    
    /* ─── Markdown ─── */
    .stMarkdown h1 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        color: #e5e7eb !important;
        letter-spacing: -0.02em;
        font-size: 1.3rem !important;
    }
    
    .stMarkdown h2, .stMarkdown h3 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        color: #c8cdd6 !important;
        letter-spacing: -0.01em;
    }
    
    .stMarkdown p, .stMarkdown li {
        font-family: 'Inter', sans-serif !important;
        color: #9ca3af !important;
        line-height: 1.6 !important;
    }
    
    /* ─── Divider ─── */
    hr {
        border-color: rgba(255, 255, 255, 0.04) !important;
        margin: 1.2rem 0 !important;
    }
    
    /* ─── DataTable ─── */
    .stDataFrame {
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    
    /* ─── Scrollbar ─── */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: #0c0f14; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.14); }
    
    /* ─── Hide Branding ─── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stDeployButton { display: none; }
    
    /* ─── Custom Components ─── */
    .terminal-header {
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        padding-bottom: 16px;
        margin-bottom: 24px;
    }
    
    .info-card {
        background: #141820;
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 8px;
        padding: 20px;
        margin: 8px 0;
    }
    
    .status-indicator {
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        margin-right: 6px;
    }
    
    .status-active { background: #22c55e; }
    .status-warning { background: #eab308; }
    .status-danger { background: #ef4444; }
    
    /* ─── Modern Tam Genişlik Navbar Stilleri ─── */
    div[data-testid="stRadio"] {
        background: rgba(14, 18, 26, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 6px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45) !important;
        width: 100% !important;
    }
    
    /* Streamlit Radio / Pills Navbar Özelleştirmesi */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        background: transparent !important;
        gap: 8px !important;
        display: flex !important;
        flex-direction: row !important;
        width: 100% !important;
        border: none !important;
    }
    
    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        flex: 1 1 0px !important;
        background: rgba(22, 28, 40, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 9px !important;
        padding: 12px 10px !important;
        color: #9ca3af !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        text-align: center !important;
        justify-content: center !important;
        align-items: center !important;
        transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1) !important;
        margin: 0 !important;
        box-sizing: border-box !important;
    }
    
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover {
        background: rgba(59, 130, 246, 0.14) !important;
        border-color: rgba(59, 130, 246, 0.4) !important;
        color: #f3f4f6 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    }
    
    div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-checked="true"],
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.35), rgba(59, 130, 246, 0.18)) !important;
        border-color: #3b82f6 !important;
        color: #60a5fa !important;
        font-weight: 700 !important;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* Radio yuvarlak butonunu gizle, sadece şık buton görünümü ver */
    div[data-testid="stRadio"] input[type="radio"] {
        display: none !important;
    }
    
    /* Radio yuvarlak simgesini küçült/gizle */
    div[data-testid="stRadio"] [data-baseweb="radio"] > div:first-child:not([data-testid="stMarkdownContainer"]) {
        display: none !important;
    }
    
    /* Buton içindeki metni net, parlak ve belirgin göster */
    div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #e2e8f0 !important;
        margin: 0 !important;
        padding: 4px 6px !important;
        text-align: center !important;
        line-height: 1.3 !important;
        visibility: visible !important;
        opacity: 1 !important;
        white-space: normal !important;
    }
    
    div[data-testid="stRadio"] label:hover [data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
    }
    
    div[data-testid="stRadio"] label[data-checked="true"] [data-testid="stMarkdownContainer"] p,
    div[data-testid="stRadio"] label:has(input:checked) [data-testid="stMarkdownContainer"] p {
        color: #60a5fa !important;
        font-weight: 700 !important;
    }
    
    /* Bilgi ve Rehber Kartları */
    .guide-card {
        background: #141820;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 16px;
        transition: border-color 0.2s;
    }
    .guide-card:hover {
        border-color: rgba(59, 130, 246, 0.25);
    }
    .guide-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #f3f4f6;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .guide-body {
        font-size: 0.85rem;
        color: #9ca3af;
        line-height: 1.6;
    }
    </style>
    """


import textwrap
import streamlit as st


def clean_html(raw_html: str) -> str:
    """Minify and clean HTML string so markdown/Streamlit never parses it as a code block."""
    return "".join(line.strip() for line in raw_html.splitlines() if line.strip())


def render_html(html_code: str):
    """Safely render HTML without markdown code-block conversion."""
    cleaned = clean_html(html_code)
    try:
        st.html(cleaned)
    except Exception:
        st.markdown(cleaned, unsafe_allow_html=True)


def get_header_html() -> str:
    """Kurumsal terminal başlığı."""
    raw = """
    <div class="terminal-header">
        <div style="display: flex; justify-content: space-between; align-items: flex-end;">
            <div>
                <div style="font-size: 0.65rem; color: #4b5563; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 6px;">EPİAŞ Gün Öncesi Piyasası</div>
                <div style="font-size: 1.4rem; font-weight: 700; font-family: 'Inter', sans-serif; color: #e5e7eb; letter-spacing: -0.02em;">PTF Tahmin & Trading Terminali</div>
            </div>
            <div style="font-size: 0.68rem; color: #4b5563; font-family: 'JetBrains Mono', monospace; text-align: right; letter-spacing: 0.04em;">
                <span class="status-indicator status-active"></span> Sistem Aktif
            </div>
        </div>
    </div>
    """
    return clean_html(raw)


def get_section_header_html(title: str, subtitle: str = "") -> str:
    """Bölüm başlığı."""
    sub = f'<div style="color: #4b5563; font-size: 0.72rem; font-family: Inter, sans-serif; margin-top: 2px;">{subtitle}</div>' if subtitle else ""
    raw = f"""
    <div style="margin: 20px 0 12px 0;">
        <div style="font-size: 0.7rem; color: #6b7280; font-family: 'Inter', sans-serif; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em;">{title}</div>
        {sub}
    </div>
    """
    return clean_html(raw)


def get_ticker_bar_html(
    tsi_time_str: str,
    session_name: str,
    last_ptf: float,
    base_load: float,
    peak_load: float,
    spread_val: float,
    system_direction: str,
    mode_label: str = "CANLI PIYASA",
    is_live: bool = False,
    selected_hour_str: str = "16:00",
) -> str:
    """
    Bloomberg/Refinitiv tarzı üst piyasa bilgi ve seans bantı.
    """
    import math
    def fmt_tl(val):
        if val is None or (isinstance(val, (int, float)) and math.isnan(val)):
            return "NaN TL"
        return f"{val:,.0f} TL"

    def fmt_spread(val):
        if val is None or (isinstance(val, (int, float)) and math.isnan(val)):
            return "NaN TL"
        return f"{val:+,.0f} TL"

    dir_color = "#22c55e" if "FAZLASI" in system_direction else "#f59e0b" if ("DENGE" in system_direction or "BEKLE" in system_direction) else "#ef4444"
    dot_color = "#22c55e" if is_live else "#f59e0b" if "ŞABLON" in mode_label else "#38bdf8"
    ptf_label = "PTF GÜNCEL" if is_live else f"PTF ({selected_hour_str})" if selected_hour_str else "PTF"
    
    last_ptf_str = fmt_tl(last_ptf)
    base_load_str = fmt_tl(base_load)
    peak_load_str = fmt_tl(peak_load)
    spread_str = fmt_spread(spread_val)
    spread_color = "#94a3b8" if (spread_val is None or (isinstance(spread_val, float) and math.isnan(spread_val))) else ('#22c55e' if spread_val >= 0 else '#ef4444')

    raw = f"""
    <div style="display: flex; align-items: center; justify-content: space-between; background: #0f141d; border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 8px; padding: 8px 16px; margin-bottom: 18px; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #9ca3af; gap: 12px; flex-wrap: wrap;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: {dot_color}; box-shadow: 0 0 8px {dot_color};"></span>
            <span style="color: {'#22c55e' if is_live else '#fbbf24' if 'ŞABLON' in mode_label else '#38bdf8'}; font-weight: 600;">{mode_label}</span>
            <span style="color: #64748b;">|</span>
            <span>TSI: <span style="color: #e2e8f0; font-weight: 600;">{tsi_time_str}</span></span>
            <span style="color: #64748b;">|</span>
            <span style="background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); color: #60a5fa; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.68rem;">{session_name}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap;">
            <div>{ptf_label}: <span style="color: #f8fafc; font-weight: 600;">{last_ptf_str}</span></div>
            <div>BAZ YÜK: <span style="color: #cbd5e1;">{base_load_str}</span></div>
            <div>PUANT: <span style="color: #60a5fa; font-weight: 600;">{peak_load_str}</span></div>
            <div>SPREAD: <span style="color: {spread_color};">{spread_str}</span></div>
            <div style="display: flex; align-items: center; gap: 6px;">
                <span>SİSTEM:</span>
                <span style="color: {dir_color}; font-weight: 600; background: rgba(255,255,255,0.03); padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.06);">{system_direction}</span>
            </div>
        </div>
    </div>
    """
    return clean_html(raw)
