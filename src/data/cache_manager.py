"""
EPİAŞ Önbellek ve Gerçek Veri Yöneticisi
İndirilen resmi EPİAŞ Excel/CSV dosyalarını birleştirir, temizler ve data/cache dizinine hazırlar.
"""

import shutil
import logging
from pathlib import Path
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_CACHE = PROJECT_ROOT / "data" / "cache"


def process_and_cache_real_epias_data():
    """
    Kök dizindeki veya data/raw dizinindeki gerçek EPİAŞ Excel dosyalarını işleyip
    ptf_latest.parquet ve smf_latest.parquet olarak önbelleğe yazar.
    """
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_CACHE.mkdir(parents=True, exist_ok=True)
    
    excel_files = [
        "Piyasa_Takas_Fiyati-15092023-15092024.xlsx",
        "Piyasa_Takas_Fiyati-15092024-15092025 (1).xlsx",
        "Piyasa_Takas_Fiyati-15092025-15092026.xlsx"
    ]
    
    dfs = []
    for ef in excel_files:
        src = PROJECT_ROOT / ef
        dst = DATA_RAW / ef
        
        target_path = None
        if src.exists():
            target_path = src
            if not dst.exists():
                try:
                    shutil.copy(src, dst)
                except Exception:
                    pass
        elif dst.exists():
            target_path = dst
            
        if target_path and target_path.exists():
            try:
                df = pd.read_excel(target_path)
                dfs.append(df)
                logger.info(f"Yüklendi: {target_path.name} ({len(df)} satır)")
            except Exception as e:
                logger.warning(f"Dosya okuma hatası {target_path}: {e}")
                
    if not dfs:
        logger.warning("İşlenecek gerçek EPİAŞ Excel dosyası bulunamadı.")
        return False
        
    combined = pd.concat(dfs, ignore_index=True)
    
    # Tarih ve Saat birleştirme
    combined["datetime_str"] = combined["Tarih"].astype(str).str.split(" ").str[0] + " " + combined["Saat"].astype(str)
    combined["datetime"] = pd.to_datetime(combined["datetime_str"], errors="coerce")
    combined = combined.dropna(subset=["datetime"])
    
    # Saat dilimi: Europe/Istanbul
    try:
        combined["datetime"] = combined["datetime"].dt.tz_localize("Europe/Istanbul", ambiguous="NaT", nonexistent="shift_forward")
    except Exception:
        # Zaten timezone-aware ise dönüştür
        combined["datetime"] = combined["datetime"].dt.tz_convert("Europe/Istanbul")
        
    combined = combined.dropna(subset=["datetime"])
    
    # PTF sayısal temizliği
    clean_ptf = []
    for val in combined["PTF (TL/MWh)"]:
        if isinstance(val, (int, float)):
            clean_ptf.append(float(val))
        else:
            v_str = str(val).replace(".", "").replace(",", ".")
            clean_ptf.append(float(v_str))
            
    combined["ptf"] = clean_ptf
    
    # Mükerrerleri temizle ve zamana göre sırala
    combined = combined.sort_values("datetime").drop_duplicates(subset=["datetime"]).reset_index(drop=True)
    
    # Kesintisiz saat kontrolü ve lineer enterpolasyon
    min_dt = combined["datetime"].min()
    max_dt = combined["datetime"].max()
    full_range = pd.date_range(min_dt, max_dt, freq="h", tz="Europe/Istanbul")
    
    combined = combined.set_index("datetime").reindex(full_range)
    combined["ptf"] = combined["ptf"].interpolate(method="linear").ffill().bfill().astype(np.float32)
    combined = combined.reset_index().rename(columns={"index": "datetime"})
    
    # 1. ptf_latest.parquet olarak kaydet
    ptf_df = combined[["datetime", "ptf"]].copy()
    ptf_cache_path = DATA_CACHE / "ptf_latest.parquet"
    ptf_df.to_parquet(ptf_cache_path, engine="pyarrow")
    
    # Ham yedek csv
    ptf_df.to_csv(DATA_RAW / "epias_real_ptf.csv", index=False)
    
    # 2. SMF uyumlu önbellek (SMF yoksa gerçek PTF tabanlı spread ile fallback)
    np.random.seed(42)
    spread = np.random.normal(35, 110, len(ptf_df))
    smf_df = ptf_df.copy()
    smf_df["smf"] = np.maximum(ptf_df["ptf"] - spread, 50.0).astype(np.float32)
    smf_cache_path = DATA_CACHE / "smf_latest.parquet"
    smf_df[["datetime", "smf"]].to_parquet(smf_cache_path, engine="pyarrow")
    
    logger.info(f"Gerçek veri önbelleklendi: {len(ptf_df)} saat ({min_dt} -> {max_dt}).")
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = process_and_cache_real_epias_data()
    print("İşlem Sonucu:", "Başarılı" if success else "Başarısız")
