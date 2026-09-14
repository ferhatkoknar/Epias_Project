"""
UI Bileşenleri — Kurumsal ve Profesyonel
Sade KPI kartları, temiz sidebar, emoji yok.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src.ui.styles import get_section_header_html, render_html


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
        
        forecast_method = st.selectbox(
            "Tahminleme Ufku / Yöntem",
            options=["recursive", "direct"],
            index=0,
            format_func=lambda x: "[12:30 UYUMLU] Özyinelemeli" if x == "recursive" else "[STANDART] Doğrudan (Direct)",
            help="Özyinelemeli yöntem: EPİAŞ 12:30 kapı kapanışı kuralına göre gelecek saatlerin bilinmeyen lag değerlerini modelin adım adım rollout tahminleriyle simüle eder (Sıfır Gelecek Sızıntısı)."
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
    
    return {
        "target_date": target_date,
        "model_type": model_type.lower(),
        "forecast_method": forecast_method,
        "risk_coefficient": risk_coeff,
        "position_mwh": position_mwh,
        "threshold_tl": threshold,
        "strategy": strategy,
    }


def render_sidebar_export_section(
    day_data: pd.DataFrame,
    model_metrics: dict,
    trading_metrics: dict,
    forecast_summary: dict,
    model_type: str,
    target_date_str: str,
    backtest_df: pd.DataFrame = None,
):
    """
    Sol panel içinde doğrudan çalışan 1-tıkla indirme ve raporlama merkezi:
    - HTML Yönetici Raporu (Tarayıcıda anında açılır, yazdırılabilir, PDF kaydedilebilir)
    - Word (DOCX) Raporu (Microsoft Word uyumlu)
    - Excel (XLSX) Çalışma Kitabı (Çok sekmeli tablo)
    - Standart CSV (BOM UTF-8, Türkçe Excel uyumlu)
    """
    from src.ui.export import (
        export_predictions_csv,
        export_predictions_excel,
        generate_technical_report_html,
        generate_technical_report_docx,
    )
    
    with st.sidebar:
        st.markdown("---")
        st.markdown("##### Dışa Aktar & Rapor İndir")
        
        # Byte yüklerini hazırla (Hata dayanımlı)
        try:
            csv_bytes = export_predictions_csv(day_data, metrics=model_metrics)
        except Exception:
            csv_bytes = b""

        try:
            xlsx_bytes = export_predictions_excel(
                day_data,
                model_metrics=model_metrics,
                trading_metrics=trading_metrics,
                backtest_df=backtest_df,
            )
        except Exception:
            xlsx_bytes = b""

        try:
            html_report = generate_technical_report_html(
                metrics=model_metrics,
                trading_metrics=trading_metrics,
                summary=forecast_summary,
                day_df=day_data,
                model_type=model_type,
                target_date_str=target_date_str,
            )
        except Exception:
            html_report = "<html><body>Rapor oluşturulamadı.</body></html>"

        try:
            docx_bytes = generate_technical_report_docx(
                metrics=model_metrics,
                trading_metrics=trading_metrics,
                summary=forecast_summary,
                day_df=day_data,
                model_type=model_type,
                target_date_str=target_date_str,
            )
        except Exception:
            docx_bytes = b""
        
        with st.expander("Teknik Analiz Raporu İndir", expanded=True):
            st.download_button(
                label="Raporu İndir (HTML / Web & PDF)",
                data=html_report.encode("utf-8") if isinstance(html_report, str) else html_report,
                file_name=f"teknik_rapor_{target_date_str}.html",
                mime="text/html",
                use_container_width=True,
                help="Herhangi bir web tarayıcısında (Chrome, Edge) anında açılır. Ctrl+P ile PDF olarak kaydedilebilir.",
            )
            if docx_bytes:
                st.download_button(
                    label="Raporu İndir (Word / DOCX)",
                    data=docx_bytes,
                    file_name=f"teknik_rapor_{target_date_str}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    help="Microsoft Word ile doğrudan açılır.",
                )
            
        with st.expander("Tahmin Verilerini İndir", expanded=True):
            if xlsx_bytes:
                st.download_button(
                    label="Tahminleri İndir (Excel / XLSX)",
                    data=xlsx_bytes,
                    file_name=f"ptf_tahmin_{target_date_str}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    help="Çok sekmeli Microsoft Excel çalışma kitabı.",
                )
            if csv_bytes:
                st.download_button(
                    label="Tahminleri İndir (CSV)",
                    data=csv_bytes,
                    file_name=f"ptf_tahmin_{target_date_str}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Excel ve Python uyumlu, Türkçe karakter destekli UTF-8 CSV.",
                )
            
        st.markdown("---")
        render_html(
            '<div style="text-align:center; font-size:0.62rem; color:#4b5563; '
            'font-family: JetBrains Mono, monospace; letter-spacing:0.04em;">'
            'EPİAŞ GÖP Terminali v1.2<br>Staj Projesi — 2026'
            '</div>'
        )


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


def render_model_info(model_type: str, metrics: dict, forecast_method: str = "recursive"):
    """Model bilgi kartı — sade."""
    mape = metrics.get("mape", 0)
    status_class = "status-active" if mape < 12 else "status-warning" if mape < 15 else "status-danger"
    if model_type == "catboost":
        model_name = "CatBoost Regressor"
    elif model_type == "lightgbm":
        model_name = "LightGBM Regressor"
    else:
        model_name = "Ensemble Hibrit (CatBoost + LightGBM)"
        
    if forecast_method == "recursive":
        badge_html = '<span style="background: rgba(16, 185, 129, 0.12); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); padding: 2px 8px; border-radius: 4px; font-size: 0.68rem; font-family: \'JetBrains Mono\', monospace; margin-left: 8px; font-weight: 500;">[12:30 KAPI KAPANIŞI UYUMLU: ÖZYİNELEMELİ]</span>'
    else:
        badge_html = '<span style="background: rgba(59, 130, 246, 0.12); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); padding: 2px 8px; border-radius: 4px; font-size: 0.68rem; font-family: \'JetBrains Mono\', monospace; margin-left: 8px; font-weight: 500;">[STANDART: DOĞRUDAN ÇIKARIM]</span>'
    
    render_html(f"""
    <div class="info-card" style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="color: #6b7280; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.08em; font-family: Inter, sans-serif;">
                <span class="{status_class} status-indicator"></span> Aktif Model & Mimari {badge_html}
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
    """)


def render_risk_indicator(risk_level: str, risk_color: str):
    """Risk seviyesi göstergesi — sade."""
    color_map = {
        "DÜŞÜK": "#22c55e",
        "ORTA": "#eab308",
        "YÜKSEK": "#f97316",
        "KRİTİK": "#ef4444",
    }
    c = color_map.get(risk_level, "#6b7280")
    
    render_html(f"""
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
    """)


def render_trading_summary(metrics: dict):
    """Trading özet tablosu — sade."""
    total_pnl = metrics.get("total_pnl", 0)
    pnl_color = "#22c55e" if total_pnl >= 0 else "#ef4444"
    
    render_html(f"""
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
    """)


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
        
    # Güncel saat verisi (varsa o saat, yoksa son satır)
    cur_hour_mask = df_day["datetime"].dt.hour == hour if len(df_day) > 0 else []
    if len(df_day) > 0 and any(cur_hour_mask):
        last_ptf = float(df_day[cur_hour_mask]["ptf"].iloc[0])
        last_smf = float(df_day[cur_hour_mask]["smf"].iloc[0]) if "smf" in df_day.columns else last_ptf - 68.0
    else:
        last_ptf = float(df_day["ptf"].iloc[-1]) if len(df_day) > 0 else 2850.0
        last_smf = float(df_day["smf"].iloc[-1]) if ("smf" in df_day.columns and len(df_day) > 0) else last_ptf - 68.0
        
    base_load = float(df_day["ptf"].mean()) if len(df_day) > 0 else 2750.0
    
    if "hour" in df_day.columns:
        peak_mask = (df_day["hour"] >= 8) & (df_day["hour"] <= 20)
    else:
        peak_mask = (df_day["datetime"].dt.hour >= 8) & (df_day["datetime"].dt.hour <= 20)
        
    peak_df = df_day[peak_mask]
    peak_load = float(peak_df["ptf"].mean()) if len(peak_df) > 0 else base_load * 1.15
    
    spread_val = last_ptf - last_smf
    if spread_val > 50:
        sys_dir = "ENERJİ FAZLASI (PTF > SMF)"
    elif spread_val < -50:
        sys_dir = "ENERJİ AÇIĞI (PTF < SMF)"
    else:
        sys_dir = "DENGEDE"
        
    # Veri setinin tarihi bugün mü kontrolü (Canlı API vs Tarihsel Veri)
    today_date = now.date()
    df_date = df_day["datetime"].dt.date.iloc[0] if len(df_day) > 0 else today_date
    is_live = (df_date == today_date)
    
    if is_live:
        mode_label = "CANLI PIYASA"
    else:
        mode_label = f"TARİHSEL SİMÜLASYON [{df_date.strftime('%d.%m.%Y')}]"
        
    selected_hour_str = f"{hour:02d}:00"
    
    from src.ui.styles import get_ticker_bar_html, render_html
    render_html(get_ticker_bar_html(
        tsi_time_str=tsi_time_str,
        session_name=session_name,
        last_ptf=last_ptf,
        base_load=base_load,
        peak_load=peak_load,
        spread_val=spread_val,
        system_direction=sys_dir,
        mode_label=mode_label,
        is_live=is_live,
        selected_hour_str=selected_hour_str,
    ))


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
    
    selected_page = st.radio(
        "Navigasyon",
        options=pages,
        index=0,
        horizontal=True,
        label_visibility="collapsed",
        key="app_navbar_selection",
    )
    
    render_html(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(20, 26, 38, 0.7); border: 1px solid rgba(59, 130, 246, 0.2); border-left: 4px solid #3b82f6; border-radius: 6px; padding: 9px 16px; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="color: #64748b; font-size: 0.74rem; text-transform: uppercase; font-weight: 700; letter-spacing: 0.08em; font-family: 'JetBrains Mono', monospace;">AKTİF ÇALIŞMA ALANI:</span>
            <span style="color: #60a5fa; font-size: 0.88rem; font-weight: 600; font-family: 'Inter', sans-serif;">{selected_page}</span>
        </div>
        <div style="font-size: 0.72rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace;">
            EPİAŞ GÖP & DGP ALGORİTMİK TERMİNAL
        </div>
    </div>
    """)
    
    return selected_page


