"""
P&L Trading Simülatörü (FR-07)
Kullanıcı tanımlı eşik kuralına göre geçmişe dönük kâr/zarar simülasyonu yapar.
"""

import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def run_backtest(
    actual_ptf: np.ndarray,
    predicted_ptf: np.ndarray,
    datetimes: pd.DatetimeIndex,
    threshold_tl: float = 2500,
    position_mwh: float = 10,
    commission_rate: float = 0.001,
    strategy: str = "momentum",
    risk_coefficient: float = 1.0,
) -> pd.DataFrame:
    """
    Basit trading stratejisi ile geçmişe dönük P&L simülasyonu.
    
    Strateji: 
    - Model Tahmini > Eşik → ALIŞ pozisyonu (fiyat yüksek, sat)
    - Model Tahmini < Eşik → Pozisyon alma
    
    Args:
        actual_ptf: Gerçekleşen PTF fiyatları
        predicted_ptf: Model tahminleri
        datetimes: Zaman damgaları
        threshold_tl: Alış/satış eşiği (TL/MWh)
        position_mwh: Pozisyon hacmi (MWh)
        commission_rate: İşlem komisyonu oranı
        strategy: 'momentum' veya 'mean_reversion'
        risk_coefficient: Risk katsayısı (pozisyon boyutlandırma)
    
    Returns:
        DataFrame: datetime, signal, pnl, cumulative_pnl, position
    """
    n = len(actual_ptf)
    
    signals = np.zeros(n)
    pnl = np.zeros(n)
    positions = np.zeros(n)
    
    adjusted_position = position_mwh * risk_coefficient
    
    for i in range(1, n):
        if strategy == "momentum":
            # Momentum: Tahmin yüksekse AL (fiyat artacak beklentisi)
            if predicted_ptf[i] > threshold_tl:
                signals[i] = 1  # ALIŞ
                # Kâr/zarar = (gerçek fiyat - önceki fiyat) × pozisyon
                price_diff = actual_ptf[i] - actual_ptf[i - 1]
                pnl[i] = price_diff * adjusted_position
            elif predicted_ptf[i] < threshold_tl * 0.95:
                signals[i] = -1  # SATIŞ
                price_diff = actual_ptf[i - 1] - actual_ptf[i]
                pnl[i] = price_diff * adjusted_position
            else:
                signals[i] = 0  # BEKLEMede
                
        elif strategy == "mean_reversion":
            # Mean reversion: Tahmin ortalamanın üstündeyse SAT
            avg = np.mean(predicted_ptf[max(0, i-24):i])
            if predicted_ptf[i] > avg * 1.05:
                signals[i] = -1
                price_diff = actual_ptf[i - 1] - actual_ptf[i]
                pnl[i] = price_diff * adjusted_position
            elif predicted_ptf[i] < avg * 0.95:
                signals[i] = 1
                price_diff = actual_ptf[i] - actual_ptf[i - 1]
                pnl[i] = price_diff * adjusted_position
        
        # Komisyon düş
        if signals[i] != 0:
            commission = abs(pnl[i]) * commission_rate
            pnl[i] -= commission
        
        positions[i] = signals[i] * adjusted_position
    
    cumulative_pnl = np.cumsum(pnl)
    
    result = pd.DataFrame({
        "datetime": datetimes[:n],
        "actual_ptf": actual_ptf,
        "predicted_ptf": predicted_ptf,
        "signal": signals,
        "position_mwh": positions,
        "pnl": pnl.astype(np.float32),
        "cumulative_pnl": cumulative_pnl.astype(np.float32),
    })
    
    logger.info(f"Backtest tamamlandı: {n} bar, toplam P&L = {cumulative_pnl[-1]:,.0f} TL")
    return result


