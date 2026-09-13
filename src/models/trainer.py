"""
Model Eğitim Modülü (FR-03)
CatBoost ve LightGBM modellerini Walk-Forward validasyonla eğitir.
"""

import logging
import time
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"


def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame = None,
    y_val: pd.Series = None,
    model_type: str = "catboost",
    params: dict = None,
) -> object:
    """
    Seçilen model tipini eğitir.
    
    Args:
        X_train: Eğitim öznitelikleri
        y_train: Eğitim hedef değişkeni
        X_val: Validasyon öznitelikleri (opsiyonel)
        y_val: Validasyon hedef değişkeni (opsiyonel)
        model_type: 'catboost' veya 'lightgbm'
        params: Model hiperparametreleri
    
    Returns:
        Eğitilmiş model nesnesi
    """
    start = time.time()
    
    if model_type == "catboost":
        model = _train_catboost(X_train, y_train, X_val, y_val, params)
    elif model_type == "lightgbm":
        model = _train_lightgbm(X_train, y_train, X_val, y_val, params)
    else:
        raise ValueError(f"Bilinmeyen model tipi: {model_type}")
    
    elapsed = time.time() - start
    logger.info(f"{model_type} eğitimi tamamlandı: {elapsed:.1f}s")
    
    return model


def _train_catboost(X_train, y_train, X_val, y_val, params):
    """CatBoost regresyon modeli eğitir."""
    from catboost import CatBoostRegressor, Pool
    
    default_params = {
        "iterations": 1000,
        "learning_rate": 0.05,
        "depth": 6,
        "l2_leaf_reg": 3,
        "random_seed": 42,
        "verbose": 100,
        "loss_function": "RMSE",
        "thread_count": -1,
    }
    
    if params:
        default_params.update(params)
    
    model = CatBoostRegressor(**default_params)
    
    eval_set = None
    if X_val is not None and y_val is not None:
        eval_set = Pool(X_val, y_val)
        model.set_params(early_stopping_rounds=50)
    
    model.fit(
        X_train, y_train,
        eval_set=eval_set,
        verbose=default_params.get("verbose", 100),
    )
    
    return model


def _train_lightgbm(X_train, y_train, X_val, y_val, params):
    """LightGBM regresyon modeli eğitir."""
    import lightgbm as lgb
    
    default_params = {
        "n_estimators": 1000,
        "learning_rate": 0.05,
        "max_depth": 6,
        "num_leaves": 31,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "random_state": 42,
        "verbose": -1,
        "n_jobs": -1,
    }
    
    if params:
        default_params.update(params)
    
    early_stopping = default_params.pop("early_stopping_rounds", 50)
    
    model = lgb.LGBMRegressor(**default_params)
    
    callbacks = [lgb.log_evaluation(100)]
    if X_val is not None and y_val is not None:
        callbacks.append(lgb.early_stopping(early_stopping))
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            callbacks=callbacks,
        )
    else:
        model.fit(X_train, y_train)
    
    return model


def save_model(model: object, name: str) -> Path:
    """Eğitilmiş modeli .joblib formatında kaydeder."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = MODELS_DIR / f"{name}.joblib"
    joblib.dump(model, path)
    logger.info(f"Model kaydedildi: {path}")
    return path


def load_model(name: str) -> object:
    """Kaydedilmiş modeli yükler."""
    path = MODELS_DIR / f"{name}.joblib"
    if not path.exists():
        raise FileNotFoundError(f"Model bulunamadı: {path}")
    
    model = joblib.load(path)
    logger.info(f"Model yüklendi: {path}")
    return model


def get_feature_importance(model: object, feature_names: list[str], model_type: str = "catboost") -> pd.DataFrame:
    """Model öznitelik önem sıralamasını döndürür."""
    if model_type == "catboost":
        importances = model.get_feature_importance()
    elif model_type == "lightgbm":
        importances = model.feature_importances_
    else:
        return pd.DataFrame()
    
    fi = pd.DataFrame({
        "feature": feature_names,
        "importance": importances,
    }).sort_values("importance", ascending=False).reset_index(drop=True)
    
    # Normalize
    fi["importance_pct"] = (fi["importance"] / fi["importance"].sum() * 100).round(2)
    
    return fi
