"""
Veri Temizleme Modülü
Eksik veri tespiti, enterpolasyon, aykırı değer filtreleme ve zaman damgası hizalama.
NFR-01: float32 dönüşümü ile hafıza optimizasyonu.
"""

import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def clean_market_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Piyasa verisini temizler ve standartlaştırır.
    
    İşlemler:
    1. Zaman damgası hizalama (UTC → Europe/Istanbul)
    2. Eksik saatlerin tespiti ve enterpolasyonla doldurulması
    3. Aykırı değer filtreleme (IQR yöntemi)
    4. float32 dönüşümü (RAM optimizasyonu)
    
    Args:
        df: Ham piyasa verisi DataFrame
    
    Returns:
        Temizlenmiş DataFrame
    """
    df = df.copy()
    
    # 1. Datetime sütununu standartlaştır
    df = _standardize_datetime(df)
    
    # 2. Eksik saatleri doldur
    df = _fill_missing_hours(df)
    
    # 2b. Henüz kesinleşmemiş SMF gibi uç değerleri son bilinen değerle tamamla
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].ffill().bfill()
    
    # 3. Aykırı değerleri temizle
    for col in numeric_cols:
        df = _handle_outliers(df, col)
    
    # 4. float32 dönüşümü (hafıza optimizasyonu — NFR-01)
    df = _optimize_memory(df)
    
    # 5. Sıralama
    df = df.sort_values("datetime").reset_index(drop=True)
    
    logger.info(f"Veri temizlendi: {len(df)} satır, {df.memory_usage().sum() / 1024:.1f} KB")
    return df


def _standardize_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """Zaman damgasını Europe/Istanbul'a hizalar."""
    if "datetime" not in df.columns:
        # Olası datetime sütun isimlerini dene
        for col in ["date", "tarih", "timestamp", "Tarih"]:
            if col in df.columns:
                df = df.rename(columns={col: "datetime"})
                break
    
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"])
        
        # Timezone kontrolü
        if df["datetime"].dt.tz is None:
            df["datetime"] = df["datetime"].dt.tz_localize("Europe/Istanbul")
        else:
            df["datetime"] = df["datetime"].dt.tz_convert("Europe/Istanbul")
    
    return df


def _fill_missing_hours(df: pd.DataFrame) -> pd.DataFrame:
    """
    Eksik saatleri tespit eder ve enterpolasyonla doldurur.
    Tam bir saatlik zaman serisi oluşturur.
    """
    if "datetime" not in df.columns:
        return df
    
    # Tam saatlik aralık oluştur
    full_range = pd.date_range(
        start=df["datetime"].min(),
        end=df["datetime"].max(),
        freq="h",
        tz="Europe/Istanbul"
    )
    
    # Eksik saatleri bul
    existing = set(df["datetime"])
    missing = [t for t in full_range if t not in existing]
    
    if missing:
        logger.warning(f"{len(missing)} eksik saat tespit edildi. Enterpolasyon uygulanıyor...")
        
        # Tam indeks ile reindex
        df = df.set_index("datetime").reindex(full_range)
        df.index.name = "datetime"
        
        # Numerik sütunları enterpolasyonla doldur
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].interpolate(method="time")
        
        # Kalan NaN'leri forward/backward fill
        df = df.ffill().bfill()
        df = df.reset_index()
    
    return df


def _handle_outliers(df: pd.DataFrame, column: str, factor: float = 3.0) -> pd.DataFrame:
    """
    IQR yöntemiyle aykırı değerleri tespit eder ve clip'ler.
    Enerji fiyatlarında meşru spike'lar olabileceği için agresif filtreleme yapılmaz.
    """
    if column not in df.columns:
        return df
    
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - factor * IQR
    upper_bound = Q3 + factor * IQR
    
    outlier_count = ((df[column] < lower_bound) | (df[column] > upper_bound)).sum()
    
    if outlier_count > 0:
        logger.info(f"'{column}': {outlier_count} aykırı değer clip'lendi [{lower_bound:.0f}, {upper_bound:.0f}]")
        df[column] = df[column].clip(lower=lower_bound, upper=upper_bound)
    
    return df


def _optimize_memory(df: pd.DataFrame) -> pd.DataFrame:
    """
    Numerik sütunları float32'ye dönüştürür.
    NFR-01: 1 GB RAM sınırına uyum.
    """
    for col in df.select_dtypes(include=[np.float64]).columns:
        df[col] = df[col].astype(np.float32)
    
    for col in df.select_dtypes(include=[np.int64]).columns:
        if df[col].min() >= 0 and df[col].max() < 65535:
            df[col] = df[col].astype(np.uint16)
        else:
            df[col] = df[col].astype(np.int32)
    
    return df
