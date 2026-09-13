"""
Önbellek Yöneticisi (NFR-02 — Fallback)
API bağlantısında gecikme yaşandığında yerel Parquet dosyalarından veri okur.
"""

import logging
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
CACHE_DIR = PROJECT_ROOT / "data" / "cache"


class CacheManager:
    """Parquet tabanlı yerel veri önbelleği."""
    
    def __init__(self, cache_dir: Path = CACHE_DIR, expiry_hours: int = 24):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.expiry_hours = expiry_hours
    
    def get(self, key: str) -> pd.DataFrame | None:
        """Önbellekten veri okur. Süresi dolmuşsa None döndürür."""
        cache_path = self.cache_dir / f"{key}.parquet"
        
        if not cache_path.exists():
            logger.debug(f"Önbellek bulunamadı: {key}")
            return None
        
        # Süre kontrolü
        file_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        if file_age > timedelta(hours=self.expiry_hours):
            logger.info(f"Önbellek süresi dolmuş: {key} ({file_age.total_seconds()/3600:.1f}h)")
            return None
        
        df = pd.read_parquet(cache_path)
        logger.info(f"Önbellekten okundu: {key} ({len(df)} satır)")
        return df
    
    def put(self, key: str, df: pd.DataFrame) -> None:
        """Veriyi önbelleğe kaydeder."""
        cache_path = self.cache_dir / f"{key}.parquet"
        df.to_parquet(cache_path, engine="pyarrow")
        logger.info(f"Önbelleğe kaydedildi: {key} ({len(df)} satır)")
    
    def get_or_fetch(self, key: str, fetch_fn, *args, **kwargs) -> pd.DataFrame:
        """
        Önbellekte varsa okur, yoksa fetch_fn ile çeker ve kaydeder.
        Fallback mekanizması: API başarısız olursa son geçerli veriyi kullanır.
        """
        # Önce önbelleği kontrol et
        cached = self.get(key)
        if cached is not None:
            return cached
        
        # API'den çekmeyi dene
        try:
            df = fetch_fn(*args, **kwargs)
            self.put(key, df)
            return df
        except Exception as e:
            logger.error(f"Veri çekme hatası: {e}")
            
            # Fallback: süresi dolmuş olsa bile son veriyi kullan
            cache_path = self.cache_dir / f"{key}.parquet"
            if cache_path.exists():
                df = pd.read_parquet(cache_path)
                logger.warning(f"Fallback: eski önbellek kullanılıyor ({len(df)} satır)")
                return df
            
            raise RuntimeError(f"Veri alınamadı ve önbellek yok: {key}") from e
    
    def clear(self) -> None:
        """Tüm önbelleği temizler."""
        for f in self.cache_dir.glob("*.parquet"):
            f.unlink()
            logger.info(f"Önbellek silindi: {f.name}")
    
    def list_cached(self) -> list[dict]:
        """Önbellekteki dosyaları listeler."""
        entries = []
        for f in self.cache_dir.glob("*.parquet"):
            age = datetime.now() - datetime.fromtimestamp(f.stat().st_mtime)
            entries.append({
                "key": f.stem,
                "size_kb": f.stat().st_size / 1024,
                "age_hours": age.total_seconds() / 3600,
                "expired": age > timedelta(hours=self.expiry_hours),
            })
        return entries
