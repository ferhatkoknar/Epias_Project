"""
Zaman Serisi Öznitelik Mühendisliği (FR-02)
Lag, rolling, takvim ve tatil özellikleri üretir.
Data Leakage engeli (NFR-02): Sadece geçmiş veriler kullanılır.
"""

import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Türkiye resmi tatilleri (ay, gün)
HOLIDAYS_TR = [
    (1, 1),    # Yılbaşı
    (4, 23),   # Ulusal Egemenlik ve Çocuk Bayramı
    (5, 1),    # Emek ve Dayanışma Günü
    (5, 19),   # Atatürk'ü Anma, Gençlik ve Spor Bayramı
    (7, 15),   # Demokrasi ve Milli Birlik Günü
    (8, 30),   # Zafer Bayramı
    (10, 29),  # Cumhuriyet Bayramı
]


def create_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tüm zaman serisi özniteliklerini üretir.
    
    Üretilen öznitelikler:
    - Lag özellikleri: t-1, t-2, t-3, t-6, t-12, t-24, t-48, t-168
    - Rolling istatistikler: 6h, 12h, 24h, 48h, 168h pencerelerinde mean/std
    - Takvim: saat, gün, ay, hafta sonu, tatil
    
    Args:
        df: 'datetime' ve 'ptf' sütunları içeren DataFrame
    
    Returns:
        Öznitelikler eklenmiş DataFrame
    """
    df = df.copy()
    df = df.sort_values("datetime").reset_index(drop=True)
    
    # 1. Lag özellikleri
    df = _add_lag_features(df, "ptf")
    
    # 2. Rolling istatistikler
    df = _add_rolling_features(df, "ptf")
    
    # 3. Takvim özellikleri
    df = _add_calendar_features(df)
    
    # 4. Fark (diff) özellikleri
    df = _add_diff_features(df, "ptf")
    
    # NaN olan satırları işaretle (lag'lardan dolayı)
    initial_len = len(df)
    df = df.dropna().reset_index(drop=True)
    dropped = initial_len - len(df)
    
    if dropped > 0:
        logger.info(f"{dropped} satır NaN nedeniyle çıkarıldı (lag penceresi).")
    
    logger.info(f"Toplam {len(df.columns)} öznitelik üretildi. Satır: {len(df)}")
    return df


def _add_lag_features(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """
    Gecikme (lag) öznitelikleri üretir.
    Strictly causal: Sadece geçmiş değerler kullanılır (NFR-02 Data Leakage engeli).
    """
    lag_hours = [1, 2, 3, 6, 12, 24, 48, 168]
    
    for lag in lag_hours:
        df[f"lag_{lag}h"] = df[target_col].shift(lag)
    
    # Çapraz lag'lar (SMF varsa)
    if "smf" in df.columns:
        for lag in [1, 24]:
            df[f"smf_lag_{lag}h"] = df["smf"].shift(lag)
    
    if "spread" in df.columns:
        df["spread_lag_24h"] = df["spread"].shift(24)
    
    return df


def _add_rolling_features(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """
    Yuvarlanan (rolling) pencere istatistikleri üretir.
    min_periods kullanarak kısmi pencereler de hesaplanır.
    """
    windows = [6, 12, 24, 48, 168]
    
    for w in windows:
        # Ortalama
        df[f"roll_mean_{w}h"] = df[target_col].shift(1).rolling(window=w, min_periods=1).mean()
        
        # Standart sapma (volatilite)
        df[f"roll_std_{w}h"] = df[target_col].shift(1).rolling(window=w, min_periods=2).std()
        
        # Min/Max (sadece büyük pencereler için)
        if w >= 24:
            df[f"roll_min_{w}h"] = df[target_col].shift(1).rolling(window=w, min_periods=1).min()
            df[f"roll_max_{w}h"] = df[target_col].shift(1).rolling(window=w, min_periods=1).max()
    
    # Ratio: mevcut lag vs rolling ortalama
    if "lag_1h" in df.columns:
        df["price_vs_24h_avg"] = df["lag_1h"] / (df["roll_mean_24h"] + 1e-8)
    
    return df


def _add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Takvim bazlı öznitelikler üretir."""
    dt = df["datetime"]
    
    # Temel zamansal öznitelikler
    df["hour"] = dt.dt.hour
    df["day_of_week"] = dt.dt.dayofweek  # 0=Pazartesi, 6=Pazar
    df["day_of_month"] = dt.dt.day
    df["month"] = dt.dt.month
    df["week_of_year"] = dt.dt.isocalendar().week.astype(int)
    
    # İkili göstergeler
    df["is_weekend"] = (dt.dt.dayofweek >= 5).astype(np.uint8)
    df["is_night"] = ((dt.dt.hour >= 22) | (dt.dt.hour <= 6)).astype(np.uint8)
    df["is_peak_hour"] = ((dt.dt.hour >= 8) & (dt.dt.hour <= 20)).astype(np.uint8)
    
    # Türkiye resmi tatilleri
    df["is_holiday"] = df["datetime"].apply(
        lambda x: int((x.month, x.day) in HOLIDAYS_TR)
    ).astype(np.uint8)
    
    # Tatil veya hafta sonu
    df["is_off_day"] = ((df["is_weekend"] == 1) | (df["is_holiday"] == 1)).astype(np.uint8)
    
    # Sinüzoidal saat kodlaması (döngüsel yapıyı yakalamak için)
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24).astype(np.float32)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24).astype(np.float32)
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7).astype(np.float32)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7).astype(np.float32)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12).astype(np.float32)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12).astype(np.float32)
    
    return df



def _add_diff_features(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """Fark (değişim) öznitelikleri üretir."""
    # Saatlik fark
    df["diff_1h"] = df[target_col].diff(1)
    
    # Günlük fark (aynı saat bir gün önce)
    df["diff_24h"] = df[target_col].diff(24)
    
    # Haftalık fark
    df["diff_168h"] = df[target_col].diff(168)
    
    # Yüzdesel değişim
    df["pct_change_1h"] = df[target_col].pct_change(1).astype(np.float32)
    df["pct_change_24h"] = df[target_col].pct_change(24).astype(np.float32)
    
    return df


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    """Model eğitiminde kullanılacak öznitelik sütunlarını döndürür."""
    exclude_cols = {"datetime", "ptf", "smf", "spread"}
    return [col for col in df.columns if col not in exclude_cols]