def render_home_page(summary: dict, model_metrics: dict, trading_metrics: dict):
    """Sisteme girişte kullanıcıyı karşılayan Proje Ana Sayfası & Genel Bakış."""
    render_html("""
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
    """)
    
    # ─── Hızlı İstatistik Kartları ───
    render_html(get_section_header_html("Sistem Performans Özeti", "Güncel model doğrulama metrikleri ve simülasyon sonuçları"))
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
    
    render_html("<div style='height:12px;'></div>")
    
    # ─── Proje Mimarisi & Temel Modüller ───
    render_html(get_section_header_html("Terminal Çalışma Alanları", "Üst navigasyon menüsünden dilediğiniz modüle geçiş yapabilirsiniz"))
    
    m1, m2, m3 = st.columns(3)
    with m1:
        render_html("""
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
        """)
        
    with m2:
        render_html("""
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
        """)
        
    with m3:
        render_html("""
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
        """)
        
    render_html("<div style='height:12px;'></div>")
    
    # ─── Hızlı Başlangıç Rehberi ───
    render_html("""
    <div style="background: rgba(20, 26, 38, 0.7); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 10px; padding: 18px 22px;">
        <div style="color:#f8fafc; font-size:0.95rem; font-weight:600; margin-bottom:10px; font-family:'Inter', sans-serif;">Hızlı Kullanım Talimatı</div>
        <div style="color:#94a3b8; font-size:0.84rem; line-height:1.7; font-family:'Inter', sans-serif;">
            1. <b>[02] Fiyat Tahmini:</b> 24 saatlik fiyat eğrisini inceleyin. Farenizle grafiğe sürükleme yaparak istediğiniz saat dilimine yakınlaşabilirsiniz.<br>
            2. <b>[03] Model Kıyaslama:</b> CatBoost, LightGBM ve Ensemble modellerinin tahminlerini yan yana karşılaştırın.<br>
            3. <b>[04] Trading Masası:</b> Sol panelden alım-satım eşiğini ve pozisyon hacmini güncelleyerek kârlılık eğrisini test edin.<br>
            4. <b>[06] Saatlik Profil & Isı Haritası:</b> Günün saatleri ve haftanın günleri bazında elektrik fiyatlarının yoğunlaştığı tepe saatleri analiz edin.
        </div>
    </div>
    """)


