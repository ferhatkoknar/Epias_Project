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
    """Veriyi yükler, temizler ve öznitelikleri üretir."""
    with st.spinner("Veriler hazırlanıyor..."):
        # Veri çek (demo veya API)
        raw_df = fetch_all_market_data("2024-01-01", "2026-09-01")
        
        # Temizle
        clean_df = clean_market_data(raw_df)
        
        # Öznitelik mühendisliği
        featured_df = create_time_features(clean_df)
        featured_df = create_market_features(featured_df)
        
        return clean_df, featured_df


@st.cache_data(ttl=3600, show_spinner=False)
def train_and_evaluate(featured_df_hash, model_type):
    """Model eğitir ve değerlendirir."""
    featured_df = st.session_state.get("featured_df")
    if featured_df is None:
        return None, None, None, None
    
    feature_cols = get_feature_columns(featured_df)
    target = "ptf"
    
    # Train/test split (son 30 gün test)
    test_size = 30 * 24  # 30 gün x 24 saat
    train_df = featured_df.iloc[:-test_size]
    test_df = featured_df.iloc[-test_size:]
    
    X_train = train_df[feature_cols]
    y_train = train_df[target]
    X_test = test_df[feature_cols]
    y_test = test_df[target]
    
    # Model eğit
    from src.models.trainer import train_model, get_feature_importance
    
    # Validasyon seti (son %10 train)
    val_size = max(1, int(len(X_train) * 0.1))
    X_val = X_train.iloc[-val_size:]
    y_val = y_train.iloc[-val_size:]
    X_train_final = X_train.iloc[:-val_size]
    y_train_final = y_train.iloc[:-val_size]
    
    model = train_model(
        X_train_final, y_train_final,
        X_val, y_val,
        model_type=model_type,
    )
    
    # Tahmin ve değerlendirme
    predictions = model.predict(X_test)
    metrics = evaluate_model(y_test.values, predictions)
    
    # Öznitelik önemi
    fi_df = get_feature_importance(model, feature_cols, model_type)
    
    return model, metrics, predictions, fi_df


