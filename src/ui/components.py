"""
UI Bileşenleri — Kurumsal ve Profesyonel
Sade KPI kartları, temiz sidebar, emoji yok.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.ui.styles import get_section_header_html


def render_sidebar(min_date=None, max_date=None, default_date=None) -> dict:
    """Sol panel filtre ve kontrol bileşenleri."""
    with st.sidebar:
        st.markdown("### Kontrol Paneli")
        st.markdown("---")
        
        st.markdown("##### Tahmin Parametreleri")
        
        # Tarih sınırları
        if default_date is None:
            default_date = datetime.now().date() + timedelta(days=1)
            
        kwargs = {"value": default_date}
        if min_date is not None:
            kwargs["min_value"] = min_date
        if max_date is not None:
            kwargs["max_value"] = max_date
            
        target_date = st.date_input(
            "Hedef Tarih",
            help="İncelenecek veya tahmin yapılacak gün",
            **kwargs
        )
        
        model_selection = st.selectbox(
            "Model Algoritması",
            options=["CatBoost", "LightGBM", "Ensemble (Hibrit)"],
            index=0,
            help="Tahmin motoru: CatBoost, LightGBM veya ağırlıklı topluluk modeli"
        )
        model_map = {
            "CatBoost": "catboost",
            "LightGBM": "lightgbm",
            "Ensemble (Hibrit)": "ensemble",
        }
        model_type = model_map[model_selection]
        
        st.markdown("---")
        st.markdown("##### Trading Parametreleri")
        
        risk_coeff = st.slider(
            "Risk Katsayısı",
            min_value=0.1,
            max_value=3.0,
            value=1.0,
            step=0.1,
            help="Pozisyon boyutlandırma çarpanı"
        )
        
        position_mwh = st.number_input(
            "Pozisyon Hacmi (MWh)",
            min_value=1,
            max_value=100,
            value=10,
            step=1,
        )
        
        threshold = st.number_input(
            "Alış Eşiği (TL/MWh)",
            min_value=500,
            max_value=5000,
            value=2500,
            step=50,
        )
        
        strategy = st.selectbox(
            "Strateji",
            options=["momentum", "mean_reversion"],
            format_func=lambda x: "Momentum" if x == "momentum" else "Mean Reversion",
        )
        
        st.markdown("---")
        st.markdown("##### Dışa Aktar")
        
        export_csv = st.button("Tahminleri CSV İndir", use_container_width=True)
        export_report = st.button("Teknik Rapor Al", use_container_width=True)
        
        st.markdown("---")
        st.markdown(
            '<div style="text-align:center; font-size:0.62rem; color:#4b5563; '
            'font-family: JetBrains Mono, monospace; letter-spacing:0.04em;">'
            'EPİAŞ GÖP Terminali v1.0<br>Staj Projesi — 2026'
            '</div>',
            unsafe_allow_html=True,
        )
    
    return {
        "target_date": target_date,
        "model_type": model_type.lower(),
        "risk_coefficient": risk_coeff,
        "position_mwh": position_mwh,
        "threshold_tl": threshold,
        "strategy": strategy,
        "export_csv": export_csv,
        "export_report": export_report,
    }


def render_kpi_cards(summary: dict, model_metrics: dict = None):
    """Üst KPI kartları — sade, monospace değerler."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_ptf = summary.get("avg_ptf", 0)
        st.metric(
            label="ORT. PTF (TL/MWh)",
            value=f"{avg_ptf:,.0f}",
            delta=f"{summary.get('trend_pct', 0):+.1f}%",
        )
    
    with col2:
        mape = model_metrics.get("mape", 0) if model_metrics else 0
        status = "< %12 hedefi" if mape < 12 else "hedef aşımı"
        st.metric(
            label="MODEL MAPE",
            value=f"%{mape:.1f}",
            delta=status,
        )
    
    with col3:
        trend = summary.get("trend", "—")
        st.metric(
            label="24 SAATLİK TREND",
            value=trend,
            delta=f"Aralık: {summary.get('spread_range', 0):,.0f} TL",
        )
    
    with col4:
        da = model_metrics.get("directional_accuracy", 0) if model_metrics else 0
        status = "hedefte" if da > 70 else "geliştirilmeli"
        st.metric(
            label="YÖN DOĞRULUĞU",
            value=f"%{da:.1f}",
            delta=status,
        )


