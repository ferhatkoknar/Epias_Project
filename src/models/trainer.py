"""
Model Eğitim Modülü (FR-03)
CatBoost ve LightGBM modellerini Walk-Forward validasyonla eğitir.
"""

import logging
import time
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*eval_set.*")

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"


class EnsembleModel:
    """CatBoost ve LightGBM modellerini agirlikli birlestiren Topluluk (Ensemble) Modeli."""
    def __init__(self, catboost_model, lightgbm_model, weights=(0.5, 0.5)):
        self.catboost = catboost_model
        self.lightgbm = lightgbm_model
        self.weights = weights
        
    def predict(self, X):
        pred_cb = np.array(self.catboost.predict(X))
        pred_lgb = np.array(self.lightgbm.predict(X))
        return self.weights[0] * pred_cb + self.weights[1] * pred_lgb
        
    def get_feature_importance(self):
        fi_cb = np.array(self.catboost.get_feature_importance(), dtype=float)
        fi_cb = fi_cb / (np.sum(fi_cb) + 1e-9)
        fi_lgb = np.array(self.lightgbm.feature_importances_, dtype=float)
        fi_lgb = fi_lgb / (np.sum(fi_lgb) + 1e-9)
        return self.weights[0] * fi_cb + self.weights[1] * fi_lgb


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
        model_type: 'catboost', 'lightgbm' veya 'ensemble'
        params: Model hiperparametreleri
    
    Returns:
        Eğitilmiş model nesnesi
    """
    start = time.time()
    
    if model_type == "catboost":
        model = _train_catboost(X_train, y_train, X_val, y_val, params)
    elif model_type == "lightgbm":
        model = _train_lightgbm(X_train, y_train, X_val, y_val, params)
    elif model_type == "ensemble":
        cb = _train_catboost(X_train, y_train, X_val, y_val, params)
        lgb = _train_lightgbm(X_train, y_train, X_val, y_val, params)
        model = EnsembleModel(cb, lgb, weights=(0.5, 0.5))
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
        callbacks.append(lgb.early_stopping(early_stopping, verbose=False))
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore")
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
    elif model_type == "ensemble" or hasattr(model, "get_feature_importance"):
        try:
            importances = model.get_feature_importance()
        except Exception:
            importances = np.ones(len(feature_names)) / len(feature_names)
    else:
        return pd.DataFrame()
    
    fi = pd.DataFrame({
        "feature": feature_names,
        "importance": importances,
    }).sort_values("importance", ascending=False).reset_index(drop=True)
    
    # Normalize
    fi["importance_pct"] = (fi["importance"] / fi["importance"].sum() * 100).round(2)
    
    return fi


def train_and_save_all_models(save: bool = True) -> dict:
    """
    CatBoost, LightGBM ve Ensemble modellerini eğitir, test seti üzerinde değerlendirir
    ve istenirse models/ dizinine .joblib formatında kaydeder.
    """
    from src.data.fetcher import fetch_all_market_data
    from src.data.cleaner import clean_market_data
    from src.features.time_features import create_time_features, get_feature_columns
    from src.features.market_features import create_market_features
    from src.models.evaluator import evaluate_model
    
    print("=" * 65)
    print("  EPİAŞ GÖP PTF MODEL EĞİTİM & DOĞRULAMA MOTORU (CLI)")
    print("=" * 65)
    
    # 1. Veri yükle & Öznitelikler
    print("\n[1/4] Piyasa verileri yükleniyor ve causal öznitelikler üretiliyor...")
    raw_df = fetch_all_market_data("2024-01-01")
    clean_df = clean_market_data(raw_df)
    feat_df = create_time_features(clean_df)
    feat_df = create_market_features(feat_df)
    feature_cols = get_feature_columns(feat_df)
    print(f"      Toplam Satır: {len(feat_df)}, Öznitelik Sayısı: {len(feature_cols)}")
    
    # 2. Train / Val / Test Ayrımı
    print("\n[2/4] Veri seti ayrıştırılıyor (Son 30 gün Test, %10 Val)...")
    test_size = 30 * 24
    train_df = feat_df.iloc[:-test_size]
    test_df = feat_df.iloc[-test_size:]
    
    X_train_full = train_df[feature_cols]
    y_train_full = train_df["ptf"]
    X_test = test_df[feature_cols]
    y_test = test_df["ptf"].values
    
    val_size = max(1, int(len(train_df) * 0.1))
    X_val = X_train_full.iloc[-val_size:]
    y_val = y_train_full.iloc[-val_size:]
    X_train = X_train_full.iloc[:-val_size]
    y_train = y_train_full.iloc[:-val_size]
    
    # 3. Model Eğitimi
    print("\n[3/4] Modeller eğitiliyor (CatBoost & LightGBM)...")
    # CatBoost
    t0 = time.time()
    cb_model = train_model(X_train, y_train, X_val, y_val, model_type="catboost", params={"iterations": 800, "verbose": 0})
    cb_time = time.time() - t0
    
    t0 = time.time()
    cb_preds = cb_model.predict(X_test)
    cb_infer_ms = ((time.time() - t0) * 1000) / (len(X_test) / 24)
    cb_metrics = evaluate_model(y_test, cb_preds)
    cb_metrics["train_time_s"] = cb_time
    cb_metrics["infer_time_24h_ms"] = cb_infer_ms
    
    # LightGBM
    t0 = time.time()
    lgb_model = train_model(X_train, y_train, X_val, y_val, model_type="lightgbm", params={"n_estimators": 800, "verbose": -1})
    lgb_time = time.time() - t0
    
    t0 = time.time()
    lgb_preds = lgb_model.predict(X_test)
    lgb_infer_ms = ((time.time() - t0) * 1000) / (len(X_test) / 24)
    lgb_metrics = evaluate_model(y_test, lgb_preds)
    lgb_metrics["train_time_s"] = lgb_time
    lgb_metrics["infer_time_24h_ms"] = lgb_infer_ms
    
    # Ensemble
    ens_model = EnsembleModel(cb_model, lgb_model, weights=(0.5, 0.5))
    t0 = time.time()
    ens_preds = ens_model.predict(X_test)
    ens_infer_ms = ((time.time() - t0) * 1000) / (len(X_test) / 24)
    ens_metrics = evaluate_model(y_test, ens_preds)
    ens_metrics["train_time_s"] = cb_time + lgb_time
    ens_metrics["infer_time_24h_ms"] = ens_infer_ms
    
    # 4. Modelleri Kaydet
    saved_paths = {}
    if save:
        print("\n[4/4] Eğitilmiş ağırlıklar models/ klasörüne kaydediliyor...")
        saved_paths["catboost"] = str(save_model(cb_model, "catboost_model"))
        saved_paths["lightgbm"] = str(save_model(lgb_model, "lightgbm_model"))
        saved_paths["ensemble"] = str(save_model(ens_model, "ensemble_model"))
        print(f"      [KAYIT] CatBoost  -> {saved_paths['catboost']}")
        print(f"      [KAYIT] LightGBM  -> {saved_paths['lightgbm']}")
        print(f"      [KAYIT] Ensemble  -> {saved_paths['ensemble']}")
    
    # Sonuç Tablosu
    print("\n" + "=" * 92)
    print(f"{'Model':<12} | {'WAPE (%)':<10} | {'MAPE (%)':<10} | {'Yön Doğ.':<10} | {'MAE (TL)':<10} | {'RMSE (TL)':<10} | {'24s Infer'}")
    print("-" * 92)
    for name, m in [("CatBoost", cb_metrics), ("LightGBM", lgb_metrics), ("Ensemble", ens_metrics)]:
        w = m.get('wape', m['mape'])
        status_wape = "[OK]" if w < 12.0 else "[FAIL]"
        status_da = "[OK]" if m['directional_accuracy'] > 70.0 else "[FAIL]"
        print(f"{name:<12} | %{w:<5.2f} {status_wape} | %{m['mape']:<5.2f}        | %{m['directional_accuracy']:<5.2f} {status_da} | {m['mae']:<10.2f} | {m['rmse']:<10.2f} | {m['infer_time_24h_ms']:<6.2f} ms")
    print("=" * 92)
    print("SRS KABUL KRİTERLERİ KONTROLÜ:")
    ens_wape = ens_metrics.get('wape', ens_metrics['mape'])
    print(f"  * Hacim Ağırlıklı WAPE < %12.0    : {'BAŞARILI' if ens_wape < 12.0 else 'BAŞARISIZ'} (%{ens_wape:.2f})")
    print(f"  * Aritmetik Test MAPE             : %{ens_metrics['mape']:.2f}")
    print(f"  * Yön Doğruluğu > %70.0           : {'BAŞARILI' if ens_metrics['directional_accuracy'] > 70.0 else 'BAŞARISIZ'} (%{ens_metrics['directional_accuracy']:.2f})")
    print(f"  * Test MAE                        : {ens_metrics['mae']:.2f} TL")
    print(f"  * Test RMSE                       : {ens_metrics['rmse']:.2f} TL")
    print(f"  * 24s Çıkarım Süresi < 500 ms     : {'BAŞARILI' if ens_metrics['infer_time_24h_ms'] < 500 else 'BAŞARISIZ'} ({ens_metrics['infer_time_24h_ms']:.2f} ms)")
    print("=" * 92 + "\n")
    
    return {
        "catboost": (cb_model, cb_metrics),
        "lightgbm": (lgb_model, lgb_metrics),
        "ensemble": (ens_model, ens_metrics),
        "saved_paths": saved_paths,
    }


if __name__ == "__main__":
    train_and_save_all_models(save=True)

