"""
EPİAŞ GÖP PTF Tahmin & Trading Terminali
Ana Streamlit uygulaması — kurumsal enerji masası terminali.
"""

import sys
import time
import logging
from datetime import datetime
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
    render_market_ticker_bar,
)
from src.ui.charts import (
    create_ptf_forecast_chart, create_error_distribution_chart,
    create_pnl_chart, create_spread_risk_chart, create_feature_importance_chart,
    create_hourly_heatmap, create_base_peak_chart,
    create_multi_model_comparison_chart, create_stress_test_chart,
)
from src.ui.export import export_predictions_csv, generate_technical_report
from src.data.fetcher import fetch_all_market_data
from src.data.cleaner import clean_market_data
from src.features.time_features import create_time_features, get_feature_columns
from src.features.market_features import create_market_features
from src.models.predictor import generate_forecast_summary
from src.models.evaluator import evaluate_model, evaluate_hourly, calculate_error_distribution
from src.trading.simulator import run_backtest, calculate_trading_metrics, simulate_market_shock
from src.trading.risk import calculate_spread_risk, get_risk_summary

# ─── Logging ───
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Sayfa Ayarları (Sıfır Emoji) ───
st.set_page_config(
    page_title="EPİAŞ PTF Tahmin & Trading Terminali",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS enjekte et
st.markdown(get_premium_css(), unsafe_allow_html=True)


# ─── Veri Yükleme (Cache) ───
@st.cache_data(ttl=3600, show_spinner=False)
def load_and_prepare_data():
    """Veriyi yükler, temizler ve öznitelikleri üretir."""
    with st.spinner("Piyasa verileri yükleniyor ve öznitelikler hesaplanıyor..."):
        raw_df = fetch_all_market_data(start_date="2024-01-01")
        clean_df = clean_market_data(raw_df)
        featured_df = create_time_features(clean_df)
        featured_df = create_market_features(featured_df)
        return clean_df, featured_df


@st.cache_resource(show_spinner=False)
def get_cached_model_suite(data_len: int):
    """
    Tüm modelleri (CatBoost, LightGBM, Ensemble) tek seferde eğitip önbelleğe alır.
    Sayfa ve model geçişlerinde sıfır bekleme süresi sağlar.
    """
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
    X_test = test_df[feature_cols]
    y_test = test_df["ptf"].values
    
    from src.models.trainer import train_model, get_feature_importance, EnsembleModel
    
    # 1. CatBoost
    t0 = time.time()
    cb_model = train_model(X_train, y_train, X_val, y_val, model_type="catboost")
    cb_train_time = time.time() - t0
    
    t0 = time.time()
    cb_preds = cb_model.predict(X_test)
    cb_infer_time = ((time.time() - t0) * 1000) / (len(X_test) / 24)
    cb_metrics = evaluate_model(y_test, cb_preds)
    cb_metrics["train_time_s"] = cb_train_time
    cb_metrics["infer_time_24h_ms"] = cb_infer_time
    cb_fi = get_feature_importance(cb_model, feature_cols, "catboost")
    
    # 2. LightGBM
    t0 = time.time()
    lgb_model = train_model(X_train, y_train, X_val, y_val, model_type="lightgbm")
    lgb_train_time = time.time() - t0
    
    t0 = time.time()
    lgb_preds = lgb_model.predict(X_test)
    lgb_infer_time = ((time.time() - t0) * 1000) / (len(X_test) / 24)
    lgb_metrics = evaluate_model(y_test, lgb_preds)
    lgb_metrics["train_time_s"] = lgb_train_time
    lgb_metrics["infer_time_24h_ms"] = lgb_infer_time
    lgb_fi = get_feature_importance(lgb_model, feature_cols, "lightgbm")
    
    # 3. Ensemble (Ağırlıklı %50 CB + %50 LGB)
    ens_model = EnsembleModel(cb_model, lgb_model, weights=(0.5, 0.5))
    t0 = time.time()
    ens_preds = ens_model.predict(X_test)
    ens_infer_time = ((time.time() - t0) * 1000) / (len(X_test) / 24)
    ens_metrics = evaluate_model(y_test, ens_preds)
    ens_metrics["train_time_s"] = cb_train_time + lgb_train_time
    ens_metrics["infer_time_24h_ms"] = ens_infer_time
    ens_fi = get_feature_importance(ens_model, feature_cols, "ensemble")
    
    return {
        "catboost": (cb_model, cb_preds, cb_metrics, cb_fi),
        "lightgbm": (lgb_model, lgb_preds, lgb_metrics, lgb_fi),
        "ensemble": (ens_model, ens_preds, ens_metrics, ens_fi),
    }


# ─── Ana Uygulama ───
def main():
    # Terminal Üst Başlığı
    st.markdown(get_header_html(), unsafe_allow_html=True)
    
    # Veri yükle
    try:
        clean_df, featured_df = load_and_prepare_data()
        st.session_state["featured_df"] = featured_df
    except Exception as e:
        st.error(f"Veri yukleme hatasi: {e}")
        st.stop()
    
    feature_cols = get_feature_columns(featured_df)
    
    # Test verisi (son 30 gün = 720 saat)
    test_size = 30 * 24
    test_df = featured_df.iloc[-test_size:].copy()
    
    # Mevcut test tarihleri
    test_dates = test_df["datetime"].dt.date.unique()
    min_test_date = test_dates.min()
    max_test_date = test_dates.max()
    
    # Sidebar
    params = render_sidebar(
        min_date=min_test_date,
        max_date=max_test_date,
        default_date=max_test_date,
    )
    
    # Çoklu model paketini RAM önbelleğinden al
    with st.spinner("Modeller optimize ediliyor..."):
        model_suite = get_cached_model_suite(len(featured_df))
    
    selected_model_type = params["model_type"]
    model, test_predictions, model_metrics, fi_df = model_suite[selected_model_type]
    
    # Tahminleri ve %90 güven aralığını ekle
    test_df["predicted_ptf"] = test_predictions
    test_df["lower_bound"] = test_predictions - 1.96 * model_metrics.get("rmse", 50)
    test_df["upper_bound"] = test_predictions + 1.96 * model_metrics.get("rmse", 50)
    
    # Aktif gün seçimi
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
    
    # Backtest hesaplaması
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
    
    # ─── Canlı Piyasa Ticker & Seans Bantı ───
    render_market_ticker_bar(day_data, model_metrics)
    
    # ─── Üst Navigasyon Menüsü ───
    current_page = render_navbar()
    
    # ══════════════════════════════════════════════════════════
    # MODÜL 1: [01] GENEL BAKIŞ & SEANS ÖZETİ
    # ══════════════════════════════════════════════════════════
    if current_page == "[01] GENEL BAKIŞ & SEANS ÖZETİ":
        render_home_page(forecast_summary, model_metrics, trading_metrics)

    # ══════════════════════════════════════════════════════════
    # MODÜL 2: [02] 24S PTF FİYAT TAHMİNİ
    # ══════════════════════════════════════════════════════════
    elif current_page == "[02] 24S PTF FİYAT TAHMİNİ":
        render_kpi_cards(forecast_summary, day_metrics)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        render_model_info(params["model_type"], model_metrics)
        
        st.markdown(get_section_header_html(
            "PTF Fiyat Projeksiyonu & Geçmiş Analizi",
            f"İncelenen Gün: {active_date.strftime('%d %B %Y')} — Gerçekleşen vs Model Tahmini"
        ), unsafe_allow_html=True)
        
        # Tarih & Aralık Gezinme Çubuğu
        c_nav_prev, c_nav_date, c_nav_next, c_nav_range = st.columns([1.2, 2.2, 1.2, 2.4])
        curr_idx = list(test_dates).index(active_date) if active_date in test_dates else len(test_dates) - 1
        
        with c_nav_prev:
            if st.button("Önceki Gün", use_container_width=True, disabled=(curr_idx == 0)):
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
            if st.button("Sonraki Gün", use_container_width=True, disabled=(curr_idx >= len(test_dates) - 1)):
                st.session_state["active_date"] = test_dates[curr_idx + 1]
                st.rerun()
                
        with c_nav_range:
            view_mode = st.selectbox(
                "Görünüm Aralığı",
                options=["Seçili Gün (24 Saat)", "Son 3 Gün", "Son 7 Gün", "Tüm Test Dönemi (30 Gün)"],
                index=0,
                label_visibility="collapsed",
            )
        
        # Filtreleme
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
        
        # Hata ve risk analizi
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
    # MODÜL 3: [03] MODEL KIYASLAMA & ENSEMBLE
    # ══════════════════════════════════════════════════════════
    elif current_page == "[03] MODEL KIYASLAMA & ENSEMBLE":
        st.markdown(get_section_header_html(
            "Çoklu Model Kıyaslama Laboratuvarı",
            "CatBoost vs LightGBM vs Ensemble (Hibrit) başarım ve gecikme karşılaştırması"
        ), unsafe_allow_html=True)
        
        # Çoklu tahmin grafiği (seçili 24 saat için)
        day_sub = test_df[test_df["datetime"].dt.date == active_date]
        day_indices = day_sub.index - test_df.index[0]
        
        models_day_preds = {
            "CatBoost": model_suite["catboost"][1][day_indices],
            "LightGBM": model_suite["lightgbm"][1][day_indices],
            "Ensemble": model_suite["ensemble"][1][day_indices],
        }
        
        fig_multi = create_multi_model_comparison_chart(
            dates=day_sub["datetime"],
            actual=day_sub["ptf"].values,
            models_dict=models_day_preds,
            height=430,
        )
        st.plotly_chart(fig_multi, use_container_width=True, config={"displayModeBar": False})
        
        # Karşılaştırma tablosu
        st.markdown(get_section_header_html("Test Seti Performans Karşılaştırma Matrisi (30 Günlük)"), unsafe_allow_html=True)
        
        bench_data = []
        for m_name, (m_obj, m_preds, m_metrics, m_fi) in [
            ("CatBoost Regressor", model_suite["catboost"]),
            ("LightGBM Regressor", model_suite["lightgbm"]),
            ("Ensemble (Hibrit)", model_suite["ensemble"]),
        ]:
            bench_data.append({
                "Model Mimarisi": m_name,
                "MAPE (%)": f"%{m_metrics['mape']:.2f}",
                "RMSE (TL)": f"{m_metrics['rmse']:,.1f} TL",
                "MAE (TL)": f"{m_metrics['mae']:,.1f} TL",
                "R² Skoru": f"{m_metrics['r2']:.4f}",
                "Yön Doğruluğu": f"%{m_metrics['directional_accuracy']:.1f}",
                "24s Çıkarım (ms)": f"{m_metrics.get('infer_time_24h_ms', 0):.2f} ms",
                "SRS Uyumluluk": "[KABUL] HEDEFLER SAGLANDI" if m_metrics["mape"] < 12 and m_metrics["directional_accuracy"] > 70 else "[UYARI] GELISTIRILMELI",
            })
            
        st.dataframe(pd.DataFrame(bench_data), use_container_width=True, hide_index=True)
        
        # Öznitelik önemi ve hata dökümü
        c_fi, c_err = st.columns([1, 1])
        with c_fi:
            st.markdown(get_section_header_html(f"Öznitelik Önemi — {selected_model_type.upper()}"), unsafe_allow_html=True)
            fig_fi = create_feature_importance_chart(fi_df, top_n=12)
            st.plotly_chart(fig_fi, use_container_width=True, config={"displayModeBar": False})
            
        with c_err:
            st.markdown(get_section_header_html("Saatlik Doğruluk Dağılımı"), unsafe_allow_html=True)
            hourly_comp = evaluate_hourly(test_df["ptf"].values, test_predictions, test_df["datetime"].dt.hour.values)
            h_disp = hourly_comp[["hour", "mape", "rmse", "bias"]].copy()
            h_disp.columns = ["Saat", "MAPE (%)", "RMSE (TL)", "Sapma / Bias (TL)"]
            h_disp["MAPE (%)"] = h_disp["MAPE (%)"].round(2)
            h_disp["RMSE (TL)"] = h_disp["RMSE (TL)"].round(0)
            h_disp["Sapma / Bias (TL)"] = h_disp["Sapma / Bias (TL)"].round(0)
            st.dataframe(h_disp, use_container_width=True, hide_index=True, height=360)

    # ══════════════════════════════════════════════════════════
    # MODÜL 4: [04] TRADING & P&L SİMÜLATÖRÜ
    # ══════════════════════════════════════════════════════════
    elif current_page == "[04] TRADING & P&L SİMÜLATÖRÜ":
        st.markdown(get_section_header_html(
            "Algoritmik Trading Masası & Stres Testi",
            "PTF fiyat arbitrajı, kümülatif P&L eğrisi ve ekstrem piyasa senaryoları"
        ), unsafe_allow_html=True)
        
        render_trading_summary(trading_metrics)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        
        # P&L Grafiği
        fig_pnl = create_pnl_chart(backtest_df)
        st.plotly_chart(fig_pnl, use_container_width=True, config={"displayModeBar": False})
        
        # Stres Testi Bölümü
        st.markdown(get_section_header_html("Piyasa Stres Testi & Ekstrem Senaryo Simülatörü", "Sistem şoklarında strateji dayanıklılığı"), unsafe_allow_html=True)
        c_st1, c_st2 = st.columns([1, 2])
        with c_st1:
            scenario = st.selectbox(
                "Stres Senaryosu",
                options=[
                    ("gas_spike", "Doğal Gaz Arz Kesintisi (+%25 Puant)"),
                    ("renewable_surge", "Aşırı Yenilenebilir Üretim (-%30 Taban)"),
                    ("volatility_shock", "Volatilite & Jeopolitik Şok (%20 Dalgalanma)"),
                ],
                format_func=lambda x: x[1],
            )
            shock_pct = st.slider("Şok Büyüklüğü (%)", min_value=10, max_value=50, value=25, step=5) / 100.0
            
            shocked_df = simulate_market_shock(backtest_df, shock_type=scenario[0], shock_pct=shock_pct)
            s_metrics = calculate_trading_metrics(shocked_df.rename(columns={"shocked_pnl": "pnl", "shocked_cumulative_pnl": "cumulative_pnl"}))
            
            st.markdown(f"""
            <div style="background: rgba(20,26,38,0.7); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 14px; margin-top: 10px; font-family:'JetBrains Mono',monospace; font-size:0.75rem;">
                <div style="color:#64748b; margin-bottom:4px;">STRES ALTINDA SONUÇ:</div>
                <div style="color:{'#22c55e' if s_metrics['total_pnl']>=0 else '#ef4444'}; font-size:1.1rem; font-weight:700;">{s_metrics['total_pnl']:,.0f} TL</div>
                <div style="color:#94a3b8; margin-top:4px;">Maks. Drawdown: {s_metrics['max_drawdown_pct']:.1f}%</div>
                <div style="color:#94a3b8;">Başarı Oranı: %{s_metrics['win_rate']:.1f}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c_st2:
            fig_stress = create_stress_test_chart(shocked_df, shock_name=scenario[1], height=340)
            st.plotly_chart(fig_stress, use_container_width=True, config={"displayModeBar": False})
            
        # İşlem Defteri (Trade Log)
        st.markdown(get_section_header_html("İşlem Defteri (Trade Execution Log)"), unsafe_allow_html=True)
        trades_only = backtest_df[backtest_df["signal"] != 0][
            ["datetime", "actual_ptf", "predicted_ptf", "signal", "position_mwh", "pnl", "cumulative_pnl"]
        ].copy()
        trades_only["signal"] = trades_only["signal"].map({1: "AL", -1: "SAT"})
        trades_only = trades_only.rename(columns={
            "datetime": "Tarih / Saat",
            "actual_ptf": "Gerçek PTF (TL)",
            "predicted_ptf": "Tahmin PTF (TL)",
            "signal": "İşlem",
            "position_mwh": "Hacim (MWh)",
            "pnl": "Net P&L (TL)",
            "cumulative_pnl": "Kümülatif Kâr (TL)",
        })
        st.dataframe(trades_only.tail(100), use_container_width=True, hide_index=True, height=320)

    # ══════════════════════════════════════════════════════════
    # MODÜL 5: [05] SMF SPREAD & RİSK RADARI
    # ══════════════════════════════════════════════════════════
    elif current_page == "[05] SMF SPREAD & RİSK RADARI":
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
            
            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
            fig_spread_all = create_spread_risk_chart(all_risk_df)
            st.plotly_chart(fig_spread_all, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("SMF verisi bulunamadı.")

    # ══════════════════════════════════════════════════════════
    # MODÜL 6: [06] SAATLİK PROFİL & ISI HARİTASI
    # ══════════════════════════════════════════════════════════
    elif current_page == "[06] SAATLİK PROFİL & ISI HARİTASI":
        st.markdown(get_section_header_html(
            "Piyasa Fiyat Profili & Saatlik Yoğunluk Isı Haritası",
            "Haftanın günleri ve günün saatleri bazında elektrik fiyat formasyonu"
        ), unsafe_allow_html=True)
        
        # Isı haritası
        fig_heat = create_hourly_heatmap(test_df, height=380)
        st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})
        
        # Kontrat bazlı taban / puant dinamiği
        st.markdown(get_section_header_html("Puant ve Taban Yük Kontrat Trendleri (00-24 vs 08-20 vs 17-21)"), unsafe_allow_html=True)
        fig_bp = create_base_peak_chart(test_df, height=360)
        st.plotly_chart(fig_bp, use_container_width=True, config={"displayModeBar": False})

    # ══════════════════════════════════════════════════════════
    # MODÜL 7: [07] SİSTEM REHBERİ & SRS
    # ══════════════════════════════════════════════════════════
    elif current_page == "[07] SİSTEM REHBERİ & SRS":
        render_documentation_page()

    # ─── Dışa Aktarma ───
    if params["export_csv"]:
        csv_data = export_predictions_csv(forecast_df, test_df, model_metrics)
        st.download_button(
            label="Tahmin Verilerini CSV İndir",
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
            label="Teknik Analiz Raporunu İndir",
            data=report.encode("utf-8"),
            file_name=f"teknik_rapor_{params['target_date']}.md",
            mime="text/markdown",
        )


if __name__ == "__main__":
    main()
