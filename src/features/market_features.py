"""
Piyasa Öznitelikleri Modülü
PTF-SMF spread, volatilite ve KGÜP bazlı öznitelikler üretir.
"""

import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def create_market_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Piyasa bazlı öznitelikler ekler.
    
    Üretilen öznitelikler:
    - Spread dinamikleri (PTF - SMF)
    - Volatilite göstergeleri
    - Fiyat rejim göstergeleri
    """
    df = df.copy()
    
    # Spread özellikleri
    if "smf" in df.columns:
        df = _add_spread_features(df)
    
    # Volatilite özellikleri
    df = _add_volatility_features(df)
    
    # Fiyat rejimi göstergeleri
    df = _add_regime_indicators(df)
    
    logger.info(f"Piyasa öznitelikleri eklendi. Toplam sütun: {len(df.columns)}")
    return df


def _add_spread_features(df: pd.DataFrame) -> pd.DataFrame:
    """PTF-SMF spread dinamiklerini hesaplar."""
    if "spread" not in df.columns:
        df["spread"] = df["ptf"] - df["smf"]
    
    # Spread lag'ları
    for lag in [1, 6, 24]:
        df[f"spread_lag_{lag}h"] = df["spread"].shift(lag)
    
    # Spread rolling ortalama
    df["spread_roll_24h"] = df["spread"].shift(1).rolling(24, min_periods=1).mean()
    df["spread_roll_std_24h"] = df["spread"].shift(1).rolling(24, min_periods=2).std()
    
    # Enerji açığı/fazlası göstergesi (spread yönü)
    df["spread_positive"] = (df["spread"].shift(1) > 0).astype(np.uint8)
    
    # Spread büyüklük kategorisi
    spread_abs = df["spread"].shift(1).abs()
    df["spread_regime"] = pd.cut(
        spread_abs,
        bins=[-np.inf, 50, 150, 400, np.inf],
        labels=[0, 1, 2, 3]
    ).astype(float).astype(np.float32)
    
    return df


def _add_volatility_features(df: pd.DataFrame) -> pd.DataFrame:
    """Fiyat volatilitesi göstergelerini hesaplar."""
    ptf = df["ptf"]
    
    # Gerçekleşen volatilite (6h, 24h, 168h)
    for w in [6, 24, 168]:
        returns = ptf.pct_change(1)
        df[f"volatility_{w}h"] = returns.shift(1).rolling(w, min_periods=2).std().astype(np.float32)
    
    # Bollinger Band benzeri sinyaller
    roll_mean = ptf.shift(1).rolling(24, min_periods=1).mean()
    roll_std = ptf.shift(1).rolling(24, min_periods=2).std()
    
    df["bb_upper_dist"] = ((ptf.shift(1) - (roll_mean + 2 * roll_std)) / (roll_std + 1e-8)).astype(np.float32)
    df["bb_lower_dist"] = ((ptf.shift(1) - (roll_mean - 2 * roll_std)) / (roll_std + 1e-8)).astype(np.float32)
    
    # ATR benzeri gösterge (Average True Range)
    high_24 = ptf.shift(1).rolling(24, min_periods=1).max()
    low_24 = ptf.shift(1).rolling(24, min_periods=1).min()
    df["atr_24h"] = ((high_24 - low_24) / (roll_mean + 1e-8)).astype(np.float32)
    
    return df


def _add_regime_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Fiyat rejimi (düşük/normal/yüksek/spike) göstergeleri."""
    ptf = df["ptf"]
    
    # Rolling yüzdelik dilimler
    roll_50 = ptf.shift(1).rolling(168, min_periods=24).quantile(0.5)
    roll_90 = ptf.shift(1).rolling(168, min_periods=24).quantile(0.9)
    roll_10 = ptf.shift(1).rolling(168, min_periods=24).quantile(0.1)
    
    # Mevcut fiyatın tarihsel konumu
    df["price_percentile"] = (
        (ptf.shift(1) - roll_10) / (roll_90 - roll_10 + 1e-8)
    ).clip(0, 2).astype(np.float32)
    
    # Momentum göstergesi (yükseliş/düşüş trendi)
    df["momentum_6h"] = (ptf.shift(1) / ptf.shift(7) - 1).astype(np.float32)
    df["momentum_24h"] = (ptf.shift(1) / ptf.shift(25) - 1).astype(np.float32)
    
    return df
