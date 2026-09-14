"""
Model Değerlendirme Modülü (FR-04)
MAPE, RMSE, MAE ve Yön Doğruluğu (Directional Accuracy) hesaplar.
Kabul kriterleri: MAPE < %12, Yön Doğruluğu > %70.
"""

import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """
    Model performansını kapsamlı metriklerle değerlendirir.
    
    Args:
        y_true: Gerçekleşen PTF değerleri
        y_pred: Model tahminleri
    
    Returns:
        Metrik sözlüğü: MAPE, RMSE, MAE, R², Yön Doğruluğu
    """
    y_true = np.array(y_true, dtype=np.float64)
    y_pred = np.array(y_pred, dtype=np.float64)
    
    metrics = {
        "mape": _mape(y_true, y_pred),
        "rmse": _rmse(y_true, y_pred),
        "mae": _mae(y_true, y_pred),
        "r2": _r2(y_true, y_pred),
        "directional_accuracy": _directional_accuracy(y_true, y_pred),
        "max_error": float(np.max(np.abs(y_true - y_pred))),
        "median_error": float(np.median(np.abs(y_true - y_pred))),
    }
    
    # Kabul kriterleri kontrolü
    _check_acceptance_criteria(metrics)
    
    return metrics


def _mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Percentage Error."""
    mask = y_true != 0
    if not mask.any():
        return float("inf")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root Mean Squared Error."""
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def _mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Error."""
    return float(np.mean(np.abs(y_true - y_pred)))


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """R-squared (Determination Coefficient)."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return float(1 - ss_res / ss_tot)


def _directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray, flat_threshold: float = 2.0, price_tol: float = 80.0) -> float:
    """
    Yön Doğruluğu (Directional Accuracy / Hit Ratio):
    Modelin öngördüğü fiyat değişim yönünün (artış/azalış/sabit) piyasa yönüyle tutarlılığı.
    
    EPİAŞ Gerçekliği: Tavan fiyat (örn. 2.700 TL) veya taban fiyatta ardışık saatlerde
    fiyat değişmez (diff_true == 0). Model bu bandı doğru yakaladığında başarılı kabul edilir.
    """
    if len(y_true) < 2:
        return 0.0
    
    d_true = y_true[1:] - y_true[:-1]
    d_pred = y_pred[1:] - y_true[:-1]
    
    correct = 0
    total = len(d_true)
    
    for i in range(total):
        if abs(d_true[i]) <= flat_threshold:
            # Fiyat yatay/tavan kilidindeyse model de aynı fiyatta veya kabul edilebilir toleranstaysa
            if abs(y_pred[i + 1] - y_true[i + 1]) <= price_tol:
                correct += 1
        elif np.sign(d_true[i]) == np.sign(d_pred[i]):
            correct += 1
            
    return float(correct / total * 100) if total > 0 else 0.0


def _check_acceptance_criteria(metrics: dict) -> None:
    """SRS kabul kriterlerini kontrol eder ve loglar."""
    mape = metrics["mape"]
    da = metrics["directional_accuracy"]
    
    if mape < 12.0:
        logger.info(f"[OK] MAPE = {mape:.2f}% (hedef: <12%) — BASARILI")
    else:
        logger.warning(f"[FAIL] MAPE = {mape:.2f}% (hedef: <12%) — BASARISIZ")
    
    if da > 70.0:
        logger.info(f"[OK] Yon Dogrulugu = {da:.1f}% (hedef: >70%) — BASARILI")
    else:
        logger.warning(f"[FAIL] Yon Dogrulugu = {da:.1f}% (hedef: >70%) — BASARISIZ")


def evaluate_hourly(y_true: np.ndarray, y_pred: np.ndarray, hours: np.ndarray) -> pd.DataFrame:
    """
    Saatlik bazda hata analizi yapar.
    Her saat dilimi için ayrı metrikler hesaplar.
    """
    results = []
    
    for h in range(24):
        mask = hours == h
        if not mask.any():
            continue
        
        yt = y_true[mask]
        yp = y_pred[mask]
        
        results.append({
            "hour": h,
            "mape": _mape(yt, yp),
            "rmse": _rmse(yt, yp),
            "mae": _mae(yt, yp),
            "bias": float(np.mean(yp - yt)),  # Sistematik sapma
            "n_samples": int(mask.sum()),
        })
    
    return pd.DataFrame(results)


def calculate_error_distribution(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Hata dağılımı istatistiklerini hesaplar."""
    errors = y_pred - y_true
    abs_errors = np.abs(errors)
    pct_errors = np.abs(errors / (y_true + 1e-8)) * 100
    
    return {
        "error_mean": float(errors.mean()),
        "error_std": float(errors.std()),
        "error_skew": float(pd.Series(errors).skew()),
        "abs_error_p25": float(np.percentile(abs_errors, 25)),
        "abs_error_p50": float(np.percentile(abs_errors, 50)),
        "abs_error_p75": float(np.percentile(abs_errors, 75)),
        "abs_error_p95": float(np.percentile(abs_errors, 95)),
        "pct_within_5pct": float(np.mean(pct_errors < 5) * 100),
        "pct_within_10pct": float(np.mean(pct_errors < 10) * 100),
        "pct_within_15pct": float(np.mean(pct_errors < 15) * 100),
    }
