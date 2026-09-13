"""
Walk-Forward Validasyon Modülü (FR-03)
Zaman serisi validasyonunu zamansal sırayı bozmadan TimeSeriesSplit ile yapar.
Data Leakage engeli: Geleceğe ait veri kesinlikle eğitimde kullanılmaz.
"""

import logging
import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

logger = logging.getLogger(__name__)


def walk_forward_validate(
    df: pd.DataFrame,
    feature_columns: list[str],
    target_column: str = "ptf",
    model_type: str = "catboost",
    n_splits: int = 5,
    model_params: dict = None,
) -> dict:
    """
    Walk-Forward (genişleyen pencere) validasyonu uygular.
    
    Her fold'da:
    - Eğitim: t=0 ... t=k
    - Test: t=k+1 ... t=k+n
    - Zamansal sıra ASLA bozulmaz
    
    Args:
        df: Öznitelik matrisi + hedef değişken
        feature_columns: Kullanılacak öznitelik sütunları
        target_column: Hedef değişken sütunu
        n_splits: Fold sayısı
        model_type: 'catboost' veya 'lightgbm'
        model_params: Model hiperparametreleri
    
    Returns:
        Fold bazında metrikler ve en iyi model
    """
    from src.models.trainer import train_model
    from src.models.evaluator import evaluate_model
    
    X = df[feature_columns]
    y = df[target_column]
    
    tscv = TimeSeriesSplit(n_splits=n_splits)
    
    fold_results = []
    all_predictions = []
    all_actuals = []
    best_model = None
    best_mape = float("inf")
    
    logger.info(f"Walk-Forward validasyon başlıyor: {n_splits} fold, model={model_type}")
    
    for fold_idx, (train_idx, test_idx) in enumerate(tscv.split(X)):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Son %10'unu validasyon olarak ayır
        val_size = max(1, int(len(X_train) * 0.1))
        X_val = X_train.iloc[-val_size:]
        y_val = y_train.iloc[-val_size:]
        X_train_final = X_train.iloc[:-val_size]
        y_train_final = y_train.iloc[:-val_size]
        
        # Model eğit
        model = train_model(
            X_train_final, y_train_final,
            X_val, y_val,
            model_type=model_type,
            params=model_params,
        )
        
        # Tahmin ve değerlendirme
        predictions = model.predict(X_test)
        metrics = evaluate_model(y_test.values, predictions)
        
        fold_result = {
            "fold": fold_idx + 1,
            "train_size": len(X_train_final),
            "val_size": val_size,
            "test_size": len(X_test),
            **metrics,
        }
        fold_results.append(fold_result)
        
        all_predictions.extend(predictions)
        all_actuals.extend(y_test.values)
        
        # En iyi modeli sakla
        if metrics["mape"] < best_mape:
            best_mape = metrics["mape"]
            best_model = model
        
        logger.info(
            f"  Fold {fold_idx+1}/{n_splits}: "
            f"MAPE={metrics['mape']:.2f}%, "
            f"RMSE={metrics['rmse']:.1f}, "
            f"DA={metrics['directional_accuracy']:.1f}%"
        )
    
    # Genel metrikler
    overall_metrics = evaluate_model(np.array(all_actuals), np.array(all_predictions))
    
    results = {
        "folds": fold_results,
        "overall": overall_metrics,
        "best_model": best_model,
        "fold_summary": pd.DataFrame(fold_results),
        "n_splits": n_splits,
        "model_type": model_type,
    }
    
    logger.info(
        f"Walk-Forward tamamlandı. Genel MAPE={overall_metrics['mape']:.2f}%, "
        f"DA={overall_metrics['directional_accuracy']:.1f}%"
    )
    
    return results


def expanding_window_split(n_samples: int, min_train_size: int, test_size: int) -> list[tuple]:
    """
    Özel genişleyen pencere bölümleri oluşturur.
    
    Args:
        n_samples: Toplam örnek sayısı
        min_train_size: Minimum eğitim boyutu
        test_size: Her fold'daki test boyutu
    
    Returns:
        (train_indices, test_indices) tuple listesi
    """
    splits = []
    start = min_train_size
    
    while start + test_size <= n_samples:
        train_idx = np.arange(0, start)
        test_idx = np.arange(start, min(start + test_size, n_samples))
        splits.append((train_idx, test_idx))
        start += test_size
    
    return splits