def calculate_trading_metrics(backtest_df: pd.DataFrame) -> dict:
    """
    Trading performans metriklerini hesaplar.
    """
    pnl = backtest_df["pnl"]
    cum_pnl = backtest_df["cumulative_pnl"]
    signals = backtest_df["signal"]
    
    trades = signals != 0
    winning_trades = (pnl > 0) & trades
    losing_trades = (pnl < 0) & trades
    
    total_trades = trades.sum()
    win_count = winning_trades.sum()
    loss_count = losing_trades.sum()
    
    # Maksimum drawdown
    peak = cum_pnl.cummax()
    drawdown = cum_pnl - peak
    max_drawdown = drawdown.min()
    max_drawdown_pct = (max_drawdown / (peak.max() + 1e-8)) * 100 if peak.max() > 0 else 0
    
    # Sharpe benzeri oran (saatlik)
    if pnl[trades].std() > 0:
        sharpe = (pnl[trades].mean() / pnl[trades].std()) * np.sqrt(24 * 365)
    else:
        sharpe = 0
    
    # Profit factor
    gross_profit = pnl[pnl > 0].sum()
    gross_loss = abs(pnl[pnl < 0].sum())
    profit_factor = gross_profit / (gross_loss + 1e-8)
    
    metrics = {
        "total_pnl": float(cum_pnl.iloc[-1]) if len(cum_pnl) > 0 else 0,
        "total_trades": int(total_trades),
        "winning_trades": int(win_count),
        "losing_trades": int(loss_count),
        "win_rate": float(win_count / total_trades * 100) if total_trades > 0 else 0,
        "avg_win": float(pnl[winning_trades].mean()) if win_count > 0 else 0,
        "avg_loss": float(pnl[losing_trades].mean()) if loss_count > 0 else 0,
        "max_drawdown_tl": float(max_drawdown),
        "max_drawdown_pct": float(max_drawdown_pct),
        "sharpe_ratio": float(sharpe),
        "profit_factor": float(profit_factor),
        "gross_profit": float(gross_profit),
        "gross_loss": float(gross_loss),
    }
    
    return metrics


def simulate_market_shock(
    backtest_df: pd.DataFrame,
    shock_type: str = "gas_spike",
    shock_pct: float = 0.25,
) -> pd.DataFrame:
    """
    Piyasa stres testi: Ani fiyat soklarinda strateji saglamligini olcer.
    
    Args:
        backtest_df: Orijinal backtest sonuclari
        shock_type: 'gas_spike' (ani gaz kesintisi/puant artisi), 
                    'renewable_surge' (ani yenilenebilir arzi/taban baskisi), 
                    'volatility_shock' (oynaklik soku)
        shock_pct: Sok buyuklugu (orn. 0.25 = %25)
    """
    df = backtest_df.copy()
    shocked_ptf = df["actual_ptf"].copy().values
    
    dts = pd.to_datetime(df["datetime"])
    hours = dts.dt.hour.values
    
    if shock_type == "gas_spike":
        mask = (hours >= 8) & (hours <= 20)
        shocked_ptf[mask] = shocked_ptf[mask] * (1.0 + shock_pct)
    elif shock_type == "renewable_surge":
        shocked_ptf = np.maximum(0, shocked_ptf * (1.0 - shock_pct))
    elif shock_type == "volatility_shock":
        rng = np.random.default_rng(42)
        noise = rng.normal(0, shock_pct, len(shocked_ptf))
        shocked_ptf = np.maximum(0, shocked_ptf * (1.0 + noise))
        
    df["shocked_actual_ptf"] = shocked_ptf
    shocked_pnl = np.zeros(len(df))
    signals = df["signal"].values
    positions = df["position_mwh"].values
    
    for i in range(1, len(df)):
        sig = signals[i]
        pos = abs(positions[i])
        if sig == 1:
            shocked_pnl[i] = (shocked_ptf[i] - shocked_ptf[i - 1]) * pos
        elif sig == -1:
            shocked_pnl[i] = (shocked_ptf[i - 1] - shocked_ptf[i]) * pos
            
    df["shocked_pnl"] = shocked_pnl
    df["shocked_cumulative_pnl"] = np.cumsum(shocked_pnl)
    return df
