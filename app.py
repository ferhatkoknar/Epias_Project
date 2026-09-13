"""
EPİAŞ GÖP PTF Tahmin & Trading Terminali
Ana Streamlit uygulaması — giriş noktası.
"""

import sys
import logging
from pathlib import Path

# Proje kök dizinini path'e ekle
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import numpy as np

from src.ui.styles import get_premium_css, get_header_html, get_section_header_html
from src.ui.components import (
    render_sidebar, render_kpi_cards, render_model_info,
    render_risk_indicator, render_trading_summary,
    render_navbar, render_documentation_page, render_home_page,
)
from src.ui.charts import (
    create_ptf_forecast_chart, create_error_distribution_chart,
    create_pnl_chart, create_spread_risk_chart, create_feature_importance_chart,
)
from src.ui.export import export_predictions_csv, generate_technical_report
from src.data.fetcher import fetch_all_market_data
from src.data.cleaner import clean_market_data
from src.features.time_features import create_time_features, get_feature_columns
from src.features.market_features import create_market_features
from src.models.predictor import predict_24h, generate_forecast_summary
from src.models.evaluator import evaluate_model, evaluate_hourly, calculate_error_distribution
from src.trading.simulator import run_backtest, calculate_trading_metrics
from src.trading.risk import calculate_spread_risk, get_risk_summary