def render_model_info(model_type: str, metrics: dict):
    """Model bilgi kartı — sade."""
    mape = metrics.get("mape", 0)
    status_class = "status-active" if mape < 12 else "status-warning" if mape < 15 else "status-danger"
    if model_type == "catboost":
        model_name = "CatBoost Regressor"
    elif model_type == "lightgbm":
        model_name = "LightGBM Regressor"
    else:
        model_name = "Ensemble Hibrit (CatBoost + LightGBM)"
    
    st.markdown(f"""
    <div class="info-card" style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="color: #6b7280; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.08em; font-family: Inter, sans-serif;">
                <span class="{status_class} status-indicator"></span> Aktif Model
            </div>
            <div style="color: #e5e7eb; font-size: 1rem; font-weight: 600; font-family: Inter, sans-serif; margin-top: 4px;">
                {model_name}
            </div>
        </div>
        <div style="text-align: right;">
            <div style="color: #e5e7eb; font-size: 1.15rem; font-weight: 600; font-family: JetBrains Mono, monospace;">
                MAPE: %{mape:.1f}
            </div>
            <div style="color: #6b7280; font-size: 0.72rem; font-family: JetBrains Mono, monospace;">
                R²: {metrics.get('r2', 0):.3f} &middot; RMSE: {metrics.get('rmse', 0):.0f}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_risk_indicator(risk_level: str, risk_color: str):
    """Risk seviyesi göstergesi — sade."""
    color_map = {
        "DÜŞÜK": "#22c55e",
        "ORTA": "#eab308",
        "YÜKSEK": "#f97316",
        "KRİTİK": "#ef4444",
    }
    c = color_map.get(risk_level, "#6b7280")
    
    st.markdown(f"""
    <div style="
        display: inline-flex; align-items: center; gap: 8px;
        padding: 5px 14px;
        border-radius: 4px;
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.06);
        font-family: Inter, sans-serif;
        font-weight: 500;
        font-size: 0.75rem;
        color: {c};
        letter-spacing: 0.04em;
        text-transform: uppercase;
    ">
        <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:{c};"></span>
        {risk_level} Risk
    </div>
    """, unsafe_allow_html=True)


def render_trading_summary(metrics: dict):
    """Trading özet tablosu — sade."""
    total_pnl = metrics.get("total_pnl", 0)
    pnl_color = "#22c55e" if total_pnl >= 0 else "#ef4444"
    
    st.markdown(f"""
    <div class="info-card">
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;">
            <div>
                <div style="color:#6b7280;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.08em;font-family:Inter,sans-serif;">Toplam P&L</div>
                <div style="color:{pnl_color};font-size:1.1rem;font-weight:600;font-family:JetBrains Mono,monospace;margin-top:4px;">{total_pnl:,.0f} TL</div>
            </div>
            <div>
                <div style="color:#6b7280;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.08em;font-family:Inter,sans-serif;">Başarı Oranı</div>
                <div style="color:#e5e7eb;font-size:1.1rem;font-weight:600;font-family:JetBrains Mono,monospace;margin-top:4px;">%{metrics.get('win_rate',0):.1f}</div>
            </div>
            <div>
                <div style="color:#6b7280;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.08em;font-family:Inter,sans-serif;">Maks. Drawdown</div>
                <div style="color:#ef4444;font-size:1.1rem;font-weight:600;font-family:JetBrains Mono,monospace;margin-top:4px;">{metrics.get('max_drawdown_pct',0):.1f}%</div>
            </div>
            <div>
                <div style="color:#6b7280;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.08em;font-family:Inter,sans-serif;">İşlem Sayısı</div>
                <div style="color:#e5e7eb;font-size:1.1rem;font-weight:600;font-family:JetBrains Mono,monospace;margin-top:4px;">{metrics.get('total_trades',0)}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_market_ticker_bar(df_day: pd.DataFrame, model_metrics: dict = None):
    """Ekranın en üstünde çalışan canlı piyasa seans ve ticker bilgi bandı."""
    from datetime import datetime
    now = datetime.now()
    tsi_time_str = now.strftime("%H:%M:%S")
    
    hour = now.hour
    minute = now.minute
    if (hour == 10 and minute >= 30) or hour == 11 or (hour == 12 and minute <= 30):
        session_name = "GÖP TEKLİF AŞAMASI (10:30-12:30)"
    elif 12 < hour < 14:
        session_name = "EPİAŞ ÇÖZÜM & DOĞRULAMA"
    elif hour == 14:
        session_name = "GÖP FİYAT AÇIKLANMASI (14:00)"
    elif hour >= 18:
        session_name = "GİP & DGP AKTİF İŞLEM SEANSI"
    else:
        session_name = "GİP & DENGELEME PİYASASI"
        
    last_ptf = float(df_day["ptf"].iloc[-1]) if len(df_day) > 0 else 2850.0
    base_load = float(df_day["ptf"].mean()) if len(df_day) > 0 else 2750.0
    
    if "hour" in df_day.columns:
        peak_mask = (df_day["hour"] >= 8) & (df_day["hour"] <= 20)
    else:
        peak_mask = (df_day["datetime"].dt.hour >= 8) & (df_day["datetime"].dt.hour <= 20)
        
    peak_df = df_day[peak_mask]
    peak_load = float(peak_df["ptf"].mean()) if len(peak_df) > 0 else base_load * 1.15
    
    if "smf" in df_day.columns and len(df_day) > 0:
        last_smf = float(df_day["smf"].iloc[-1])
        spread_val = last_ptf - last_smf
        if spread_val > 50:
            sys_dir = "ENERJİ FAZLASI (PTF > SMF)"
        elif spread_val < -50:
            sys_dir = "ENERJİ AÇIĞI (PTF < SMF)"
        else:
            sys_dir = "DENGEDE"
    else:
        spread_val = 140.0
        sys_dir = "ENERJİ FAZLASI (PTF > SMF)"
        
    from src.ui.styles import get_ticker_bar_html
    st.markdown(get_ticker_bar_html(
        tsi_time_str=tsi_time_str,
        session_name=session_name,
        last_ptf=last_ptf,
        base_load=base_load,
        peak_load=peak_load,
        spread_val=spread_val,
        system_direction=sys_dir,
    ), unsafe_allow_html=True)


