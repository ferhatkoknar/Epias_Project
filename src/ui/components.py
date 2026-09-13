"""
UI Bileşenleri — Kurumsal ve Profesyonel
Sade KPI kartları, temiz sidebar, emoji yok.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


def render_sidebar() -> dict:
    """Sol panel filtre ve kontrol bileşenleri."""
    with st.sidebar:
        st.markdown("### Kontrol Paneli")
        st.markdown("---")
        
        st.markdown("##### Tahmin Parametreleri")
        target_date = st.date_input(
            "Hedef Tarih",
            value=datetime.now().date() + timedelta(days=1),
            help="Tahmin yapılacak gün"
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
                <div style="color:#6b7280;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.08em;font-family:Inter,sans-serif;">Profit Factor</div>
                <div style="color:#e5e7eb;font-size:1.1rem;font-weight:600;font-family:JetBrains Mono,monospace;margin-top:4px;">{metrics.get('profit_factor',0):.2f}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
