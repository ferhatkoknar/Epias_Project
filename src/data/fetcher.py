"""
EPİAŞ Veri Çekme Modülü (FR-01)
eptr2 ve EPİAŞ CAS/TGT REST servisleri ile Şeffaflık Platformu'ndan canlı veri çeker.
API kimlik bilgisi girilmediğinde temiz bir şablon (NaN) döner.
"""

import os
import logging
import pandas as pd
import numpy as np
import requests
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_CACHE = PROJECT_ROOT / "data" / "cache"


def get_epias_credentials():
    """Çevre değişkenlerinden veya .env dosyasından EPİAŞ kullanıcı bilgilerini alır."""
    load_dotenv(override=True)
    username = os.getenv("EPTR_USERNAME") or os.getenv("EPTR2_USERNAME")
    password = os.getenv("EPTR_PASSWORD") or os.getenv("EPTR2_PASSWORD")
    if username and password and username.strip() and password.strip():
        return username.strip(), password.strip()
    return None, None


def get_tgt_token(username: str, password: str) -> str:
    """EPİAŞ CAS servisinden 2 saat geçerli TGT erişim anahtarı alır."""
    try:
        auth_url = "https://giris.epias.com.tr/cas/v1/tickets"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/plain"
        }
        res = requests.post(auth_url, data={"username": username, "password": password}, headers=headers, timeout=10)
        if res.status_code == 201:
            return res.text.strip()
        logger.warning(f"EPİAŞ CAS kimlik doğrulama yanıtı: HTTP {res.status_code}")
    except Exception as e:
        logger.warning(f"EPİAŞ CAS bağlantı hatası: {e}")
    return None


def fetch_ptf_data(start_date: str = "2024-01-01", end_date: str = None) -> pd.DataFrame:
    """
    EPİAŞ API'sinden saatlik PTF verilerini çeker.
    API erişimi yoksa şablon (NaN) döner.
    """
    if end_date is None:
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
    username, password = get_epias_credentials()
    if username and password:
        # 1. Yöntem: EPTR2 kütüphanesi
        try:
            from eptr2 import EPTR2
            client = EPTR2()
            res = client.call("mcp", start_date=start_date, end_date=end_date)
            if hasattr(res, "to_dataframe"):
                df = res.to_dataframe()
            elif isinstance(res, dict) and "items" in res:
                df = pd.DataFrame(res["items"])
            else:
                df = pd.DataFrame(res)
                
            if "price" in df.columns:
                df["ptf"] = df["price"]
            elif "priceEur" in df.columns and "ptf" not in df.columns:
                df["ptf"] = df["priceTry"]
                
            if "date" in df.columns:
                df["datetime"] = pd.to_datetime(df["date"])
                
            df = df[["datetime", "ptf"]].dropna()
            if not df.empty:
                logger.info(f"EPİAŞ API'den {len(df)} satır canlı PTF verisi çekildi.")
                cache_path = DATA_CACHE / "ptf_latest.parquet"
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_parquet(cache_path, engine="pyarrow")
                return df
        except Exception as e:
            logger.warning(f"EPTR2 çağrısı başarısız: {e}. Doğrudan CAS deneniyor...")
            
        # 2. Yöntem: Doğrudan EPİAŞ REST API (TGT ile)
        try:
            tgt = get_tgt_token(username, password)
            if tgt:
                url = "https://seffaflik.epias.com.tr/reporting-service/v1/data/daily-prices"
                headers = {"TGT": tgt, "Content-Type": "application/json"}
                body = {
                    "startDate": f"{start_date}T00:00:00+03:00",
                    "endDate": f"{end_date}T23:00:00+03:00"
                }
                r = requests.post(url, json=body, headers=headers, timeout=15)
                if r.status_code == 200:
                    items = r.json().get("items", [])
                    if items:
                        df = pd.DataFrame(items)
                        if "date" in df.columns and "price" in df.columns:
                            df["datetime"] = pd.to_datetime(df["date"])
                            df["ptf"] = df["price"].astype(float)
                            df = df[["datetime", "ptf"]].dropna()
                            cache_path = DATA_CACHE / "ptf_latest.parquet"
                            cache_path.parent.mkdir(parents=True, exist_ok=True)
                            df.to_parquet(cache_path, engine="pyarrow")
                            return df
        except Exception as e:
            logger.warning(f"Doğrudan EPİAŞ REST API hatası: {e}")

    # Önbellek varsa oku, yoksa şablon (NaN) dön
    return _load_from_cache("ptf_latest.parquet", start_date, end_date, is_smf=False)


def fetch_smf_data(start_date: str = "2024-01-01", end_date: str = None) -> pd.DataFrame:
    """EPİAŞ API'sinden saatlik SMF verilerini çeker."""
    if end_date is None:
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
    username, password = get_epias_credentials()
    if username and password:
        try:
            from eptr2 import EPTR2
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
            if not df.empty:
                logger.info(f"EPİAŞ API'den {len(df)} satır canlı SMF verisi çekildi.")
                cache_path = DATA_CACHE / "smf_latest.parquet"
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_parquet(cache_path, engine="pyarrow")
                return df
        except Exception as e:
            logger.warning(f"SMF çekme hatası: {e}")

    return _load_from_cache("smf_latest.parquet", start_date, end_date, is_smf=True)


def fetch_all_market_data(start_date: str = "2024-01-01", end_date: str = None) -> pd.DataFrame:
    """Tüm piyasa verilerini (PTF, SMF) çekip birleştirir."""
    if end_date is None:
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
    ptf_df = fetch_ptf_data(start_date, end_date)
    smf_df = fetch_smf_data(start_date, end_date)
    
    merged = ptf_df.copy()
    if "smf" in smf_df.columns:
        merged = pd.merge(merged, smf_df[["datetime", "smf"]], on="datetime", how="left")
    else:
        merged["smf"] = np.nan
        
    merged["spread"] = merged["ptf"] - merged["smf"]
    return merged


def _load_from_cache(filename: str, start_date: str, end_date: str, is_smf: bool = False) -> pd.DataFrame:
    """Yerel önbellekten veri okur, önbellek yoksa gerçek veriyi işleyip okur."""
    cache_path = DATA_CACHE / filename
    if not cache_path.exists():
        try:
            from src.data.cache_manager import process_and_cache_real_epias_data
            process_and_cache_real_epias_data()
        except Exception as e:
            logger.warning(f"Gerçek veri önbellekleme hatası: {e}")
            
    if cache_path.exists():
        try:
            return pd.read_parquet(cache_path)
        except Exception as e:
            logger.warning(f"Önbellek okuma hatası: {e}")
            
    # API yok ve dosya yoksa: boş şablon dön (Asla sahte rastgele sayı üretilmez)
    return _create_template_data(start_date, end_date, is_smf=is_smf)


def _create_template_data(start_date: str, end_date: str, is_smf: bool = False) -> pd.DataFrame:
    """API bağlantısı beklenirken arayüz şablonunun ayakta kalmasını sağlayan NaN serisi."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    date_range = pd.date_range(start=f"{today_str} 00:00:00", periods=24, freq="h", tz="Europe/Istanbul")
    val_col = "smf" if is_smf else "ptf"
    return pd.DataFrame({
        "datetime": date_range,
        val_col: np.nan
    })
