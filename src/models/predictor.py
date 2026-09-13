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


def predict_24h(model, feature_df: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    """
    Yarının 24 saatlik PTF fiyat tahminini üretir.
    
    Args:
        model: Eğitilmiş CatBoost/LightGBM modeli
        feature_df: Öznitelik matrisi (en az son 24 saat)
        feature_columns: Model öznitelik sütun isimleri
    
    Returns:
        DataFrame: datetime, predicted_ptf, lower_bound, upper_bound
    """
    start = time.time()
    
    # Son 24 saatlik dilimi al
    last_24 = feature_df.tail(24).copy()
    
    if len(last_24) < 24:
        logger.warning(f"24 saatten az veri var: {len(last_24)} saat")
    
    X = last_24[feature_columns]
    
    # Tahmin
    predictions = model.predict(X)
    
    # Güven aralığı (basit yaklaşım: ±%5-10 bant)
    # Gerçek projede quantile regression veya conformal prediction kullanılmalı
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
