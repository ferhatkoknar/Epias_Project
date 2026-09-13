"""
EPİAŞ GÖP PTF Fiyat Tahmini — Proje Konfigürasyonu
Tüm sabitler, API ayarları, model parametreleri ve UI konfigürasyonu burada tanımlanır.
"""

import os
from pathlib import Path
from datetime import datetime, timedelta

# ─────────────────────────── Dizin Yapısı ───────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CACHE_DIR = DATA_DIR / "cache"
MODELS_DIR = PROJECT_ROOT / "models"

# ─────────────────────────── EPİAŞ API Ayarları ───────────────────────────
API_CONFIG = {
    "start_date": "2024-01-01",
    "end_date": datetime.now().strftime("%Y-%m-%d"),
    "timezone": "Europe/Istanbul",
    "retry_count": 3,
    "retry_delay_seconds": 5,
    "cache_expiry_hours": 24,
}

# ─────────────────────────── Öznitelik Mühendisliği ───────────────────────────
FEATURE_CONFIG = {
    # Gecikme (Lag) özellikleri
    "lag_hours": [1, 2, 3, 6, 12, 24, 48, 168],  # t-1 ... t-168 (1 hafta)
    
    # Hareketli ortalamalar
    "rolling_windows": [6, 12, 24, 48, 168],
    
    # Takvim özellikleri
    "calendar_features": ["hour", "day_of_week", "month", "is_weekend", "is_holiday"],
    
    # Türkiye resmi tatilleri (sabit tarihler)
    "holidays_tr": [
        (1, 1),   # Yılbaşı
        (4, 23),  # Ulusal Egemenlik
        (5, 1),   # Emek ve Dayanışma
        (5, 19),  # Atatürk'ü Anma
        (7, 15),  # Demokrasi ve Milli Birlik
        (8, 30),  # Zafer Bayramı
        (10, 29), # Cumhuriyet Bayramı
    ],
}

# ─────────────────────────── Model Parametreleri ───────────────────────────
MODEL_CONFIG = {
    "catboost": {
        "iterations": 1000,
        "learning_rate": 0.05,
        "depth": 6,
        "l2_leaf_reg": 3,
        "random_seed": 42,
        "verbose": 100,
        "early_stopping_rounds": 50,
        "loss_function": "RMSE",
    },
    "lightgbm": {
        "n_estimators": 1000,
        "learning_rate": 0.05,
        "max_depth": 6,
        "num_leaves": 31,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "random_state": 42,
        "verbose": -1,
        "early_stopping_rounds": 50,
    },
    # Walk-Forward validasyon
    "time_series_splits": 5,
    "test_size_days": 30,
    
    # Kabul kriterleri (SRS)
    "acceptance_criteria": {
        "mape_threshold": 12.0,        # MAPE < %12
        "directional_accuracy": 70.0,   # Yön doğruluğu > %70
        "inference_time_ms": 500,       # Inference < 500ms
    },
}

# ─────────────────────────── Trading Simülasyonu ───────────────────────────
TRADING_CONFIG = {
    "default_position_mwh": 10,          # Varsayılan pozisyon hacmi
    "default_threshold_tl": 2500,        # Varsayılan alış eşiği (TL/MWh)
    "commission_rate": 0.001,            # İşlem komisyonu
    "risk_coefficient_range": (0.5, 2.0), # Risk katsayısı aralığı
}

# ─────────────────────────── UI Konfigürasyonu ───────────────────────────
UI_CONFIG = {
    "page_title": "EPİAŞ GÖP PTF Tahmin & Trading Terminali",
    "page_icon": "⚡",
    "layout": "wide",
    
    # Renk paleti
    "colors": {
        "bg_primary": "#0E1117",
        "bg_secondary": "#1A1F2E",
        "bg_card": "#162032",
        "accent_green": "#00D4AA",
        "accent_blue": "#4A9EFF",
        "accent_amber": "#FFB800",
        "accent_red": "#FF4444",
        "profit": "#00E676",
        "loss": "#FF5252",
        "text_primary": "#FAFAFA",
        "text_secondary": "#8B95A5",
        "border": "rgba(255, 255, 255, 0.06)",
        "glass_bg": "rgba(22, 32, 50, 0.6)",
    },
    
    # Plotly tema
    "plotly_template": "plotly_dark",
    "chart_height": 450,
    "chart_colors": ["#00D4AA", "#4A9EFF", "#FFB800", "#FF5252", "#BB86FC"],
}
