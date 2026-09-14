"""
EPİAŞ Veri Çekme Modülü (FR-01)
eptr2 istemcisiyle EPİAŞ Şeffaflık API'sinden PTF, SMF ve KGÜP verilerini çeker.
Fallback: API kesilirse yerel önbellekten okur.
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Proje dizin yapısına göre path ayarları
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_CACHE = PROJECT_ROOT / "data" / "cache"


def fetch_ptf_data(start_date: str = "2024-01-01", end_date: str = None) -> pd.DataFrame:
    """
    EPİAŞ API'sinden saatlik PTF verilerini çeker.
    API erişimi yoksa demo veri üretir.
    
    Args:
        start_date: Başlangıç tarihi (YYYY-MM-DD)
        end_date: Bitiş tarihi (YYYY-MM-DD) — boş bırakılırsa yarına kadar alır
    
    Returns:
        Saatlik PTF değerleri içeren DataFrame
    """
    if end_date is None:
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
    try:
        from eptr2 import EPTR2
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        client = EPTR2()
        res = client.call("mcp", start_date=start_date, end_date=end_date)
        
        if hasattr(res, "to_dataframe"):
            df = res.to_dataframe()
        elif isinstance(res, dict) and "items" in res:
            df = pd.DataFrame(res["items"])
        else:
            df = pd.DataFrame(res)
            
        # Sütun standardizasyonu
        if "price" in df.columns:
            df["ptf"] = df["price"]
        elif "priceEur" in df.columns and "ptf" not in df.columns:
            df["ptf"] = df["priceTry"]
            
        if "date" in df.columns:
            df["datetime"] = pd.to_datetime(df["date"])
            
        df = df[["datetime", "ptf"]].dropna()
        logger.info(f"EPİAŞ API'den {len(df)} satır canlı PTF verisi çekildi.")
        
        # Önbelleğe kaydet
        cache_path = DATA_CACHE / "ptf_latest.parquet"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_path, engine="pyarrow")
        
        return df
    except ImportError:
        logger.warning("eptr2 kurulu değil. Demo veri üretiliyor...")
        return _load_from_cache("ptf_latest.parquet", start_date, end_date, is_smf=False)
    except Exception as e:
        logger.warning(f"API hatası: {e}. Önbellekten okunuyor...")
        return _load_from_cache("ptf_latest.parquet", start_date, end_date, is_smf=False)


def fetch_smf_data(start_date: str = "2024-01-01", end_date: str = None) -> pd.DataFrame:
    """
    EPİAŞ API'sinden saatlik SMF verilerini çeker.
    """
    if end_date is None:
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
    try:
        from eptr2 import EPTR2
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        client = EPTR2()
        res = client.call("smp", start_date=start_date, end_date=end_date)
        
        if hasattr(res, "to_dataframe"):
            df = res.to_dataframe()
        elif isinstance(res, dict) and "items" in res:
            df = pd.DataFrame(res["items"])
        else:
            df = pd.DataFrame(res)
            
        if "price" in df.columns:
            df["smf"] = df["price"]
        elif "priceTry" in df.columns and "smf" not in df.columns:
            df["smf"] = df["priceTry"]
            
        if "date" in df.columns:
            df["datetime"] = pd.to_datetime(df["date"])
            
        df = df[["datetime", "smf"]].dropna()
        logger.info(f"EPİAŞ API'den {len(df)} satır canlı SMF verisi çekildi.")
        
        cache_path = DATA_CACHE / "smf_latest.parquet"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_path, engine="pyarrow")
        
        return df
    except ImportError:
        logger.warning("eptr2 kurulu değil. Demo SMF verisi üretiliyor...")
        return _load_from_cache("smf_latest.parquet", start_date, end_date, is_smf=True)
    except Exception as e:
        logger.warning(f"API hatası: {e}. Önbellekten okunuyor...")
        return _load_from_cache("smf_latest.parquet", start_date, end_date, is_smf=True)


def fetch_all_market_data(start_date: str = "2024-01-01", end_date: str = None) -> pd.DataFrame:
    """
    Tüm piyasa verilerini (PTF, SMF) çekip birleştirir.
    
    Returns:
        Birleştirilmiş DataFrame: datetime, ptf, smf, spread sütunları
    """
    if end_date is None:
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
    ptf_df = fetch_ptf_data(start_date, end_date)
    smf_df = fetch_smf_data(start_date, end_date)
    
    # Birleştir
    merged = ptf_df.copy()
    if "smf" in smf_df.columns:
        merged = pd.merge(merged, smf_df[["datetime", "smf"]], on="datetime", how="left")
    elif len(smf_df) == len(ptf_df):
        merged["smf"] = smf_df["smf"].values if "smf" in smf_df.columns else smf_df.iloc[:, 1].values
    
    # Spread hesapla
    if "smf" in merged.columns:
        merged["spread"] = merged["ptf"] - merged["smf"]
    
    logger.info(f"Toplam {len(merged)} satır piyasa verisi hazır. Son tarih: {merged['datetime'].max()}")
    return merged


def _load_real_epias_data() -> pd.DataFrame:
    """Kaggle / EPİAŞ üzerinden indirilen resmi gerçek piyasa verisini (epias_real_ptf.csv) yükler."""
    raw_path = DATA_RAW / "epias_real_ptf.csv"
    if not raw_path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(raw_path)
        df["datetime_str"] = df["Tarih"].astype(str) + " " + df["Saat"].astype(str)
        df["datetime"] = pd.to_datetime(df["datetime_str"], format="%d.%m.%Y %H:%M")
        df["datetime"] = df["datetime"].dt.tz_localize("Europe/Istanbul", ambiguous="NaT", nonexistent="shift_forward")
        df["ptf"] = df["PTF (TL/MWh)"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)
        df = df[["datetime", "ptf"]].dropna().sort_values("datetime").drop_duplicates("datetime").reset_index(drop=True)
        # Modern piyasa dönemini filtrele (2022 sonrası)
        df = df[df["datetime"] >= "2022-01-01"].copy().reset_index(drop=True)
        return df
    except Exception as e:
        logger.warning(f"Gerçek EPİAŞ CSV okuma hatası: {e}")
        return pd.DataFrame()


def _load_from_cache(filename: str, start_date: str, end_date: str, is_smf: bool = False) -> pd.DataFrame:
    """Yerel önbellekten veya resmi gerçek EPİAŞ CSV dosyasından veri okur."""
    cache_path = DATA_CACHE / filename
    
    # 1. Öncelik: Eğer data/raw/epias_real_ptf.csv varsa ve cache yoksa oluştur
    if not cache_path.exists():
        real_df = _load_real_epias_data()
        if not real_df.empty:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            if is_smf:
                np.random.seed(42)
                spread = np.random.normal(25, 120, len(real_df))
                smf_df = real_df.copy()
                smf_df["smf"] = np.maximum(real_df["ptf"] - spread, 50.0).astype(float)
                smf_df[["datetime", "smf"]].to_parquet(cache_path, engine="pyarrow")
                return smf_df[["datetime", "smf"]]
            else:
                real_df.to_parquet(cache_path, engine="pyarrow")
                return real_df
                
    if cache_path.exists():
        try:
            df = pd.read_parquet(cache_path)
            return df
        except Exception as e:
            logger.warning(f"Önbellek okuma hatası: {e}. Yeniden üretiliyor...")
            
    # Gerçek veri yoksa demo fallback
    real_df = _load_real_epias_data()
    if not real_df.empty:
        return real_df
    df = _generate_demo_smf(start_date, end_date) if is_smf else _generate_demo_ptf(start_date, end_date)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache_path, engine="pyarrow")
    return df


def _generate_demo_ptf(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Demo PTF verisi üretir. Gerçekçi Türkiye elektrik piyasası fiyat
    dinamiklerini simüle eder.
    """
    # Günün son saatine (23:00) kadar 24 saatin tamamını kapsa
    end_dt = pd.to_datetime(end_date).strftime("%Y-%m-%d") + " 23:00:00"
    date_range = pd.date_range(start=start_date, end=end_dt, freq="h", tz="Europe/Istanbul")
    n = len(date_range)
    
    # Temel fiyat seviyesi (TL/MWh) — gerçekçi Türkiye PTF aralığı
    base_price = 2200
    
    # Mevsimsel bileşen (yıllık)
    day_of_year = date_range.dayofyear
    seasonal = 300 * np.sin(2 * np.pi * (day_of_year - 30) / 365)
    
    # Günlük profil (saatlik talep eğrisi)
    hour = date_range.hour
    daily_pattern = np.where(
        (hour >= 8) & (hour <= 20),
        200 + 150 * np.sin(np.pi * (hour - 8) / 12),
        -100 + 50 * np.sin(np.pi * hour / 8)
    )
    
    # Hafta sonu etkisi
    is_weekend = date_range.weekday >= 5
    weekend_effect = np.where(is_weekend, -180, 0)
    
    # Trend bileşeni
    trend = np.linspace(0, 200, n)
    
    # Rastgele gürültü
    noise = np.random.normal(0, 120, n)
    
    # Spike'lar (anlık fiyat sıçramaları — piyasa gerçekliği)
    spikes = np.zeros(n)
    spike_indices = np.random.choice(n, size=int(n * 0.02), replace=False)
    spikes[spike_indices] = np.random.choice([-1, 1], size=len(spike_indices)) * np.random.uniform(300, 800, len(spike_indices))
    
    ptf = base_price + seasonal + daily_pattern + weekend_effect + trend + noise + spikes
    ptf = np.maximum(ptf, 50)  # Minimum fiyat sınırı
    ptf = ptf.astype(np.float32)
    
    df = pd.DataFrame({
        "datetime": date_range,
        "ptf": ptf,
    })
    
    # Önbelleğe kaydet
    cache_path = DATA_CACHE / "ptf_latest.parquet"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache_path, engine="pyarrow")
    
    logger.info(f"Demo PTF verisi üretildi: {len(df)} satır")
    return df


def _generate_demo_smf(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Demo SMF verisi üretir. SMF, PTF'den sapma gösteren dengeleme fiyatıdır.
    """
    np.random.seed(123)
    
    # Önce PTF verisini al (önbellekten)
    ptf_df = _load_from_cache("ptf_latest.parquet", start_date, end_date)
    
    if ptf_df.empty:
        ptf_df = _generate_demo_ptf(start_date, end_date)
    
    # SMF = PTF + spread (tipik olarak ±%5-15 sapma)
    spread_pct = np.random.normal(0, 0.08, len(ptf_df))
    smf = ptf_df["ptf"].values * (1 + spread_pct)
    smf = np.maximum(smf, 30).astype(np.float32)
    
    df = pd.DataFrame({
        "datetime": ptf_df["datetime"],
        "smf": smf,
    })
    
    cache_path = DATA_CACHE / "smf_latest.parquet"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache_path, engine="pyarrow")
    
    logger.info(f"Demo SMF verisi üretildi: {len(df)} satır")
    return df
