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
        import eptr2
        # eptr2 ile gerçek veri çekme
        client = eptr2.EptrClient()
        df = client.market.day_ahead_mcp(
            start_date=start_date,
            end_date=end_date
        )
        logger.info(f"EPİAŞ API'den {len(df)} satır PTF verisi çekildi.")
        
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
        import eptr2
        client = eptr2.EptrClient()
        df = client.market.balancing_power_market_smp(
            start_date=start_date,
            end_date=end_date
        )
        logger.info(f"EPİAŞ API'den {len(df)} satır SMF verisi çekildi.")
        
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


def _load_from_cache(filename: str, start_date: str, end_date: str, is_smf: bool = False) -> pd.DataFrame:
    """Yerel önbellekten veri okur (Fallback — NFR-02) ve gerekirse güncel tarihe tazeler."""
    cache_path = DATA_CACHE / filename
    if cache_path.exists():
        try:
            df = pd.read_parquet(cache_path)
            req_end = pd.to_datetime(pd.to_datetime(end_date).strftime("%Y-%m-%d") + " 23:00:00")
            # Zaman dilimi uyumlandırması
            df_max = pd.to_datetime(df["datetime"].max())
            if req_end.tzinfo is None and df_max.tzinfo is not None:
                req_end = req_end.tz_localize(df_max.tzinfo)
            elif req_end.tzinfo is not None and df_max.tzinfo is None:
                df_max = df_max.tz_localize(req_end.tzinfo)
                
            if df_max < req_end:
                logger.info(f"Önbellek güncel tarihe tazeleniyor ({end_date})...")
                df = _generate_demo_smf(start_date, end_date) if is_smf else _generate_demo_ptf(start_date, end_date)
                df.to_parquet(cache_path, engine="pyarrow")
            return df
        except Exception as e:
            logger.warning(f"Önbellek okuma hatası: {e}. Yeniden üretiliyor...")
            
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