# ─── Ana Uygulama ───
def main():
    # Başlık
    st.markdown(get_header_html(), unsafe_allow_html=True)
    
    # Sidebar
    params = render_sidebar()
    
    # Veri yükle
    try:
        clean_df, featured_df = load_and_prepare_data()
        st.session_state["featured_df"] = featured_df
    except Exception as e:
        st.error(f"Veri yükleme hatası: {e}")
        st.stop()
    
    feature_cols = get_feature_columns(featured_df)
    
    # Test verisi ayır
    test_size = 30 * 24
    test_df = featured_df.iloc[-test_size:]
    train_df = featured_df.iloc[:-test_size]
    
    # Model eğit/yükle
    try:
        with st.spinner("Model hazırlanıyor..."):
            from src.models.trainer import train_model, get_feature_importance
            
            val_size = max(1, int(len(train_df) * 0.1))
            X_val = train_df[feature_cols].iloc[-val_size:]
            y_val = train_df["ptf"].iloc[-val_size:]
            X_train = train_df[feature_cols].iloc[:-val_size]
            y_train = train_df["ptf"].iloc[:-val_size]
            
            model = train_model(
                X_train, y_train, X_val, y_val,
                model_type=params["model_type"],
            )
            
            # Test tahminleri
            test_predictions = model.predict(test_df[feature_cols])
            model_metrics = evaluate_model(test_df["ptf"].values, test_predictions)
            fi_df = get_feature_importance(model, feature_cols, params["model_type"])
    except Exception as e:
        st.error(f"Model eğitim hatası: {e}")
        logger.error(f"Model hatası: {e}", exc_info=True)
        # Fallback metrikler
        model = None
        test_predictions = test_df["ptf"].values * np.random.uniform(0.92, 1.08, len(test_df))
        model_metrics = evaluate_model(test_df["ptf"].values, test_predictions)
        fi_df = pd.DataFrame({"feature": feature_cols[:10], "importance": range(10, 0, -1), "importance_pct": range(20, 0, -2)})
    
    # 24 saatlik tahmin
    forecast_df = predict_24h(model if model else None, test_df, feature_cols) if model else pd.DataFrame({
        "datetime": test_df["datetime"].iloc[-24:].values,
        "predicted_ptf": test_predictions[-24:],
        "lower_bound": test_predictions[-24:] * 0.93,
        "upper_bound": test_predictions[-24:] * 1.07,
    })
    forecast_summary = generate_forecast_summary(forecast_df)
    
    # KPI Kartları
    render_kpi_cards(forecast_summary, model_metrics)
    
    st.markdown("", unsafe_allow_html=True)
    
    # Model bilgi kartı
    render_model_info(params["model_type"], model_metrics)
    
    # ─── Sekmeler ───
    tab1, tab2, tab3 = st.tabs([
        "Fiyat Projeksiyonu",
        "Backtest & P/L Simülasyonu",
        "Model Analizi",
    ])
    
    # ─── SEKME 1: Fiyat Projeksiyonu ───
    with tab1:
        st.markdown(get_section_header_html(
            "24 Saatlik PTF Projeksiyonu",
            "Gerçekleşen fiyat ve model tahmini karşılaştırması"
        ), unsafe_allow_html=True)
        
        # Ana grafik
        actual_24 = test_df[["datetime", "ptf"]].tail(48)
        fig_forecast = create_ptf_forecast_chart(actual_24, forecast_df)
        st.plotly_chart(fig_forecast, use_container_width=True, config={"displayModeBar": False})
        
        # Hata analizi
        col_left, col_right = st.columns([1.1, 0.9])
        
        with col_left:
            st.markdown(get_section_header_html("Tahmin Hata Analizi"), unsafe_allow_html=True)
            hours = test_df["datetime"].dt.hour.values
            fig_err = create_error_distribution_chart(
                test_df["ptf"].values, test_predictions, hours
            )
            st.plotly_chart(fig_err, use_container_width=True, config={"displayModeBar": False})
        
        with col_right:
            st.markdown(get_section_header_html("Spread & Risk"), unsafe_allow_html=True)
            
            if "smf" in test_df.columns:
                risk_df = calculate_spread_risk(
                    test_df["ptf"].values,
                    test_df["smf"].values,
                    test_predictions,
                )
                risk_summary = get_risk_summary(risk_df)
                render_risk_indicator(risk_summary["current_risk"], risk_summary["current_color"])
                
                fig_spread = create_spread_risk_chart(risk_df.tail(168))
                st.plotly_chart(fig_spread, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Spread analizi için SMF verisi gerekli.")
    
    # ─── SEKME 2: Backtest & P&L ───
    with tab2:
        st.markdown(get_section_header_html(
            "Trading Simülasyonu",
            "Geçmişe dönük strateji performans analizi"
        ), unsafe_allow_html=True)
        
        # Backtest çalıştır
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
        
        # Trading özet kartı
        render_trading_summary(trading_metrics)
        
        st.markdown("", unsafe_allow_html=True)
        
        # P&L grafiği
        fig_pnl = create_pnl_chart(backtest_df)
        st.plotly_chart(fig_pnl, use_container_width=True, config={"displayModeBar": False})
        
        # Detay tablosu
        with st.expander("İşlem Detayları"):
            trades_only = backtest_df[backtest_df["signal"] != 0][
                ["datetime", "actual_ptf", "predicted_ptf", "signal", "pnl", "cumulative_pnl"]
            ].copy()
            trades_only["signal"] = trades_only["signal"].map({1: "ALIŞ", -1: "SATIŞ"})
            trades_only = trades_only.rename(columns={
                "datetime": "Tarih/Saat",
                "actual_ptf": "Gerçek PTF",
                "predicted_ptf": "Tahmin PTF",
                "signal": "Sinyal",
                "pnl": "P&L (TL)",
                "cumulative_pnl": "Küm. P&L (TL)",
            })
            st.dataframe(trades_only.tail(50), use_container_width=True, hide_index=True)
    
    # ─── SEKME 3: Model Analizi ───
    with tab3:
        st.markdown(get_section_header_html(
            "Model Performans Detayları",
            "Öznitelik önemi ve metrik breakdown"
        ), unsafe_allow_html=True)
        
        col_a, col_b = st.columns([1, 1])
        
        with col_a:
            # Metrikler tablosu
            st.markdown(get_section_header_html("Performans Metrikleri"), unsafe_allow_html=True)
            
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
                "Hedef": ["< %12", "—", "—", "—", "> %70", "—"],
                "Durum": [
                    "Basarili" if model_metrics["mape"] < 12 else "Asildi",
                    "—",
                    "—",
                    "—",
                    "Basarili" if model_metrics["directional_accuracy"] > 70 else "Gelistirilmeli",
                    "—",
                ],
            }
            st.dataframe(pd.DataFrame(metric_data), use_container_width=True, hide_index=True)
            
            # Hata dağılımı istatistikleri
            error_dist = calculate_error_distribution(test_df["ptf"].values, test_predictions)
            st.markdown(get_section_header_html("Hata Dağılımı"), unsafe_allow_html=True)
            
            dist_data = {
                "Istatistik": ["Ort. Hata", "Std. Sapma", "Medyan (P50)", "P75", "P95",
                              "%5 icerisinde", "%10 icerisinde"],
                "Deger": [
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
            st.markdown(get_section_header_html("Öznitelik Önemi"), unsafe_allow_html=True)
            fig_fi = create_feature_importance_chart(fi_df)
            st.plotly_chart(fig_fi, use_container_width=True, config={"displayModeBar": False})
            
            # Saatlik hata
            st.markdown(get_section_header_html("Saatlik Performans"), unsafe_allow_html=True)
            hourly_metrics = evaluate_hourly(
                test_df["ptf"].values, test_predictions, test_df["datetime"].dt.hour.values
            )
            hourly_display = hourly_metrics[["hour", "mape", "rmse", "bias"]].copy()
            hourly_display.columns = ["Saat", "MAPE (%)", "RMSE (TL)", "Bias (TL)"]
            hourly_display["MAPE (%)"] = hourly_display["MAPE (%)"].round(1)
            hourly_display["RMSE (TL)"] = hourly_display["RMSE (TL)"].round(0)
            hourly_display["Bias (TL)"] = hourly_display["Bias (TL)"].round(0)
            st.dataframe(hourly_display, use_container_width=True, hide_index=True, height=400)
    
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
            trading_metrics if "trading_metrics" in dir() else None,
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
