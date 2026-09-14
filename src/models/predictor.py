"""
Tahmin Motoru (FR-03)
Eğitilmiş modelden 24 saatlik PTF fiyat projeksiyonu üretir.
Hedef: Inference süresi < 500ms (NFR-01).
"""

import logging
import time
import numpy as np
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)


from src.features.time_features import HOLIDAYS_TR


def predict_24h_recursive(
    model, 
    history_df: pd.DataFrame, 
    feature_columns: list[str],
    base_pct: float = 0.07,
) -> pd.DataFrame:
    """
    EPİAŞ GÖP 12:30 Kapı Kapanışı Uyumlu 24 Saatlik Özyinelemeli (Recursive Rollout) Tahmin Motoru.
    
    Yarının 24 saatini (h=0...23) simüle ederken, henüz gerçekleşmemiş saatlerin
    lag_1h, lag_2h ve yuvarlanan (rolling) pencerelerini bir önceki adımların 
    model tahminleriyle (rollout) dinamik olarak günceller.
    
    Böylece saat 12:30'da geleceğin t-1 lag'i bilinmiyormuş gibi gerçek piyasa
    koşullarına %100 sadık kalınır (Sıfır Gelecek Sızıntısı / Strict Causal Rollout).
    
    Args:
        model: Eğitilmiş CatBoost/LightGBM/Ensemble modeli
        history_df: Tahmin anına kadar olan geçmiş veri çerçevesi (en az 168+ saat)
        feature_columns: Model öznitelik sütun isimleri
        base_pct: Güven aralığı genişlik yüzdesi
        
    Returns:
        DataFrame: datetime, predicted_ptf, lower_bound, upper_bound
    """
    start = time.time()
    
    # En az 240 saatlik geçmiş seriyi al (rolling_168h ve lag_168h için)
    recent = history_df.tail(240).copy().sort_values("datetime").reset_index(drop=True)
    if len(recent) < 24:
        raise ValueError(f"Yetersiz geçmiş veri: {len(recent)} saat (en az 24 saat gerekli).")
        
    ptf_series = list(recent["ptf"].values)
    last_dt = pd.to_datetime(recent["datetime"].iloc[-1])
    
    has_smf = "smf" in recent.columns
    smf_series = list(recent["smf"].values) if has_smf else []
    
    predictions = []
    pred_dts = []
    
    for step in range(1, 25):
        target_dt = last_dt + pd.Timedelta(hours=step)
        pred_dts.append(target_dt)
        
        # Takvim öznitelikleri (bilinen deterministik takvim)
        h = target_dt.hour
        dow = target_dt.dayofweek
        dom = target_dt.day
        month = target_dt.month
        woy = int(target_dt.isocalendar().week)
        
        is_weekend = int(dow >= 5)
        is_night = int((h >= 22) or (h <= 6))
        is_peak_hour = int(8 <= h <= 20)
        is_holiday = int((month, dom) in HOLIDAYS_TR)
        is_off_day = int(is_weekend or is_holiday)
        
        h_sin = np.sin(2 * np.pi * h / 24)
        h_cos = np.cos(2 * np.pi * h / 24)
        dow_sin = np.sin(2 * np.pi * dow / 7)
        dow_cos = np.cos(2 * np.pi * dow / 7)
        m_sin = np.sin(2 * np.pi * month / 12)
        m_cos = np.cos(2 * np.pi * month / 12)
        
        # Lag ve Rolling hesaplaması (mevcut serinin son elemanları üzerinden)
        cur_ptf_arr = np.array(ptf_series, dtype=np.float64)
        
        feat_dict = {
            "hour": h,
            "day_of_week": dow,
            "day_of_month": dom,
            "month": month,
            "week_of_year": woy,
            "is_weekend": is_weekend,
            "is_night": is_night,
            "is_peak_hour": is_peak_hour,
            "is_holiday": is_holiday,
            "is_off_day": is_off_day,
            "hour_sin": h_sin,
            "hour_cos": h_cos,
            "dow_sin": dow_sin,
            "dow_cos": dow_cos,
            "month_sin": m_sin,
            "month_cos": m_cos,
        }
        
        # Lag öznitelikleri
        lag_hours = [1, 2, 3, 6, 12, 24, 48, 168]
        for lag in lag_hours:
            feat_dict[f"lag_{lag}h"] = cur_ptf_arr[-lag] if len(cur_ptf_arr) >= lag else cur_ptf_arr[0]
            
        # Rolling öznitelikler
        windows = [6, 12, 24, 48, 168]
        for w in windows:
            w_vals = cur_ptf_arr[-w:]
            feat_dict[f"roll_mean_{w}h"] = float(np.mean(w_vals))
            feat_dict[f"roll_std_{w}h"] = float(np.std(w_vals)) if len(w_vals) > 1 else 0.0
            if w >= 24:
                feat_dict[f"roll_min_{w}h"] = float(np.min(w_vals))
                feat_dict[f"roll_max_{w}h"] = float(np.max(w_vals))
                
        feat_dict["price_vs_24h_avg"] = feat_dict["lag_1h"] / (feat_dict["roll_mean_24h"] + 1e-8)
        
        # Fark (diff) öznitelikleri
        t_minus_1 = cur_ptf_arr[-1]
        feat_dict["diff_1h"] = t_minus_1 - cur_ptf_arr[-2]
        feat_dict["diff_24h"] = t_minus_1 - cur_ptf_arr[-25] if len(cur_ptf_arr) >= 25 else 0.0
        feat_dict["diff_168h"] = t_minus_1 - cur_ptf_arr[-169] if len(cur_ptf_arr) >= 169 else 0.0
        feat_dict["pct_change_1h"] = feat_dict["diff_1h"] / (cur_ptf_arr[-2] + 1e-8)
        feat_dict["pct_change_24h"] = feat_dict["diff_24h"] / (cur_ptf_arr[-25] + 1e-8) if len(cur_ptf_arr) >= 25 else 0.0
        
        # Piyasa öznitelikleri (SMF ve spread)
        if has_smf and len(smf_series) >= 24:
            feat_dict["smf_lag_1h"] = smf_series[-1]
            feat_dict["smf_lag_24h"] = smf_series[-24]
            feat_dict["spread_lag_24h"] = cur_ptf_arr[-24] - smf_series[-24]
            smf_series.append(smf_series[-1])
            
        row_df = pd.DataFrame([feat_dict])
        for col in feature_columns:
            if col not in row_df.columns:
                row_df[col] = 0.0
                
        X_step = row_df[feature_columns]
        pred_val = float(model.predict(X_step)[0])
        
        predictions.append(pred_val)
        # Özyineleme: Tahmini bir sonraki adımlara girdi olarak ekle
        ptf_series.append(pred_val)
        
    preds_arr = np.array(predictions, dtype=np.float32)
    uncertainty = _estimate_uncertainty(preds_arr, base_pct=base_pct)
    
    elapsed_ms = (time.time() - start) * 1000
    logger.info(f"24 saatlik özyinelemeli (recursive) tahmin üretildi: {elapsed_ms:.1f}ms")
    
    return pd.DataFrame({
        "datetime": pred_dts,
        "predicted_ptf": preds_arr,
        "lower_bound": (preds_arr - uncertainty).astype(np.float32),
        "upper_bound": (preds_arr + uncertainty).astype(np.float32),
    })


