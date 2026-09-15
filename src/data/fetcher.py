"""
EPİAŞ Veri Çekme Modülü (FR-01)
eptr2 ve EPİAŞ CAS/TGT REST servisleri ile Şeffaflık Platformu'ndan canlı veri çeker.
3 yıllık gerçek veriyi Parquet önbelleğinde korur; canlı API çağrılarında yalnızca eksik günleri çekip önbelleğe ekler (upsert).
API kimlik bilgisi girilmediğinde yerel önbellekten veya temiz şablondan (NaN) kesintisiz devam eder.
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
    """Çevre değişkenlerinden veya .env dosyasından EPİAŞ Şeffaflık 2.0 kullanıcı bilgilerini alır."""
    load_dotenv(override=True)
    username = (
        os.getenv("EPIAS_USERNAME")
        or os.getenv("EPTR_USERNAME")
        or os.getenv("EPTR2_USERNAME")
    )
    password = (
        os.getenv("EPIAS_PASSWORD")
        or os.getenv("EPTR_PASSWORD")
        or os.getenv("EPTR2_PASSWORD")
    )
    if username and password and username.strip() and password.strip():
        return username.strip(), password.strip()
    return None, None


_TGT_CACHE = {"token": None, "expires_at": None}


def get_tgt_token(username: str, password: str) -> str:
    """EPİAŞ CAS servisinden 2 saat geçerli TGT erişim anahtarı alır ve oturumu önbellekler."""
    global _TGT_CACHE
    now = datetime.now()
    if _TGT_CACHE["token"] and _TGT_CACHE["expires_at"] and now < _TGT_CACHE["expires_at"]:
        return _TGT_CACHE["token"]

    try:
        auth_url = "https://giris.epias.com.tr/cas/v1/tickets"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/plain"
        }
        res = requests.post(auth_url, data={"username": username, "password": password}, headers=headers, timeout=10)
        if res.status_code == 201:
            token = res.text.strip()
            _TGT_CACHE["token"] = token
            _TGT_CACHE["expires_at"] = now + timedelta(minutes=105)
            logger.info("EPİAŞ CAS oturumu başarıyla açıldı, TGT bileti alındı.")
            return token
        logger.warning(f"EPİAŞ CAS kimlik doğrulama yanıtı: HTTP {res.status_code}")
    except Exception as e:
        logger.warning(f"EPİAŞ CAS bağlantı hatası: {e}")
    return None


def _filter_by_date(df: pd.DataFrame, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """Zaman dilimi uyumlu tarih aralığı filtreleme."""
    if df is None or df.empty or "datetime" not in df.columns:
        return df
    res = df.copy()
    tz = res["datetime"].dt.tz
    if start_date:
        st_dt = pd.to_datetime(start_date)
        if st_dt.tzinfo is None and tz is not None:
            st_dt = st_dt.tz_localize(tz)
        res = res[res["datetime"] >= st_dt]
    if end_date:
        end_dt = pd.to_datetime(end_date)
        if end_dt.tzinfo is None and tz is not None:
            end_dt = end_dt.tz_localize(tz)
        # Gün sonuna kadar dahil et (23:59:59)
        end_dt = end_dt + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        res = res[res["datetime"] <= end_dt]
    return res.reset_index(drop=True)


def _merge_into_parquet(cache_path: Path, new_df: pd.DataFrame) -> pd.DataFrame:
    """Mevcut Parquet önbelleği ile yeni çekilen veriyi birleştirir (upsert). Asla geçmiş veriyi silmez."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if not cache_path.exists():
        new_df.to_parquet(cache_path, engine="pyarrow")
        return new_df

    try:
        old_df = pd.read_parquet(cache_path)
        # Zaman dilimi uyumunu güvenceye al
        if old_df["datetime"].dt.tz is not None and new_df["datetime"].dt.tz is not None:
            if str(old_df["datetime"].dt.tz) != str(new_df["datetime"].dt.tz):
                new_df["datetime"] = new_df["datetime"].dt.tz_convert(old_df["datetime"].dt.tz)
        combined = pd.concat([old_df, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["datetime"], keep="last")
        combined = combined.sort_values("datetime").reset_index(drop=True)
        combined.to_parquet(cache_path, engine="pyarrow")
        return combined
    except Exception as e:
        logger.warning(f"Önbellek birleştirme hatası: {e}")
        return new_df


def _fetch_live_ptf_api(start_date: str, end_date: str, username: str, password: str) -> pd.DataFrame:
    """EPİAŞ REST API veya EPTR2 ile canlı PTF çeker."""
    # 1. Doğrudan EPİAŞ Şeffaflık 2.0 REST API
    try:
        tgt = get_tgt_token(username, password)
        if tgt:
            url = "https://seffaflik.epias.com.tr/electricity-service/v1/markets/dam/data/mcp"
            headers = {"TGT": tgt, "Content-Type": "application/json", "Accept": "application/json"}
            body = {
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
            }
            r = requests.post(url, json=body, headers=headers, timeout=12)
            if r.status_code == 200:
                resp_json = r.json()
                items = resp_json.get("items", []) if isinstance(resp_json, dict) else resp_json
                if items:
                    df = pd.DataFrame(items)
                    if "date" in df.columns:
                        df["datetime"] = pd.to_datetime(df["date"])
                        if df["datetime"].dt.tz is None:
                            df["datetime"] = df["datetime"].dt.tz_localize("Europe/Istanbul")
                        else:
                            df["datetime"] = df["datetime"].dt.tz_convert("Europe/Istanbul")
                        if "price" in df.columns:
                            df["ptf"] = df["price"].astype(np.float32)
                        elif "priceTry" in df.columns:
                            df["ptf"] = df["priceTry"].astype(np.float32)
                        return df[["datetime", "ptf"]].dropna()
    except Exception as e:
        logger.warning(f"Doğrudan REST MCP çekme hatası: {e}. eptr2 deneniyor...")

    # 2. EPTR2 İstemcisi
    try:
        from eptr2 import EPTR2
        client = EPTR2(username=username, password=password)
        res = client.call("mcp", start_date=start_date, end_date=end_date)
        df = res.to_dataframe() if hasattr(res, "to_dataframe") else pd.DataFrame(res)
        if "price" in df.columns:
            df["ptf"] = df["price"].astype(np.float32)
        elif "priceTry" in df.columns:
            df["ptf"] = df["priceTry"].astype(np.float32)
        if "date" in df.columns:
            df["datetime"] = pd.to_datetime(df["date"])
            if df["datetime"].dt.tz is None:
                df["datetime"] = df["datetime"].dt.tz_localize("Europe/Istanbul")
            else:
                df["datetime"] = df["datetime"].dt.tz_convert("Europe/Istanbul")
        return df[["datetime", "ptf"]].dropna()
    except Exception as e:
        logger.warning(f"EPTR2 MCP çekme hatası: {e}")

    return pd.DataFrame()


def _fetch_live_smf_api(start_date: str, end_date: str, username: str, password: str) -> pd.DataFrame:
    """EPİAŞ REST API veya EPTR2 ile canlı SMF çeker."""
    # 1. Doğrudan EPİAŞ Şeffaflık 2.0 REST API
    try:
        tgt = get_tgt_token(username, password)
        if tgt:
            url = "https://seffaflik.epias.com.tr/electricity-service/v1/markets/bpm/data/system-marginal-price"
            headers = {"TGT": tgt, "Content-Type": "application/json", "Accept": "application/json"}
            body = {
                "startDate": f"{start_date}T00:00:00+03:00",
                "endDate": f"{end_date}T23:00:00+03:00"
            }
            r = requests.post(url, json=body, headers=headers, timeout=12)
            if r.status_code == 200:
                resp_json = r.json()
                items = resp_json.get("items", []) if isinstance(resp_json, dict) else resp_json
                if items:
                    df = pd.DataFrame(items)
                    if "date" in df.columns:
                        df["datetime"] = pd.to_datetime(df["date"])
                        if df["datetime"].dt.tz is None:
                            df["datetime"] = df["datetime"].dt.tz_localize("Europe/Istanbul")
                        else:
                            df["datetime"] = df["datetime"].dt.tz_convert("Europe/Istanbul")
                        if "price" in df.columns:
                            df["smf"] = df["price"].astype(np.float32)
                        elif "systemMarginalPrice" in df.columns:
                            df["smf"] = df["systemMarginalPrice"].astype(np.float32)
                        elif "priceTry" in df.columns:
                            df["smf"] = df["priceTry"].astype(np.float32)
                        elif "smp" in df.columns:
                            df["smf"] = df["smp"].astype(np.float32)
                        return df[["datetime", "smf"]].dropna()
    except Exception as e:
        logger.warning(f"Doğrudan REST SMP çekme hatası: {e}. eptr2 deneniyor...")

    # 2. EPTR2 İstemcisi
    try:
        from eptr2 import EPTR2
        client = EPTR2(username=username, password=password)
        res = client.call("smp", start_date=start_date, end_date=end_date)
        df = res.to_dataframe() if hasattr(res, "to_dataframe") else pd.DataFrame(res)
        if "price" in df.columns:
            df["smf"] = df["price"].astype(np.float32)
        elif "systemMarginalPrice" in df.columns:
            df["smf"] = df["systemMarginalPrice"].astype(np.float32)
        elif "priceTry" in df.columns:
            df["smf"] = df["priceTry"].astype(np.float32)
        elif "smp" in df.columns:
            df["smf"] = df["smp"].astype(np.float32)
        if "date" in df.columns:
            df["datetime"] = pd.to_datetime(df["date"])
            if df["datetime"].dt.tz is None:
                df["datetime"] = df["datetime"].dt.tz_localize("Europe/Istanbul")
            else:
                df["datetime"] = df["datetime"].dt.tz_convert("Europe/Istanbul")
        return df[["datetime", "smf"]].dropna()
    except Exception as e:
        logger.warning(f"EPTR2 SMP çekme hatası: {e}")

    return pd.DataFrame()


def fetch_ptf_data(start_date: str = "2024-01-01", end_date: str = None) -> pd.DataFrame:
    """
    EPİAŞ PTF verilerini çeker.
    Mevcut 3 yıllık önbelleği korur; API kimliği varsa yalnızca eksik günleri (delta) çekip önbelleğe ekler.
    """
    cache_path = DATA_CACHE / "ptf_latest.parquet"
    if not cache_path.exists():
        try:
            from src.data.cache_manager import process_and_cache_real_epias_data
            process_and_cache_real_epias_data()
        except Exception as e:
            logger.warning(f"Önbellek hazırlama hatası: {e}")

    base_df = pd.DataFrame()
    if cache_path.exists():
        try:
            base_df = pd.read_parquet(cache_path)
        except Exception as e:
            logger.warning(f"PTF önbellek okuma hatası: {e}")

    if end_date is None:
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # API ile canlı delta senkronizasyonu
    username, password = get_epias_credentials()
    if username and password:
        try:
            if not base_df.empty and "datetime" in base_df.columns:
                max_dt = base_df["datetime"].max()
                delta_start = (max_dt - timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                delta_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

            # Yalnızca delta penceresi çekilir (maksimum birkaç gün)
            if delta_start <= end_date:
                live_df = _fetch_live_ptf_api(delta_start, end_date, username, password)
                if not live_df.empty:
                    base_df = _merge_into_parquet(cache_path, live_df)
                    logger.info(f"EPİAŞ canlı PTF güncellendi: {len(live_df)} satır eklendi.")
        except Exception as e:
            logger.warning(f"Canlı PTF senkronizasyon hatası: {e}")

    if not base_df.empty:
        return _filter_by_date(base_df, start_date, end_date)

    return _create_template_data(start_date, end_date, is_smf=False)


def fetch_smf_data(start_date: str = "2024-01-01", end_date: str = None) -> pd.DataFrame:
    """
    EPİAŞ SMF verilerini çeker.
    SMF verisi yalnızca düne kadar olan günleri içerir.
    """
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    if end_date is None or end_date > yesterday:
        end_date = yesterday

    cache_path = DATA_CACHE / "smf_latest.parquet"
    base_df = pd.DataFrame()
    if cache_path.exists():
        try:
            base_df = pd.read_parquet(cache_path)
        except Exception as e:
            logger.warning(f"SMF önbellek okuma hatası: {e}")

    username, password = get_epias_credentials()
    if username and password:
        try:
            if not base_df.empty and "datetime" in base_df.columns:
                max_dt = base_df["datetime"].max()
                delta_start = (max_dt - timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                delta_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

            if delta_start <= end_date:
                live_df = _fetch_live_smf_api(delta_start, end_date, username, password)
                if not live_df.empty:
                    base_df = _merge_into_parquet(cache_path, live_df)
                    logger.info(f"EPİAŞ canlı SMF güncellendi: {len(live_df)} satır eklendi.")
        except Exception as e:
            logger.warning(f"Canlı SMF senkronizasyon hatası: {e}")

    if not base_df.empty:
        return _filter_by_date(base_df, start_date, end_date)

    return _create_template_data(start_date, end_date, is_smf=True)


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


def _create_template_data(start_date: str, end_date: str, is_smf: bool = False) -> pd.DataFrame:
    """API bağlantısı beklenirken veya veri yokken arayüzün çökmesini önleyen boş şablon."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    date_range = pd.date_range(start=f"{today_str} 00:00:00", periods=24, freq="h", tz="Europe/Istanbul")
    val_col = "smf" if is_smf else "ptf"
    return pd.DataFrame({
        "datetime": date_range,
        val_col: np.nan
    })
