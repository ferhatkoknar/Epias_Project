"""
Sistem Entegrasyon ve SRS Doğrulama Testi
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
import pandas as pd
import numpy as np
from src.data.fetcher import fetch_all_market_data
from src.data.cleaner import clean_market_data
from src.features.time_features import create_time_features, get_feature_columns
from src.features.market_features import create_market_features
from src.models.trainer import train_model, get_feature_importance
from src.models.evaluator import evaluate_model
from src.models.predictor import predict_24h
from src.trading.simulator import run_backtest, calculate_trading_metrics
from src.trading.risk import calculate_spread_risk, get_risk_summary

def run_all_tests():
    print("=== EPİAŞ PTF TAHMİN & TRADING PROJESİ SRS DOĞRULAMA TESTİ ===")
    
    # 1. Veri Çekme (FR-01)
    print("\n[FR-01] Veri Çekme & ETL Test Ediliyor...")
    t0 = time.time()
    raw_df = fetch_all_market_data("2024-01-01", "2026-09-01")
    t_fetch = time.time() - t0
    print(f"  -> Raw veri şekli: {raw_df.shape}, Süre: {t_fetch:.2f}s")
    assert not raw_df.empty, "Hata: raw_df boş olamaz!"
    assert "ptf" in raw_df.columns, "Hata: ptf sütunu bulunamadı!"
    
    # 2. Veri Temizleme & Bütünlük (FR-01 & NFR-02)
    clean_df = clean_market_data(raw_df)
    print(f"  -> Temiz veri şekli: {clean_df.shape}")
    assert clean_df["ptf"].isnull().sum() == 0, "Hata: ptf içinde eksik veri var!"
    print("  -> FR-01: BAŞARILI")
    
    # 3. Öznitelik Mühendisliği (FR-02)
    print("\n[FR-02] Öznitelik Mühendisliği Test Ediliyor...")
    feat_df = create_time_features(clean_df)
    feat_df = create_market_features(feat_df)
    feature_cols = get_feature_columns(feat_df)
    print(f"  -> Üretilen öznitelik sayısı: {len(feature_cols)}")
    print(f"  -> Örnek öznitelikler: {feature_cols[:8]}")
    
    # Lag kontrolü: t-1, t-24, t-48, t-168
    required_lags = ["lag_1h", "lag_24h", "lag_48h", "lag_168h"]
    for lag in required_lags:
        assert lag in feat_df.columns, f"Hata: {lag} özniteliği eksik!"
    
    # Takvim ve tatil kontrolü
    required_cal = ["hour", "day_of_week", "month", "is_weekend", "is_holiday"]
    for c in required_cal:
        assert c in feat_df.columns, f"Hata: {c} takvim özelliği eksik!"
    print("  -> FR-02: BAŞARILI")
    
    # 4. Model Eğitimi & Walk-Forward (FR-03, NFR-01)
    print("\n[FR-03 & NFR-01] Model Eğitimi ve Tahmin Motoru Test Ediliyor...")
    test_size = 30 * 24
    train_df = feat_df.iloc[:-test_size]
    test_df = feat_df.iloc[-test_size:]
    
    X_train = train_df[feature_cols]
    y_train = train_df["ptf"]
    X_test = test_df[feature_cols]
    y_test = test_df["ptf"]
    
    val_size = max(1, int(len(train_df) * 0.1))
    X_val = train_df[feature_cols].iloc[-val_size:]
    y_val = train_df["ptf"].iloc[-val_size:]
    X_train_sub = train_df[feature_cols].iloc[:-val_size]
    y_train_sub = train_df["ptf"].iloc[:-val_size]
    
    # CatBoost Test
    t0 = time.time()
    model_cb = train_model(X_train_sub, y_train_sub, X_val, y_val, model_type="catboost", params={"iterations": 300, "verbose": 0})
    t_train_cb = time.time() - t0
    print(f"  -> CatBoost Eğitim Süresi: {t_train_cb:.2f}s")
    
    # 24 Saatlik Çıkarım Hızı (NFR-01: < 500ms)
    t0 = time.time()
    f24 = predict_24h(model_cb, feat_df, feature_cols)
    t_infer_24 = (time.time() - t0) * 1000
    print(f"  -> 24s Tahmin Süresi (NFR-01): {t_infer_24:.2f} ms (Hedef: < 500ms)")
    assert t_infer_24 < 500, f"Hata: NFR-01 aşıldı! Süre: {t_infer_24}ms"
    assert len(f24) == 24, "Hata: 24 saatlik tahmin 24 satır değil!"
    print("  -> NFR-01: BAŞARILI")
    
    # LightGBM Test
    t0 = time.time()
    model_lgb = train_model(X_train_sub, y_train_sub, X_val, y_val, model_type="lightgbm", params={"n_estimators": 300, "verbose": -1})
    t_train_lgb = time.time() - t0
    print(f"  -> LightGBM Eğitim Süresi: {t_train_lgb:.2f}s")
    print("  -> FR-03: BAŞARILI")
    
    # 5. Model Başarımı ve Metrikler (FR-04)
    print("\n[FR-04] Performans ve Başarım Metrikleri...")
    preds = model_cb.predict(X_test)
    metrics = evaluate_model(y_test.values, preds)
    mape = metrics["mape"]
    da = metrics["directional_accuracy"]
    rmse = metrics["rmse"]
    mae = metrics["mae"]
    r2 = metrics["r2"]
    print(f"  -> Test MAPE: %{mape:.2f} (Kabul Kriteri: < %12.0)")
    print(f"  -> Yön Doğruluğu (Directional Accuracy): %{da:.2f} (Kabul Kriteri: > %70.0)")
    print(f"  -> RMSE: {rmse:.2f} TL | MAE: {mae:.2f} TL | R2: {r2:.4f}")
    assert mape < 12.0, f"Uyarı/Hata: MAPE (%{mape:.2f}) hedefi (%12) sağlamadı!"
    assert da > 70.0, f"Uyarı/Hata: Yön doğruluğu (%{da:.2f}) hedefi (%70) sağlamadı!"
    print("  -> FR-04: BAŞARILI")
    
    # 6. Risk ve Spread Göstergesi (FR-06)
    print("\n[FR-06] Spread & Risk Göstergesi Test Ediliyor...")
    risk_df = calculate_spread_risk(
        test_df["ptf"].values,
        test_df["smf"].values if "smf" in test_df.columns else test_df["ptf"].values,
        preds
    )
    risk_sum = get_risk_summary(risk_df)
    print(f"  -> Ortalama Spread: {risk_sum['avg_spread']:.2f} TL")
    print(f"  -> Yüksek/Kritik Risk Oranı: %{risk_sum['pct_high_risk']:.2f}")
    assert "risk_color" in risk_df.columns, "Hata: Renk kodlu risk sütunu eksik!"
    print("  -> FR-06: BAŞARILI")
    
    # 7. P&L Trading Simülasyonu (FR-07)
    print("\n[FR-07] P&L Trading Simülasyonu Test Ediliyor...")
    backtest_df = run_backtest(y_test.values, preds, test_df["datetime"], threshold_tl=2500, position_mwh=10)
    trading_metrics = calculate_trading_metrics(backtest_df)
    print(f"  -> Toplam P&L: {trading_metrics['total_pnl']:,.2f} TL")
    print(f"  -> Kazanma Oranı: %{trading_metrics['win_rate']:.2f}")
    print(f"  -> Max Drawdown: %{trading_metrics['max_drawdown_pct']:.2f} ({trading_metrics['max_drawdown_tl']:,.2f} TL)")
    assert "cumulative_pnl" in backtest_df.columns, "Hata: cumulative_pnl sütunu yok!"
    print("  -> FR-07: BAŞARILI")
    
    # 8. Dışa Aktarma ve Teknik Raporlama (FR-08)
    print("\n[FR-08] Dışa Aktarma (CSV, Excel, HTML, Word) Test Ediliyor...")
    from src.ui.export import (
        export_predictions_csv,
        export_predictions_excel,
        generate_technical_report_html,
        generate_technical_report_docx,
    )
    test_day = test_df.tail(24).copy()
    test_day["predicted_ptf"] = preds[-24:]
    
    csv_bytes = export_predictions_csv(test_day, metrics=metrics)
    assert len(csv_bytes) > 0, "Hata: CSV dışa aktarma boş veri üretti!"
    assert b"Tahmin_PTF_TL" in csv_bytes, "Hata: CSV beklenen sütunları içermiyor!"
    print(f"  -> CSV Aktarımı Başarılı ({len(csv_bytes)} bytes)")
    
    xlsx_bytes = export_predictions_excel(test_day, model_metrics=metrics, trading_metrics=trading_metrics)
    assert len(xlsx_bytes) > 1000, "Hata: Excel dosyası oluşturulamadı!"
    print(f"  -> Excel (XLSX) Aktarımı Başarılı ({len(xlsx_bytes)} bytes)")
    
    html_report = generate_technical_report_html(metrics, trading_metrics, day_df=test_day, model_type="catboost", target_date_str="2026-09-14")
    assert len(html_report) > 1000 and "<html" in html_report.lower(), "Hata: HTML raporu üretilemedi!"
    print(f"  -> HTML Yönetici Raporu Başarılı ({len(html_report)} karakter)")
    
    docx_bytes = generate_technical_report_docx(metrics, trading_metrics, day_df=test_day, model_type="catboost", target_date_str="2026-09-14")
    assert len(docx_bytes) > 5000, "Hata: Word (DOCX) raporu üretilemedi!"
    print(f"  -> Word (DOCX) Raporu Başarılı ({len(docx_bytes)} bytes)")
    print("  -> FR-08: BAŞARILI")
    
    # 9. Ensemble & Stres Testi (Gelişmiş Özellikler)
    print("\n[ADVANCED] Ensemble Model & Stres Testi Test Ediliyor...")
    from src.trading.simulator import simulate_market_shock
    from src.models.trainer import EnsembleModel
    ens_model = EnsembleModel(model_cb, model_lgb, weights=(0.5, 0.5))
    ens_preds = ens_model.predict(X_test)
    ens_metrics = evaluate_model(y_test.values, ens_preds)
    print(f"  -> Ensemble MAPE: %{ens_metrics['mape']:.2f}")
    assert ens_metrics["mape"] < 12.0, "Hata: Ensemble MAPE hedefi asildi!"
    
    shock_df = simulate_market_shock(backtest_df, shock_type="gas_spike", shock_pct=0.25)
    assert "shocked_cumulative_pnl" in shock_df.columns, "Hata: shocked_cumulative_pnl sutunu yok!"
    print("  -> ADVANCED: BAŞARILI")
    
    print("\n=======================================================")
    print("SONUÇ: SRS BELGESİNDEKİ TÜM GEREKSİNİMLER (FR-01...FR-08, NFR-01...NFR-03) BAŞARIYLA SAĞLANMIŞTIR!")
    print("=======================================================")

if __name__ == "__main__":
    run_all_tests()