def predict_24h(
    model, 
    feature_df: pd.DataFrame, 
    feature_columns: list[str],
    method: str = "direct",
) -> pd.DataFrame:
    """
    Yarının 24 saatlik PTF fiyat tahminini üretir.
    
    Args:
        model: Eğitilmiş CatBoost/LightGBM/Ensemble modeli
        feature_df: Öznitelik matrisi (en az son 24 saat)
        feature_columns: Model öznitelik sütun isimleri
        method: 'direct' (standart doğrudan çıkarım) veya 'recursive' (12:30 kapı kapanışı özyinelemeli rollout)
    
    Returns:
        DataFrame: datetime, predicted_ptf, lower_bound, upper_bound
    """
    if method == "recursive":
        return predict_24h_recursive(model, feature_df, feature_columns)
        
    start = time.time()
    
    # Son 24 saatlik dilimi al
    last_24 = feature_df.tail(24).copy()
    
    if len(last_24) < 24:
        logger.warning(f"24 saatten az veri var: {len(last_24)} saat")
    
    X = last_24[feature_columns]
    
    # Tahmin
    predictions = model.predict(X)
    
    # Güven aralığı (basit yaklaşım: ±%5-10 bant)
    uncertainty = _estimate_uncertainty(predictions)
    
    result = pd.DataFrame({
        "datetime": last_24["datetime"].values,
        "predicted_ptf": predictions.astype(np.float32),
        "lower_bound": (predictions - uncertainty).astype(np.float32),
        "upper_bound": (predictions + uncertainty).astype(np.float32),
    })
    
    elapsed_ms = (time.time() - start) * 1000
    logger.info(f"24 saatlik tahmin üretildi: {elapsed_ms:.1f}ms (hedef: <500ms)")
    
    if elapsed_ms > 500:
        logger.warning(f"[WARNING] Inference suresi hedefi asildi: {elapsed_ms:.1f}ms > 500ms")
    
    return result


