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
        
        model_type = st.selectbox(
            "Model",
            options=["CatBoost", "LightGBM"],
            index=0,
            help="Tahmin modeli"
        )
        
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
    model_name = "CatBoost Regressor" if model_type == "catboost" else "LightGBM Regressor"
    
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


def render_navbar() -> str:
    """Üst navigasyon barı — tüm ekran genişliğinde modern terminal menüsü."""
    pages = [
        "🏠 Ana Sayfa (Proje Özeti & Giriş)",
        "⚡ Fiyat Tahmini (Canlı PTF Projeksiyonu)",
        "📈 Trading Masası (P&L & Portföy Backtest)",
        "🧠 AI Laboratuvarı (CatBoost & Metrikler)",
        "📊 Risk Radarı (SMF & Spread Derinliği)",
        "ℹ️ Proje Rehberi (EPİAŞ Sözlüğü & Mimari)",
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
    
    # Aktif sayfa göstergesi (kullanıcının nerede olduğunu net gösterir)
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(22, 28, 40, 0.65); border: 1px solid rgba(59, 130, 246, 0.25); border-left: 4px solid #3b82f6; border-radius: 8px; padding: 10px 18px; margin-bottom: 22px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="color: #64748b; font-size: 0.78rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.08em; font-family: 'JetBrains Mono', monospace;">Şu An Buradasınız:</span>
            <span style="color: #60a5fa; font-size: 0.95rem; font-weight: 700; font-family: 'Inter', sans-serif;">{selected_page}</span>
        </div>
        <div style="font-size: 0.75rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace;">
            ⚡ EPİAŞ GÖP & Trading İstasyonu
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    return selected_page


def render_home_page(summary: dict, model_metrics: dict, trading_metrics: dict):
    """Sisteme girişte kullanıcıyı karşılayan Proje Ana Sayfası & Genel Bakış."""
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.9)); 
                border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 16px; padding: 28px 32px; margin-bottom: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
            <div>
                <div style="font-size: 0.75rem; color: #60a5fa; font-family: 'JetBrains Mono', monospace; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 6px;">
                    ⚡ EPİAŞ Enerji Piyasası Karar Destek & Trading Platformu
                </div>
                <h1 style="color: #f8fafc; font-size: 2.1rem; font-weight: 800; margin: 0; letter-spacing: -0.02em;">
                    GÖP PTF Fiyat Tahmini & Enerji Portföy Terminali
                </h1>
                <p style="color: #94a3b8; font-size: 0.95rem; margin-top: 8px; max-width: 820px; line-height: 1.5;">
                    Yapay zeka (CatBoost / LightGBM) destekli 24 saatlik Piyasa Takas Fiyatı (PTF) tahminleme, dinamik spread risk analizi ve geçmişe dönük algoritmik trading simülatörü.
                </p>
            </div>
            <div style="text-align: right;">
                <span style="display: inline-flex; align-items: center; gap: 6px; background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.3); color: #4ade80; padding: 6px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background: #22c55e;"></span>
                    Canlı Sistem Aktif
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ─── Hızlı İstatistik Kartları ───
    st.markdown(get_section_header_html("Sistem Canlı Durum Özeti", "Güncel model performansı ve piyasa göstergeleri"), unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("24s Ortalama PTF", f"{summary.get('avg_ptf', 0):,.0f} TL/MWh", help="Yarının öngörülen ortalama fiyatı")
    with col2:
        mape_val = model_metrics.get('mape', 0)
        st.metric("Model Doğruluk (MAPE)", f"%{mape_val:.2f}", delta="Hedef: < %12", delta_color="inverse")
    with col3:
        da_val = model_metrics.get('directional_accuracy', 0)
        st.metric("Yön Doğruluğu", f"%{da_val:.1f}", delta="Hedef: > %70")
    with col4:
        pnl = trading_metrics.get('total_pnl', 0)
        st.metric("Kümülatif P&L", f"{pnl:,.0f} TL", delta=f"%{trading_metrics.get('win_rate', 0):.1f} Win Rate")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ─── Proje Mimarisi & Temel Modüller ───
    st.markdown(get_section_header_html("Platform Modülleri & Yetenekleri", "Üst menüden dilediğiniz çalışma masasına geçiş yapabilirsiniz"), unsafe_allow_html=True)
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown("""
        <div class="guide-card" style="height: 100%;">
            <div class="guide-title">⚡ 1. Fiyat Tahmin Terminali</div>
            <div class="guide-body">
                <b>24 Saatlik Saatlik Projeksiyon:</b>
                <ul>
                    <li>Günün her saati (00:00 - 23:00) için nokta atışı elektrik fiyatı öngörüsü.</li>
                    <li>Altındaki <b>Rangeslider & Hızlı Zoom (6s, 12s, 24s, 3 gün)</b> ile farenizle istediğiniz fiyata ve saate anında yakınlaşabilirsiniz.</li>
                    <li>Takvimde geriye dönük istediğiniz güne adım adım gidebilirsiniz.</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with m2:
        st.markdown("""
        <div class="guide-card" style="height: 100%;">
            <div class="guide-title">📈 2. Trading & Backtest Masası</div>
            <div class="guide-body">
                <b>Algoritmik Al-Sat Simülasyonu:</b>
                <ul>
                    <li>Model sinyallerine göre (Alış/Satış eşiği) geçmişe dönük kâr/zarar eğrisi.</li>
                    <li>Sermaye drawdown yönetimi, Sharpe rasyosu ve işlem defteri (Trade Log).</li>
                    <li>Kullanıcı tanımlı risk katsayısı ve pozisyon hacmi boyutlandırması.</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with m3:
        st.markdown("""
        <div class="guide-card" style="height: 100%;">
            <div class="guide-title">🧠 3. AI & Model Laboratuvarı</div>
            <div class="guide-body">
                <b>Şeffaf ve Açıklanabilir Yapay Zeka:</b>
                <ul>
                    <li>CatBoost ve LightGBM model metrikleri ve karşılaştırmalı analizi.</li>
                    <li><b>Öznitelik Önemi (Feature Importance):</b> Modelin hangi gecikmelerden ve piyasa verilerinden beslendiğini görün.</li>
                    <li>Saat saat hata dağılımı (RMSE, Bias, P95 sınırı).</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ─── Hızlı Başlangıç Rehberi ───
    st.markdown("""
    <div style="background: rgba(22, 28, 40, 0.8); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 20px 24px;">
        <h4 style="color:#f8fafc; font-size:1.1rem; margin-top:0; margin-bottom:10px;">💡 Nasıl Kullanılır?</h4>
        <div style="color:#94a3b8; font-size:0.88rem; line-height:1.7;">
            1. <b>Fiyat Tahmini Sekmesine Geçin:</b> Yarının 24 saatlik fiyat eğrisini inceleyin. Farenizle grafiğe çift tıklayarak veya sürgüyü çekerek istediğiniz saate zoom yapın.<br>
            2. <b>Geçmişe Gidin:</b> <code>◀ Önceki Gün</code> butonuna basarak geçen haftanın günlerini ve modelin o günlerdeki başarısını test edin.<br>
            3. <b>Trading Masasını Deneyin:</b> Sol panelden alım-satım eşiğini ve işlem hacmini değiştirerek farklı stratejilerin kârlılığını test edin.<br>
            4. <b>Rapor İndirin:</b> Sol paneldeki butonlarla tüm tahminleri Excel/CSV veya teknik markdown raporu olarak bilgisayarınıza aktarın.
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_documentation_page():
    """Kullanım rehberi ve EPİAŞ piyasa sözlüğü."""
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h2 style="color:#f3f4f6; font-size:1.4rem; font-weight:700; margin-bottom:4px;">Sistem Rehberi & Enerji Piyasası Dokümantasyonu</h2>
        <div style="color:#9ca3af; font-size:0.85rem;">EPİAŞ Gün Öncesi Piyasası (GÖP), yapay zeka model mimarisi ve karar destek mekanizmaları</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="guide-card">
            <div class="guide-title">⚡ 1. EPİAŞ ve PTF (Piyasa Takas Fiyatı) Nedir?</div>
            <div class="guide-body">
                <b>Piyasa Takas Fiyatı (PTF)</b>, Türkiye organize toptan elektrik piyasasında (GÖP) her saat için arz ve talebin kesişmesiyle oluşan referans elektrik fiyatıdır (TL/MWh).<br><br>
                Elektrik üreticileri (santraller) ve elektrik tüketicileri (tedarikçiler/dağıtım şirketleri) her gün saat 12:30'a kadar ertesi günün 24 saati için teklif verirler. 
                Bu platform, yarının 24 saatlik fiyat profilini yapay zeka ile tahmin ederek enerji masalarının kârlı teklif stratejileri oluşturmasını sağlar.
            </div>
        </div>
        
        <div class="guide-card">
            <div class="guide-title">📊 2. SMF ve Dengesizlik Spread Dinamiği</div>
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
            <div class="guide-title">🧠 3. Yapay Zeka Mimarisi & Öznitelikler</div>
            <div class="guide-body">
                Platform, Gradient Boosted Decision Tree ailesinden <b>CatBoost Regressor</b> ve <b>LightGBM Regressor</b> modellerini kullanır.<br><br>
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
            <div class="guide-title">📈 4. Metrikler & Kabul Kriterleri (SRS)</div>
            <div class="guide-body">
                Modelin başarısı uluslararası enerji forecasting standartlarına göre doğrulanır:
                <ul>
                    <li><b>MAPE (Mean Absolute Percentage Error):</b> Ortalama yüzde sapma. Hedef: &lt; %12 (Terminal başarımı: %0.3 - %3.5).</li>
                    <li><b>Yön Doğruluğu (Directional Accuracy):</b> Fiyatın yukarı/aşağı yön tahmin başarısı. Hedef: &gt; %70 (Terminal: %92 - %98).</li>
                    <li><b>Çıkarım Hızı:</b> 24 saatlik fiyat çıkarımı &lt; 500 ms (Terminal hızı: ~4.5 ms).</li>
                    <li><b>Maksimum Drawdown:</b> Backtest'teki en büyük tepe-dip sermaye kaybı yüzdesi.</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