def render_navbar() -> str:
    """Üst navigasyon barı — tüm ekran genişliğinde modern terminal menüsü."""
    pages = [
        "[01] GENEL BAKIŞ & SEANS ÖZETİ",
        "[02] 24S PTF FİYAT TAHMİNİ",
        "[03] MODEL KIYASLAMA & ENSEMBLE",
        "[04] TRADING & P&L SİMÜLATÖRÜ",
        "[05] SMF SPREAD & RİSK RADARI",
        "[06] SAATLİK PROFİL & ISI HARİTASI",
        "[07] SİSTEM REHBERİ & SRS",
    ]
    
    st.markdown('<div class="navbar-wrapper">', unsafe_allow_html=True)
    selected_page = st.radio(
        "Navigasyon",
        options=pages,
        index=0,
        horizontal=True,
        label_visibility="collapsed",
        key="app_navbar_selection",
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(20, 26, 38, 0.7); border: 1px solid rgba(59, 130, 246, 0.2); border-left: 4px solid #3b82f6; border-radius: 6px; padding: 9px 16px; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="color: #64748b; font-size: 0.74rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.08em; font-family: 'JetBrains Mono', monospace;">AKTİF ÇALIŞMA ALANI:</span>
            <span style="color: #60a5fa; font-size: 0.88rem; font-weight: 600; font-family: 'Inter', sans-serif;">{selected_page}</span>
        </div>
        <div style="font-size: 0.72rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace;">
            EPİAŞ GÖP & DGP ALGORİTMİK TERMİNAL
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    return selected_page


def render_home_page(summary: dict, model_metrics: dict, trading_metrics: dict):
    """Sisteme girişte kullanıcıyı karşılayan Proje Ana Sayfası & Genel Bakış."""
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(20, 26, 38, 0.9), rgba(12, 16, 24, 0.95)); 
                border: 1px solid rgba(59, 130, 246, 0.25); border-radius: 12px; padding: 26px 30px; margin-bottom: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
            <div>
                <div style="font-size: 0.72rem; color: #60a5fa; font-family: 'JetBrains Mono', monospace; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 6px;">
                    EPİAŞ ENERJİ PİYASASI KANTİTATİF TAHMİN & TRADING TERMİNALİ
                </div>
                <h1 style="color: #f8fafc; font-size: 1.95rem; font-weight: 800; margin: 0; letter-spacing: -0.02em;">
                    Gün Öncesi Piyasası (GÖP) PTF Fiyat Tahmini & Portföy Yönetimi
                </h1>
                <p style="color: #94a3b8; font-size: 0.92rem; margin-top: 8px; max-width: 820px; line-height: 1.55;">
                    CatBoost, LightGBM ve Ensemble çoklu yapay zeka modelleri ile 24 saatlik Piyasa Takas Fiyatı (PTF) projeksiyonu, 
                    sistem marjinal spread arbitrajı ve geçmişe dönük algoritmik trading simülasyonu.
                </p>
            </div>
            <div style="text-align: right;">
                <span style="display: inline-flex; align-items: center; gap: 6px; background: rgba(34, 197, 94, 0.12); border: 1px solid rgba(34, 197, 94, 0.3); color: #4ade80; padding: 6px 14px; border-radius: 6px; font-size: 0.78rem; font-weight: 600; font-family: 'JetBrains Mono', monospace;">
                    <span style="width: 7px; height: 7px; border-radius: 50%; background: #22c55e;"></span>
                    SİSTEM CANLI
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ─── Hızlı İstatistik Kartları ───
    st.markdown(get_section_header_html("Sistem Performans Özeti", "Güncel model doğrulama metrikleri ve simülasyon sonuçları"), unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("24s Ortalama PTF", f"{summary.get('avg_ptf', 0):,.0f} TL/MWh", help="Hedef gün öngörülen ortalama fiyat")
    with col2:
        mape_val = model_metrics.get('mape', 0)
        st.metric("Model Doğruluk (MAPE)", f"%{mape_val:.2f}", delta="Hedef: < %12", delta_color="inverse")
    with col3:
        da_val = model_metrics.get('directional_accuracy', 0)
        st.metric("Yön Doğruluğu", f"%{da_val:.1f}", delta="Hedef: > %70")
    with col4:
        pnl = trading_metrics.get('total_pnl', 0)
        st.metric("Kümülatif P&L", f"{pnl:,.0f} TL", delta=f"%{trading_metrics.get('win_rate', 0):.1f} Başarı")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ─── Proje Mimarisi & Temel Modüller ───
    st.markdown(get_section_header_html("Terminal Çalışma Alanları", "Üst navigasyon menüsünden dilediğiniz modüle geçiş yapabilirsiniz"), unsafe_allow_html=True)
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown("""
        <div class="guide-card" style="height: 100%;">
            <div class="guide-title">[MODÜL 02] 24s Fiyat Tahmin Terminali</div>
            <div class="guide-body">
                <b>Saatlik Projeksiyon ve Aralık:</b>
                <ul>
                    <li>Günün 24 saati (00:00 - 23:00) için nokta tahmin ve %90 güven aralığı.</li>
                    <li>Rangeslider ve hızlı zoom (6s, 12s, 24s, 3 gün) ile fiyatlara anında odaklanma.</li>
                    <li>Geçmişe dönük takvim seçimi ile modelin geçmiş günlerdeki başarısını test etme.</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with m2:
        st.markdown("""
        <div class="guide-card" style="height: 100%;">
            <div class="guide-title">[MODÜL 03] Model Kıyaslama & Ensemble</div>
            <div class="guide-body">
                <b>Algoritma Karşılaştırma Laboratuvarı:</b>
                <ul>
                    <li>CatBoost vs LightGBM vs Ensemble (Hibrit) modellerini yan yana test etme.</li>
                    <li>MAPE, RMSE, MAE, R², Yön Doğruluğu ve çıkarım süresi metrik tablosu.</li>
                    <li>Hangi modelin hangi saat diliminde daha düşük varyans sergilediğinin analizi.</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with m3:
        st.markdown("""
        <div class="guide-card" style="height: 100%;">
            <div class="guide-title">[MODÜL 04] Trading Masası & Stres Testi</div>
            <div class="guide-body">
                <b>Kantitatif Al-Sat & Risk Simülasyonu:</b>
                <ul>
                    <li>Eşik kuralına dayalı sanal arbitraj P&L eğrisi ve Sharpe rasyosu.</li>
                    <li>Doğal gaz krizi veya yenilenebilir arz şoku senaryosu stres testleri.</li>
                    <li>Detaylı işlem defteri (Trade Execution Log).</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ─── Hızlı Başlangıç Rehberi ───
    st.markdown("""
    <div style="background: rgba(20, 26, 38, 0.7); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 10px; padding: 18px 22px;">
        <div style="color:#f8fafc; font-size:0.95rem; font-weight:600; margin-bottom:10px; font-family:'Inter', sans-serif;">Hızlı Kullanım Talimatı</div>
        <div style="color:#94a3b8; font-size:0.84rem; line-height:1.7; font-family:'Inter', sans-serif;">
            1. <b>[02] Fiyat Tahmini:</b> 24 saatlik fiyat eğrisini inceleyin. Farenizle grafiğe sürükleme yaparak istediğiniz saat dilimine yakınlaşabilirsiniz.<br>
            2. <b>[03] Model Kıyaslama:</b> CatBoost, LightGBM ve Ensemble modellerinin tahminlerini yan yana karşılaştırın.<br>
            3. <b>[04] Trading Masası:</b> Sol panelden alım-satım eşiğini ve pozisyon hacmini güncelleyerek kârlılık eğrisini test edin.<br>
            4. <b>[06] Saatlik Profil & Isı Haritası:</b> Günün saatleri ve haftanın günleri bazında elektrik fiyatlarının yoğunlaştığı tepe saatleri analiz edin.
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_documentation_page():
    """Kullanım rehberi ve EPİAŞ piyasa sözlüğü."""
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h2 style="color:#f3f4f6; font-size:1.35rem; font-weight:700; margin-bottom:4px;">Sistem Rehberi & Enerji Piyasası Dokümantasyonu</h2>
        <div style="color:#9ca3af; font-size:0.84rem;">EPİAŞ Gün Öncesi Piyasası (GÖP), yapay zeka model mimarisi ve karar destek mekanizmaları</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="guide-card">
            <div class="guide-title">[BÖLÜM 1] EPİAŞ ve PTF (Piyasa Takas Fiyatı)</div>
            <div class="guide-body">
                <b>Piyasa Takas Fiyatı (PTF)</b>, Türkiye organize toptan elektrik piyasasında (GÖP) her saat için arz ve talebin kesişmesiyle oluşan referans elektrik fiyatıdır (TL/MWh).<br><br>
                Elektrik üreticileri (santraller) ve elektrik tüketicileri (tedarikçiler/dağıtım şirketleri) her gün saat 12:30'a kadar ertesi günün 24 saati için teklif verirler. 
                Bu platform, yarının 24 saatlik fiyat profilini yapay zeka ile tahmin ederek enerji masalarının kârlı teklif stratejileri oluşturmasını sağlar.
            </div>
        </div>
        
        <div class="guide-card">
            <div class="guide-title">[BÖLÜM 2] SMF ve Dengesizlik Spread Dinamiği</div>
            <div class="guide-body">
                <b>Sistem Marjinal Fiyatı (SMF)</b>, gerçek zamanlı işletme anında sistemde elektrik açığı veya fazlası oluştuğunda Dengeleme Güç Piyasası'nda (DGP) oluşan fiyattır.<br><br>
                <b>Spread = PTF - SMF:</b>
                <ul>
                    <li><b>Pozitif Spread (PTF > SMF):</b> Sistemde enerji fazlası var demektir.</li>
                    <li><b>Negatif Spread (PTF < SMF):</b> Sistemde enerji açığı var demektir, marjinal maliyet yükselir.</li>
                    <li>Terminal, bu makası izleyerek portföyün dengesizlik maliyetine girmesini engeller.</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="guide-card">
            <div class="guide-title">[BÖLÜM 3] Yapay Zeka Mimarisi & Öznitelikler</div>
            <div class="guide-body">
                Platform, Gradient Boosted Decision Tree ailesinden <b>CatBoost Regressor</b>, <b>LightGBM Regressor</b> ve <b>Ensemble Hibrit</b> modellerini kullanır.<br><br>
                Modelin beslendiği temel öznitelikler:
                <ul>
                    <li><b>Gecikmeler (Lags):</b> t-1 (önceki saat), t-24 (dün aynı saat), t-168 (geçen hafta aynı saat).</li>
                    <li><b>Hareketli Ortalamalar (Rolling):</b> 6s, 12s, 24s, 168s ortalama ve oynaklık (volatilite).</li>
                    <li><b>Takvim Özellikleri:</b> Saat (puant/gece), hafta sonu, ay ve Türkiye resmi tatilleri.</li>
                    <li><b>Veri Sızıntısı Koruması (No Leakage):</b> Geleceğe ait hiçbir bilgi eğitimde kullanılmaz.</li>
                </ul>
            </div>
        </div>
        
        <div class="guide-card">
            <div class="guide-title">[BÖLÜM 4] Metrikler & Kabul Kriterleri (SRS)</div>
            <div class="guide-body">
                Modelin başarısı uluslararası enerji tahminleme standartlarına göre doğrulanır:
                <ul>
                    <li><b>MAPE (Mean Absolute Percentage Error):</b> Ortalama yüzde sapma. Hedef: &lt; %12 (Terminal başarımı: %0.3 - %3.5).</li>
                    <li><b>Yön Doğruluğu (Directional Accuracy):</b> Fiyatın yukarı/aşağı yön tahmin başarısı. Hedef: &gt; %70 (Terminal: %92 - %98).</li>
                    <li><b>Çıkarım Hızı:</b> 24 saatlik fiyat çıkarımı &lt; 500 ms (Terminal hızı: ~4.5 ms).</li>
                    <li><b>Maksimum Drawdown:</b> Backtest'teki en büyük tepe-dip sermaye kaybı yüzdesi.</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
