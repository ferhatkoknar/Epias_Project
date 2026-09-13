"""
Spread & Risk Göstergesi Modülü (FR-06)
PTF-SMF spread analizi ve renk kodlu risk uyarıları üretir.
"""

import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_spread_risk(
    ptf: np.ndarray,
    smf: np.ndarray,
    predicted_ptf: np.ndarray = None,
) -> pd.DataFrame:
    """
    PTF-SMF spread risk analizi yapar.
    
    Enerji açığı/fazlası durumunda marjinal risk primini hesaplar.
    
    Returns:
        DataFrame: spread, risk_level, risk_color, risk_description
    """
    spread = ptf - smf
    
    # Risk seviyeleri
    risk_levels = []
    risk_colors = []
    risk_descriptions = []
    
    for s in spread:
        level, color, desc = _classify_spread_risk(s)
        risk_levels.append(level)
        risk_colors.append(color)
        risk_descriptions.append(desc)
    
    result = pd.DataFrame({
        "ptf": ptf,
        "smf": smf,
        "spread": spread,
        "spread_pct": ((spread / (smf + 1e-8)) * 100).astype(np.float32),
        "risk_level": risk_levels,
        "risk_color": risk_colors,
        "risk_description": risk_descriptions,
    })
    
    # Tahmin varsa ek risk metrikleri
    if predicted_ptf is not None:
        result["predicted_spread"] = predicted_ptf - smf
        result["forecast_risk"] = _calculate_forecast_risk(predicted_ptf, ptf, smf)
    
    return result


def _classify_spread_risk(spread: float) -> tuple[str, str, str]:
    """
    Spread değerine göre risk seviyesi belirler.
    Renk kodlu uyarı sistemi.
    """
    abs_spread = abs(spread)
    
    if abs_spread < 50:
        return "DÜŞÜK", "#00E676", "Piyasa dengeli — Normal işlem koşulları"
    elif abs_spread < 150:
        return "ORTA", "#FFB800", "Orta spread — Pozisyon boyutuna dikkat"
    elif abs_spread < 400:
        return "YÜKSEK", "#FF9100", "Yüksek volatilite — Risk yönetimi gerekli"
    else:
        return "KRİTİK", "#FF4444", "Aşırı spread — Dikkatli olun, piyasa stresi"


def _calculate_forecast_risk(
    predicted_ptf: np.ndarray,
    actual_ptf: np.ndarray,
    smf: np.ndarray,
) -> np.ndarray:
    """
    Tahmin bazlı ileriye dönük risk skoru hesaplar.
    0-100 arası normalize edilmiş risk endeksi.
    """
    # Bileşenler
    spread_risk = np.abs(predicted_ptf - smf) / (np.mean(actual_ptf) + 1e-8) * 30
    volatility_risk = np.abs(predicted_ptf - actual_ptf) / (actual_ptf + 1e-8) * 40
    trend_risk = np.abs(np.diff(predicted_ptf, prepend=predicted_ptf[0])) / (np.mean(actual_ptf) + 1e-8) * 30
    
    total_risk = (spread_risk + volatility_risk + trend_risk).clip(0, 100)
    
    return total_risk.astype(np.float32)


def get_risk_summary(risk_df: pd.DataFrame) -> dict:
    """Risk özet istatistiklerini döndürür."""
    return {
        "avg_spread": float(risk_df["spread"].mean()),
        "max_spread": float(risk_df["spread"].max()),
        "min_spread": float(risk_df["spread"].min()),
        "std_spread": float(risk_df["spread"].std()),
        "pct_high_risk": float((risk_df["risk_level"].isin(["YÜKSEK", "KRİTİK"])).mean() * 100),
        "current_risk": risk_df["risk_level"].iloc[-1] if len(risk_df) > 0 else "N/A",
        "current_color": risk_df["risk_color"].iloc[-1] if len(risk_df) > 0 else "#8B95A5",
    }