# ─── Logging ───
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Sayfa Ayarları ───
st.set_page_config(
    page_title="EPİAŞ PTF Tahmin Terminali",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS enjekte et
st.markdown(get_premium_css(), unsafe_allow_html=True)


# ─── Veri Yükleme (Cache) ───
@st.cache_data(ttl=3600, show_spinner=False)
def load_and_prepare_data():
    """Veriyi yükler, temizler ve öznitelikleri üretir (bugünün güncel tarihine kadar)."""
    with st.spinner("Güncel piyasa verileri hazırlanıyor..."):
        raw_df = fetch_all_market_data(start_date="2024-01-01")
        clean_df = clean_market_data(raw_df)
        featured_df = create_time_features(clean_df)
        featured_df = create_market_features(featured_df)
        return clean_df, featured_df


@st.cache_resource(show_spinner=False)
def get_cached_model_and_predictions(model_type: str, data_len: int):
    """Modeli 1 kez eğitip RAM'de önbelleğe alır. Sayfa geçişlerinde asla yeniden eğitmez!"""
    featured_df = st.session_state.get("featured_df")
    feature_cols = get_feature_columns(featured_df)
    test_size = 30 * 24
    test_df = featured_df.iloc[-test_size:]
    train_df = featured_df.iloc[:-test_size]
    
    val_size = max(1, int(len(train_df) * 0.1))
    X_val = train_df[feature_cols].iloc[-val_size:]
    y_val = train_df["ptf"].iloc[-val_size:]
    X_train = train_df[feature_cols].iloc[:-val_size]
    y_train = train_df["ptf"].iloc[:-val_size]
    
    from src.models.trainer import train_model, get_feature_importance
    model = train_model(X_train, y_train, X_val, y_val, model_type=model_type)
    test_predictions = model.predict(test_df[feature_cols])
    model_metrics = evaluate_model(test_df["ptf"].values, test_predictions)
    fi_df = get_feature_importance(model, feature_cols, model_type)
    return model, test_predictions, model_metrics, fi_df


# ─── Ana Uygulama ───
def main():
    # Başlık
    st.markdown(get_header_html(), unsafe_allow_html=True)
    
    # Veri yükle
    try:
        clean_df, featured_df = load_and_prepare_data()
        st.session_state["featured_df"] = featured_df
    except Exception as e:
        st.error(f"Veri yükleme hatası: {e}")
        st.stop()
    
    feature_cols = get_feature_columns(featured_df)
    
    # Test verisi ayır (son 30 gün)
    test_size = 30 * 24
    test_df = featured_df.iloc[-test_size:].copy()
    
    # Mevcut test tarih aralığı
    test_dates = test_df["datetime"].dt.date.unique()
    min_test_date = test_dates.min()
    max_test_date = test_dates.max()
    
    # Sidebar (tarih sınırları ile)
    params = render_sidebar(
        min_date=min_test_date,
        max_date=max_test_date,
        default_date=max_test_date,
    )
    
    # Modeli önbellekten al (her tıklamada sıfırdan eğitilmez!)
    with st.spinner("Model optimize ediliyor..."):
        model, test_predictions, model_metrics, fi_df = get_cached_model_and_predictions(
            params["model_type"], len(featured_df)
        )
    
    # Test setine tahminleri ekle
    test_df["predicted_ptf"] = test_predictions
    test_df["lower_bound"] = test_predictions - 1.96 * model_metrics.get("rmse", 50)
    test_df["upper_bound"] = test_predictions + 1.96 * model_metrics.get("rmse", 50)
    
    # Seçili gün için tahmin ve metrikler
    selected_date = params["target_date"]
    
    if "active_date" not in st.session_state or st.session_state.get("prev_target_date") != selected_date:
        st.session_state["active_date"] = selected_date
        st.session_state["prev_target_date"] = selected_date
    
    active_date = st.session_state["active_date"]
    day_mask = test_df["datetime"].dt.date == active_date
    day_data = test_df[day_mask]
    
    if len(day_data) == 0:
        active_date = max_test_date
        st.session_state["active_date"] = active_date
        day_data = test_df[test_df["datetime"].dt.date == active_date]
    
    forecast_df = day_data[["datetime", "predicted_ptf", "lower_bound", "upper_bound"]].copy()
    forecast_summary = generate_forecast_summary(forecast_df)
    day_metrics = evaluate_model(day_data["ptf"].values, day_data["predicted_ptf"].values)
    
    # Backtest hesaplaması (tüm sayfalar ve export için hazır)
    backtest_df = run_backtest(
        actual_ptf=test_df["ptf"].values,
        predicted_ptf=test_predictions,
        datetimes=test_df["datetime"],
        threshold_tl=params["threshold_tl"],
        position_mwh=params["position_mwh"],
        commission_rate=0.001,
        strategy=params["strategy"],
        risk_coefficient=params["risk_coefficient"],
    )
    trading_metrics = calculate_trading_metrics(backtest_df)
    
    # ─── Üst Navbar ───
    current_page = render_navbar()
    
    # ══════════════════════════════════════════════════════════
    # SAYFA 0: 🏠 Ana Sayfa (Proje Özeti & Giriş) — VARSAYILAN
    # ══════════════════════════════════════════════════════════
    if current_page == "🏠 Ana Sayfa (Proje Özeti & Giriş)":
        render_home_page(forecast_summary, model_metrics, trading_metrics)

    # ══════════════════════════════════════════════════════════
    # SAYFA 1: ⚡ Fiyat Tahmini (Canlı PTF Projeksiyonu)
    # ══════════════════════════════════════════════════════════
    elif current_page == "⚡ Fiyat Tahmini (Canlı PTF Projeksiyonu)":
        # KPI Kartları (Seçili güne göre dinamik)
        render_kpi_cards(forecast_summary, day_metrics)
        st.markdown("", unsafe_allow_html=True)
        render_model_info(params["model_type"], model_metrics)
        
        st.markdown(get_section_header_html(
            "PTF Fiyat Projeksiyonu & Geçmiş Analizi",
            f"İncelenen Gün: {active_date.strftime('%d %B %Y')} — Gerçekleşen vs Model Tahmini"
        ), unsafe_allow_html=True)
        
        # ─── Tarih & Aralık Gezinme Çubuğu ───
        c_nav_prev, c_nav_date, c_nav_next, c_nav_range = st.columns([1.2, 2.2, 1.2, 2.4])
        
        curr_idx = list(test_dates).index(active_date) if active_date in test_dates else len(test_dates) - 1
        
        with c_nav_prev:
            if st.button("◀ Önceki Gün", use_container_width=True, disabled=(curr_idx == 0)):
                st.session_state["active_date"] = test_dates[curr_idx - 1]
                st.rerun()
                
        with c_nav_date:
            date_selection = st.selectbox(
                "Tarih Seç",
                options=list(test_dates),
                index=curr_idx,
                format_func=lambda d: d.strftime("%d %B %Y (%A)"),
                label_visibility="collapsed",
            )
            if date_selection != active_date:
                st.session_state["active_date"] = date_selection
                st.rerun()
                
        with c_nav_next:
            if st.button("Sonraki Gün ▶", use_container_width=True, disabled=(curr_idx >= len(test_dates) - 1)):
                st.session_state["active_date"] = test_dates[curr_idx + 1]
                st.rerun()
                
        with c_nav_range:
            view_mode = st.selectbox(
                "Görünüm Aralığı",
                options=["Seçili Gün (24 Saat)", "Son 3 Gün", "Son 7 Gün", "Tüm Test Dönemi (30 Gün)"],
                index=0,
                label_visibility="collapsed",
            )
        
        # Görünüm moduna göre veri filtreleme
        if view_mode == "Seçili Gün (24 Saat)":
            plot_actual = test_df[test_df["datetime"].dt.date == active_date]
            plot_forecast = forecast_df
            chart_title = f"{active_date.strftime('%d %B %Y')} — 24 Saatlik PTF Projeksiyonu"
        elif view_mode == "Son 3 Gün":
            end_dt = pd.Timestamp(active_date) + pd.Timedelta(days=1)
            start_dt = end_dt - pd.Timedelta(days=3)
            sub = test_df[(test_df["datetime"] >= start_dt) & (test_df["datetime"] < end_dt)]
            plot_actual = sub
            plot_forecast = sub[["datetime", "predicted_ptf", "lower_bound", "upper_bound"]]
            chart_title = f"Son 3 Günlük Fiyat Hareketi ({start_dt.strftime('%d %b')} - {active_date.strftime('%d %b')})"
        elif view_mode == "Son 7 Gün":
            end_dt = pd.Timestamp(active_date) + pd.Timedelta(days=1)
            start_dt = end_dt - pd.Timedelta(days=7)
            sub = test_df[(test_df["datetime"] >= start_dt) & (test_df["datetime"] < end_dt)]
            plot_actual = sub
            plot_forecast = sub[["datetime", "predicted_ptf", "lower_bound", "upper_bound"]]
            chart_title = f"Son 7 Günlük Fiyat Hareketi ({start_dt.strftime('%d %b')} - {active_date.strftime('%d %b')})"
        else:
            plot_actual = test_df
            plot_forecast = test_df[["datetime", "predicted_ptf", "lower_bound", "upper_bound"]]
            chart_title = "Tüm Test Dönemi (30 Günlük) PTF Fiyat Eğrisi & Tahminler"
        
        # Yakınlaştırma (zoom) aktif Plotly konfigürasyonu
        fig_forecast = create_ptf_forecast_chart(
            plot_actual,
            plot_forecast,
            title=chart_title,
            show_rangeslider=True,
        )
        st.plotly_chart(
            fig_forecast, 
            use_container_width=True, 
            config={
                "scrollZoom": True,
                "displayModeBar": True,
                "displaylogo": False,
                "modeBarButtonsToAdd": ["zoom2d", "pan2d", "zoomIn2d", "zoomOut2d", "autoScale2d", "resetScale2d"],
            }
        )
        
        # Hata analizi
        col_left, col_right = st.columns([1.1, 0.9])
        with col_left:
            st.markdown(get_section_header_html("Tahmin Hata Analizi"), unsafe_allow_html=True)
            hours = plot_actual["datetime"].dt.hour.values
            fig_err = create_error_distribution_chart(
                plot_actual["ptf"].values, plot_forecast["predicted_ptf"].values, hours
            )
            st.plotly_chart(fig_err, use_container_width=True, config={"displayModeBar": False})
        
        with col_right:
            st.markdown(get_section_header_html("Piyasa Riski & Spread"), unsafe_allow_html=True)
            if "smf" in plot_actual.columns:
                risk_df = calculate_spread_risk(
                    plot_actual["ptf"].values,
                    plot_actual["smf"].values,
                    plot_forecast["predicted_ptf"].values,
                )
                risk_summary = get_risk_summary(risk_df)
                render_risk_indicator(risk_summary["current_risk"], risk_summary["current_color"])
                fig_spread = create_spread_risk_chart(risk_df.tail(168))
                st.plotly_chart(fig_spread, use_container_width=True, config={"displayModeBar": False})

    # ══════════════════════════════════════════════════════════
    # SAYFA 2: 📈 Trading Masası (P&L & Portföy Backtest)
    # ══════════════════════════════════════════════════════════
    elif current_page == "📈 Trading Masası (P&L & Portföy Backtest)":
        st.markdown(get_section_header_html(
            "Enerji Trading Masası & Backtest Simülasyonu",
            "Model sinyallerine göre geçmişe dönük kâr/zarar ve portföy risk performansı"
        ), unsafe_allow_html=True)
        
        render_trading_summary(trading_metrics)
        st.markdown("", unsafe_allow_html=True)
        
        # P&L grafiği
        fig_pnl = create_pnl_chart(backtest_df)
        st.plotly_chart(fig_pnl, use_container_width=True, config={"displayModeBar": False})
        
        # İşlem detay defteri
        st.markdown(get_section_header_html("İşlem Defteri (Trade Log)"), unsafe_allow_html=True)
        trades_only = backtest_df[backtest_df["signal"] != 0][
            ["datetime", "actual_ptf", "predicted_ptf", "signal", "position_mwh", "pnl", "cumulative_pnl"]
        ].copy()
        trades_only["signal"] = trades_only["signal"].map({1: "🟢 ALIŞ", -1: "🔴 SATIŞ"})
        trades_only = trades_only.rename(columns={
            "datetime": "Tarih/Saat",
            "actual_ptf": "Gerçek PTF (TL)",
            "predicted_ptf": "Tahmin PTF (TL)",
            "signal": "İşlem Yönü",
            "position_mwh": "Hacim (MWh)",
            "pnl": "İşlem P&L (TL)",
            "cumulative_pnl": "Kümülatif Kâr (TL)",
        })
        st.dataframe(trades_only.tail(100), use_container_width=True, hide_index=True, height=360)

    # ══════════════════════════════════════════════════════════
    # SAYFA 3: 🧠 AI Laboratuvarı (CatBoost & Metrikler)
    # ══════════════════════════════════════════════════════════
    elif current_page == "🧠 AI Laboratuvarı (CatBoost & Metrikler)":
        st.markdown(get_section_header_html(
            "Yapay Zeka & Model Laboratuvarı",
            "Algoritma başarı metrikleri, öznitelik önemi ve hata analiz matrisi"
        ), unsafe_allow_html=True)
        
        col_a, col_b = st.columns([1, 1])
        
        with col_a:
            st.markdown(get_section_header_html("Model Doğrulama Metrikleri"), unsafe_allow_html=True)
            metric_data = {
                "Metrik": ["MAPE", "RMSE", "MAE", "R²", "Yön Doğruluğu", "Maks. Hata"],
                "Değer": [
                    f"%{model_metrics['mape']:.2f}",
                    f"{model_metrics['rmse']:,.1f} TL",
                    f"{model_metrics['mae']:,.1f} TL",
                    f"{model_metrics['r2']:.4f}",
                    f"%{model_metrics['directional_accuracy']:.1f}",
                    f"{model_metrics['max_error']:,.1f} TL",
                ],
                "SRS Kabul Eşiği": ["< %12.0", "—", "—", "—", "> %70.0", "—"],
                "Sonuç": [
                    "✅ BAŞARILI" if model_metrics["mape"] < 12 else "❌ AŞILDI",
                    "—", "—", "—",
                    "✅ BAŞARILI" if model_metrics["directional_accuracy"] > 70 else "⚠️ GELİŞTİRİLMELİ",
                    "—",
                ],
            }
            st.dataframe(pd.DataFrame(metric_data), use_container_width=True, hide_index=True)
            
            error_dist = calculate_error_distribution(test_df["ptf"].values, test_predictions)
            st.markdown(get_section_header_html("Hata Dağılım İstatistikleri"), unsafe_allow_html=True)
            dist_data = {
                "İstatistik": ["Ortalama Hata", "Standart Sapma", "Medyan (P50)", "P75", "P95", "%5 Bant İçi", "%10 Bant İçi"],
                "Değer": [
                    f"{error_dist['error_mean']:,.0f} TL",
                    f"{error_dist['error_std']:,.0f} TL",
                    f"{error_dist['abs_error_p50']:,.0f} TL",
                    f"{error_dist['abs_error_p75']:,.0f} TL",
                    f"{error_dist['abs_error_p95']:,.0f} TL",
                    f"%{error_dist['pct_within_5pct']:.1f}",
                    f"%{error_dist['pct_within_10pct']:.1f}",
                ],
            }
            st.dataframe(pd.DataFrame(dist_data), use_container_width=True, hide_index=True)
            
        with col_b:
            st.markdown(get_section_header_html("Öznitelik Önemi (Feature Importance)"), unsafe_allow_html=True)
            fig_fi = create_feature_importance_chart(fi_df)
            st.plotly_chart(fig_fi, use_container_width=True, config={"displayModeBar": False})
            
            st.markdown(get_section_header_html("24 Saatlik Performans Dökümü"), unsafe_allow_html=True)
            hourly_metrics = evaluate_hourly(
                test_df["ptf"].values, test_predictions, test_df["datetime"].dt.hour.values
            )
            hourly_display = hourly_metrics[["hour", "mape", "rmse", "bias"]].copy()
            hourly_display.columns = ["Saat", "MAPE (%)", "RMSE (TL)", "Bias (TL)"]
            hourly_display["MAPE (%)"] = hourly_display["MAPE (%)"].round(2)
            hourly_display["RMSE (TL)"] = hourly_display["RMSE (TL)"].round(0)
            hourly_display["Bias (TL)"] = hourly_display["Bias (TL)"].round(0)
            st.dataframe(hourly_display, use_container_width=True, hide_index=True, height=280)

    # ══════════════════════════════════════════════════════════
    # SAYFA 4: 📊 Risk Radarı (SMF & Spread Derinliği)
    # ══════════════════════════════════════════════════════════
    elif current_page == "📊 Risk Radarı (SMF & Spread Derinliği)":
        st.markdown(get_section_header_html(
            "Piyasa Derinliği & Dengesizlik Risk Radarı",
            "PTF vs SMF spread analizi ve sistem marjinal dengesizlik riskleri"
        ), unsafe_allow_html=True)
        
        if "smf" in test_df.columns:
            all_risk_df = calculate_spread_risk(
                test_df["ptf"].values,
                test_df["smf"].values,
                test_predictions,
            )
            risk_summary = get_risk_summary(all_risk_df)
            
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            with col_r1:
                st.metric("Ortalama Spread", f"{risk_summary['avg_spread']:.1f} TL")
            with col_r2:
                st.metric("Maksimum Spread", f"{risk_summary['max_spread']:.1f} TL")
            with col_r3:
                st.metric("Volatilite (Std)", f"{risk_summary['std_spread']:.1f} TL")
            with col_r4:
                st.metric("Yüksek Risk Oranı", f"%{risk_summary['pct_high_risk']:.1f}")
            
            st.markdown("", unsafe_allow_html=True)
            fig_spread_all = create_spread_risk_chart(all_risk_df)
            st.plotly_chart(fig_spread_all, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("SMF verisi bulunamadı.")

    # ══════════════════════════════════════════════════════════
    # SAYFA 5: ℹ️ Proje Rehberi (EPİAŞ Sözlüğü & Mimari)
    # ══════════════════════════════════════════════════════════
    elif current_page == "ℹ️ Proje Rehberi (EPİAŞ Sözlüğü & Mimari)":
        render_documentation_page()

    # ─── Dışa Aktarma ───
    if params["export_csv"]:
        csv_data = export_predictions_csv(forecast_df, test_df, model_metrics)
        st.download_button(
            label="CSV Dosyasını İndir",
            data=csv_data,
            file_name=f"ptf_tahmin_{params['target_date']}.csv",
            mime="text/csv",
        )
    
    if params["export_report"]:
        report = generate_technical_report(
            model_metrics,
            trading_metrics,
            forecast_summary,
            params["model_type"],
        )
        st.download_button(
            label="Raporu İndir",
            data=report.encode("utf-8"),
            file_name=f"teknik_rapor_{params['target_date']}.md",
            mime="text/markdown",
        )


if __name__ == "__main__":
    main()
