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
    
    </style>
    """


def get_header_html() -> str:
    """Kurumsal terminal başlığı."""
    return """
    <div class="terminal-header">
        <div style="display: flex; justify-content: space-between; align-items: flex-end;">
            <div>
                <div style="
                    font-size: 0.65rem;
                    color: #4b5563;
                    font-family: 'JetBrains Mono', monospace;
                    letter-spacing: 0.12em;
                    text-transform: uppercase;
                    margin-bottom: 6px;
                ">EPİAŞ Gün Öncesi Piyasası</div>
                <div style="
                    font-size: 1.4rem;
                    font-weight: 700;
                    font-family: 'Inter', sans-serif;
                    color: #e5e7eb;
                    letter-spacing: -0.02em;
                ">PTF Tahmin & Trading Terminali</div>
            </div>
            <div style="
                font-size: 0.68rem;
                color: #4b5563;
                font-family: 'JetBrains Mono', monospace;
                text-align: right;
                letter-spacing: 0.04em;
            ">
                <span class="status-indicator status-active"></span> Sistem Aktif
            </div>
        </div>
    </div>
    """


def get_section_header_html(title: str, subtitle: str = "") -> str:
    """Bölüm başlığı."""
    sub = f'<div style="color: #4b5563; font-size: 0.72rem; font-family: Inter, sans-serif; margin-top: 2px;">{subtitle}</div>' if subtitle else ""
    return f"""
    <div style="margin: 20px 0 12px 0;">
        <div style="
            font-size: 0.7rem;
            color: #6b7280;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        ">{title}</div>
        {sub}
    </div>
    """