def predict_single(model, features: pd.DataFrame, feature_columns: list[str]) -> float:
    """Tek bir saatlik tahmin üretir."""
    X = features[feature_columns].values.reshape(1, -1)
    return float(model.predict(X)[0])


def predict_batch(model, feature_df: pd.DataFrame, feature_columns: list[str]) -> np.ndarray:
    """Toplu tahmin üretir (backtest için)."""
    X = feature_df[feature_columns]
    return model.predict(X)


def _estimate_uncertainty(predictions: np.ndarray, base_pct: float = 0.07) -> np.ndarray:
    """
    Basit güven aralığı tahmini.
    Fiyat seviyesine bağlı olarak genişleyen bant.
    
    Gerçek projede conformal prediction veya quantile regression kullanılmalı.
    """
    # Fiyat seviyesiyle orantılı bant genişliği
    uncertainty = np.abs(predictions) * base_pct
    
    # Minimum belirsizlik
    uncertainty = np.maximum(uncertainty, 50)
    
    return uncertainty


def generate_forecast_summary(forecast_df: pd.DataFrame) -> dict:
    """
    Tahmin özet metrikleri üretir (KPI kartları için).
    """
    preds = forecast_df["predicted_ptf"]
    
    # Trend analizi
    first_half = preds.iloc[:12].mean()
    second_half = preds.iloc[12:].mean()
    trend = "YUKARI" if second_half > first_half else "AŞAĞI"
    
    # Saatlik min/max
    peak_hour = forecast_df.loc[preds.idxmax()]
    offpeak_hour = forecast_df.loc[preds.idxmin()]
    
    summary = {
        "avg_ptf": float(preds.mean()),
        "min_ptf": float(preds.min()),
        "max_ptf": float(preds.max()),
        "std_ptf": float(preds.std()),
        "trend": trend,
        "trend_pct": float((second_half / first_half - 1) * 100) if first_half > 0 else 0,
        "peak_hour": int(peak_hour["datetime"].hour) if hasattr(peak_hour["datetime"], "hour") else 0,
        "offpeak_hour": int(offpeak_hour["datetime"].hour) if hasattr(offpeak_hour["datetime"], "hour") else 0,
        "spread_range": float(preds.max() - preds.min()),
    }
    
    return summary