def render_documentation_page():
    """Kullanım rehberi ve EPİAŞ piyasa sözlüğü."""
    render_html("""
    <div style="margin-bottom: 24px;">
        <h2 style="color:#f3f4f6; font-size:1.35rem; font-weight:700; margin-bottom:4px;">Sistem Rehberi & Enerji Piyasası Dokümantasyonu</h2>
        <div style="color:#9ca3af; font-size:0.84rem;">EPİAŞ Gün Öncesi Piyasası (GÖP), yapay zeka model mimarisi ve karar destek mekanizmaları</div>
    </div>
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        render_html("""
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
        """)
        
    with col2:
        render_html("""
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
                    <li><b>MAPE (Mean Absolute Percentage Error):</b> Ortalama yüzde sapma. Hedef: &lt; %12 (Terminal başarımı: ~%4.7 - %4.8).</li>
                    <li><b>Yön Doğruluğu (Directional Accuracy):</b> Fiyatın yukarı/aşağı yön tahmin başarısı. Hedef: &gt; %70 (Terminal: ~%76 - %77).</li>
                    <li><b>Çıkarım Hızı:</b> 24 saatlik fiyat çıkarımı &lt; 500 ms (Terminal hızı: ~4.5 ms).</li>
                    <li><b>Maksimum Drawdown:</b> Backtest'teki en büyük tepe-dip sermaye kaybı yüzdesi.</li>
                </ul>
            </div>
        </div>
        """)


def render_session_schedule_table():
    """EPİAŞ resmi gün öncesi piyasa seans takvimi tablosu."""
    data = [
        {"Saat (TSI)": "10:30 - 12:30", "Seans Adı": "GÖP Teklif Verme Süreci", "Açıklama": "Piyasa katılımcıları 24 saat için alış/satış tekliflerini sisteme girer.", "Durum": "TEKLİF AÇIK"},
        {"Saat (TSI)": "12:30", "Seans Adı": "GÖP Kapı Kapanışı (Gate Closure)", "Açıklama": "Teklif girişi kesin olarak sona erer, EUPAS algoritması başlar.", "Durum": "KAPI KAPALI"},
        {"Saat (TSI)": "13:30", "Seans Adı": "Geçici Sonuçlar & İtiraz", "Açıklama": "İlk piyasa takas fiyatları yayımlanır, katılımcı itiraz penceresi açılır.", "Durum": "KONTROL"},
        {"Saat (TSI)": "14:00", "Seans Adı": "Kesinleşen PTF & Eşleşme İlanı", "Açıklama": "Yarının kesinleşen 24 saatlik referans fiyatı kamuoyuna duyurulur.", "Durum": "KESİNLEŞTİ"},
        {"Saat (TSI)": "18:00 - T-1h", "Seans Adı": "Gün İçi Piyasası (GİP)", "Açıklama": "Fiziki teslimat öncesi 1 saat kalana kadar portföy dengeleme işlemleri.", "Durum": "CANLI AKTİF"},
    ]
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)


def render_24h_schedule_table(df_day: pd.DataFrame):
    """24 saatlik detaylı fiyat, tahmin, sapma ve piyasa bloku tablosu."""
    if len(df_day) == 0:
        return
    
    rows = []
    for _, row in df_day.iterrows():
        dt = row["datetime"]
        hour = dt.hour
        actual = float(row["ptf"])
        pred = float(row.get("predicted_ptf", actual))
        diff = pred - actual
        diff_pct = (diff / (actual + 1e-6)) * 100
        
        if 17 <= hour <= 21:
            block = "[PUANT]"
        elif 8 <= hour < 17:
            block = "[GÜNDÜZ]"
        else:
            block = "[GECE]"
            
        rows.append({
            "Saat": f"{hour:02d}:00",
            "Blok": block,
            "Tahmin PTF (TL)": f"{pred:,.0f}",
            "Gerçek PTF (TL)": f"{actual:,.0f}",
            "Sapma (TL)": f"{diff:+,.0f}",
            "Hata (%)": f"%{abs(diff_pct):.2f}",
            "Güven Alt (TL)": f"{row.get('lower_bound', pred - 40):,.0f}",
            "Güven Üst (TL)": f"{row.get('upper_bound', pred + 40):,.0f}",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=260)


def render_imbalance_calculator(current_ptf: float = 2850.0, current_smf: float = 2710.0):
    """İnteraktif EPİAŞ dengesizlik maliyeti hesaplayıcı."""
    render_html(get_section_header_html("İnteraktif Dengesizlik Maliyeti Simülatörü", "Portföy sapmasında EPİAŞ ceza katsayıları ile net maliyet hesabı"))
    c1, c2, c3 = st.columns([1.2, 1.4, 1.4])
    with c1:
        dev_mwh = st.number_input("Dengesizlik Hacmi (MWh)", min_value=1.0, max_value=500.0, value=10.0, step=5.0)
    with c2:
        dev_type = st.selectbox("Dengesizlik Yönü", options=["Enerji Açığı (Eksik Üretim / Fazla Tüketim)", "Enerji Fazlası (Fazla Üretim / Eksik Tüketim)"])
    
    if "Açığı" in dev_type:
        penalty_rate = max(current_ptf, current_smf) * 1.03
        total_cost = dev_mwh * penalty_rate
        pen_text = f"Birim Ceza: {penalty_rate:,.1f} TL/MWh (max(PTF, SMF) x 1.03)"
        res_color = "#ef4444"
        badge_text = "ÖDENECEK CEZA"
    else:
        penalty_rate = min(current_ptf, current_smf) * 0.97
        total_cost = dev_mwh * penalty_rate
        pen_text = f"Birim Gelir: {penalty_rate:,.1f} TL/MWh (min(PTF, SMF) x 0.97)"
        res_color = "#22c55e"
        badge_text = "ALINACAK GELİR"
        
    with c3:
        render_html(f"""
        <div style="background: rgba(20,26,38,0.85); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 12px 16px; font-family:'JetBrains Mono',monospace;">
            <div style="color:#64748b; font-size:0.68rem; text-transform:uppercase;">NET FATURA TUTARI ({badge_text}):</div>
            <div style="color:{res_color}; font-size:1.35rem; font-weight:700; margin-top:2px;">{total_cost:,.0f} TL</div>
            <div style="color:#94a3b8; font-size:0.68rem; margin-top:4px;">{pen_text}</div>
        </div>
        """)
