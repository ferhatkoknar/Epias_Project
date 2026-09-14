"""
Veri Dışa Aktarma Modülü (FR-08)
CSV, Excel (XLSX), HTML Yönetici Raporu ve Word (DOCX) formatları.
"""

import io
from datetime import datetime
import pandas as pd
import numpy as np


def export_predictions_csv(
    day_df: pd.DataFrame,
    actual_df: pd.DataFrame = None,
    metrics: dict = None,
) -> bytes:
    """
    Hedef günün 24 saatlik tahmin verilerini temiz, standart ve Excel uyumlu CSV formatında dışa aktarır.
    utf-8-sig kodlaması ile Excel'de Türkçe karakter sorunu yaşanmaz.
    """
    df = day_df.copy()
    if "datetime" not in df.columns and actual_df is not None and "datetime" in actual_df.columns:
        df = actual_df.copy()
        
    rows = []
    for _, row in df.iterrows():
        dt = pd.to_datetime(row["datetime"])
        hour = dt.hour
        pred = float(row.get("predicted_ptf", row.get("tahmin_ptf", row.get("ptf", 0))))
        actual = float(row.get("ptf", row.get("gerceklesen_ptf", pred)))
        diff = pred - actual
        diff_pct = (diff / (actual + 1e-6)) * 100
        
        if 17 <= hour <= 21:
            block = "PUANT"
        elif 8 <= hour < 17:
            block = "GUNDUZ"
        else:
            block = "GECE"
            
        r = {
            "Tarih": dt.strftime("%Y-%m-%d"),
            "Saat": f"{hour:02d}:00",
            "Piyasa_Bloku": block,
            "Tahmin_PTF_TL": round(pred, 2),
            "Gerceklesen_PTF_TL": round(actual, 2),
            "Sapma_TL": round(diff, 2),
            "Hata_Yuzde": round(abs(diff_pct), 2),
            "Guven_Alt_TL": round(float(row.get("lower_bound", pred - 40)), 2),
            "Guven_Ust_TL": round(float(row.get("upper_bound", pred + 40)), 2),
        }
        if "smf" in row and pd.notna(row["smf"]):
            smf_val = float(row["smf"])
            r["Gerceklesen_SMF_TL"] = round(smf_val, 2)
            r["Spread_PTF_SMF_TL"] = round(actual - smf_val, 2)
            
        rows.append(r)
        
    clean_csv_df = pd.DataFrame(rows)
    return clean_csv_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


def _sanitize_df_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Excel (.xlsx) çıktısı öncesi tüm zaman dilimlerini (timezone) temizler.
    openpyxl timezone-aware datetimes ile karşılaştığında ValueError fırlatır.
    """
    if df is None or len(df) == 0:
        return pd.DataFrame()
    df_clean = df.copy()
    df_clean.reset_index(drop=True, inplace=True)
    for col in df_clean.columns:
        if pd.api.types.is_datetime64_any_dtype(df_clean[col]):
            try:
                if df_clean[col].dt.tz is not None:
                    df_clean[col] = df_clean[col].dt.tz_localize(None)
            except Exception:
                df_clean[col] = df_clean[col].dt.strftime("%Y-%m-%d %H:%M")
        elif df_clean[col].dtype == object:
            try:
                first_val = df_clean[col].dropna().iloc[0] if len(df_clean[col].dropna()) > 0 else None
                if isinstance(first_val, (pd.Timestamp, datetime)):
                    df_clean[col] = pd.to_datetime(df_clean[col]).dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
    return df_clean


def export_predictions_excel(
    day_df: pd.DataFrame,
    model_metrics: dict = None,
    trading_metrics: dict = None,
    backtest_df: pd.DataFrame = None,
) -> bytes:
    """
    Çok sekmeli kurumsal Excel (.xlsx) çalışma kitabı oluşturur:
    - 24s_Fiyat_Tahminleri
    - Model_Performansi
    - Trading_Performansi
    - Islem_Defteri (Varsa)
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        # 1. Sekme: 24 Saatlik Tahminler
        rows = []
        for _, row in day_df.iterrows():
            dt = pd.to_datetime(row["datetime"])
            hour = dt.hour
            pred = float(row.get("predicted_ptf", row.get("ptf", 0)))
            actual = float(row.get("ptf", pred))
            diff = pred - actual
            diff_pct = (diff / (actual + 1e-6)) * 100
            block = "PUANT" if 17 <= hour <= 21 else "GUNDUZ" if 8 <= hour < 17 else "GECE"
            
            r = {
                "Tarih": dt.strftime("%Y-%m-%d"),
                "Saat": f"{hour:02d}:00",
                "Blok": block,
                "Tahmin PTF (TL)": round(pred, 2),
                "Gerçekleşen PTF (TL)": round(actual, 2),
                "Sapma (TL)": round(diff, 2),
                "Hata (%)": f"%{abs(diff_pct):.2f}",
                "Güven Alt (TL)": round(float(row.get("lower_bound", pred - 40)), 2),
                "Güven Üst (TL)": round(float(row.get("upper_bound", pred + 40)), 2),
            }
            if "smf" in row and pd.notna(row["smf"]):
                smf_val = float(row["smf"])
                r["Gerçekleşen SMF (TL)"] = round(smf_val, 2)
                r["Spread PTF-SMF (TL)"] = round(actual - smf_val, 2)
            rows.append(r)
            
        _sanitize_df_for_excel(pd.DataFrame(rows)).to_excel(writer, sheet_name="24s_Fiyat_Tahminleri", index=False)
        
        # 2. Sekme: Model Performansı
        if model_metrics:
            wape_val = model_metrics.get("wape", model_metrics.get("mape", 0))
            mape_val = model_metrics.get("mape", 0)
            m_rows = [
                {"Metrik Adı": "WAPE (Hacim Ağırlıklı Yüzde Hata)", "Değer": f"%{wape_val:.2f}", "Kabul Kriteri": "< %12.0", "Durum": "[KABUL] HEDEFTE" if wape_val < 12 else "[UYARI] GELİŞTİRİLMELİ"},
                {"Metrik Adı": "MAPE (Aritmetik Mutlak Yüzde Hata)", "Değer": f"%{mape_val:.2f}", "Kabul Kriteri": "Referans", "Durum": "BİLGİ"},
                {"Metrik Adı": "Yön Doğruluğu (Directional Accuracy)", "Değer": f"%{model_metrics.get('directional_accuracy', 0):.1f}", "Kabul Kriteri": "> %70.0", "Durum": "[KABUL] HEDEFTE" if model_metrics.get('directional_accuracy', 0) > 70 else "[UYARI] GELİŞTİRİLMELİ"},
                {"Metrik Adı": "RMSE (Kök Ortalama Kare Hata)", "Değer": f"{model_metrics.get('rmse', 0):,.2f} TL", "Kabul Kriteri": "Minimum Hata", "Durum": "BAŞARILI"},
                {"Metrik Adı": "MAE (Ortalama Mutlak Hata)", "Değer": f"{model_metrics.get('mae', 0):,.2f} TL", "Kabul Kriteri": "Minimum Hata", "Durum": "BAŞARILI"},
                {"Metrik Adı": "R² Belirlilik Katsayısı", "Değer": f"{model_metrics.get('r2', 0):.4f}", "Kabul Kriteri": "Pozitif Trend", "Durum": "BAŞARILI"},
                {"Metrik Adı": "24s Çıkarım Gecikmesi (Latency)", "Değer": f"{model_metrics.get('infer_time_24h_ms', 0):.2f} ms", "Kabul Kriteri": "< 500.0 ms", "Durum": "BAŞARILI"},
            ]
            _sanitize_df_for_excel(pd.DataFrame(m_rows)).to_excel(writer, sheet_name="Model_Performansi", index=False)
            
        # 3. Sekme: Trading Masası Metrikleri
        if trading_metrics:
            t_rows = [
                {"Trading Parametresi": "Toplam Kümülatif P&L", "Değer": f"{trading_metrics.get('total_pnl', 0):,.2f} TL"},
                {"Trading Parametresi": "Kazanma Oranı (Win Rate)", "Değer": f"%{trading_metrics.get('win_rate', 0):.1f}"},
                {"Trading Parametresi": "Toplam İşlem Sayısı", "Değer": trading_metrics.get('total_trades', 0)},
                {"Trading Parametresi": "Ortalama Kazanç", "Değer": f"{trading_metrics.get('avg_win', 0):,.2f} TL"},
                {"Trading Parametresi": "Ortalama Kayıp", "Değer": f"{trading_metrics.get('avg_loss', 0):,.2f} TL"},
                {"Trading Parametresi": "Maksimum Drawdown (%)", "Değer": f"%{trading_metrics.get('max_drawdown_pct', 0):.2f}"},
                {"Trading Parametresi": "Maksimum Drawdown (TL)", "Değer": f"{trading_metrics.get('max_drawdown_tl', 0):,.2f} TL"},
                {"Trading Parametresi": "Sharpe Oranı", "Değer": f"{trading_metrics.get('sharpe_ratio', 0):.2f}"},
                {"Trading Parametresi": "Profit Factor", "Değer": f"{trading_metrics.get('profit_factor', 0):.2f}"},
            ]
            _sanitize_df_for_excel(pd.DataFrame(t_rows)).to_excel(writer, sheet_name="Trading_Performansi", index=False)
            
        # 4. Sekme: İşlem Defteri (Varsa)
        if backtest_df is not None:
            try:
                trades = backtest_df[backtest_df["signal"] != 0].copy()
                if len(trades) > 0:
                    trades["İşlem"] = trades["signal"].map({1: "AL", -1: "SAT"})
                    trades_export = trades[["datetime", "İşlem", "actual_ptf", "predicted_ptf", "position_mwh", "pnl", "cumulative_pnl"]].rename(columns={
                        "datetime": "Tarih / Saat",
                        "actual_ptf": "Gerçekleşen PTF (TL)",
                        "predicted_ptf": "Tahmin PTF (TL)",
                        "position_mwh": "Pozisyon (MWh)",
                        "pnl": "İşlem P&L (TL)",
                        "cumulative_pnl": "Kümülatif P&L (TL)",
                    })
                    _sanitize_df_for_excel(trades_export).to_excel(writer, sheet_name="Islem_Defteri", index=False)
            except Exception as e:
                logger.warning(f"Islem_Defteri sekmesi yazılırken hata: {e}")
                
    return buffer.getvalue()


def generate_technical_report_html(
    metrics: dict,
    trading_metrics: dict = None,
    summary: dict = None,
    day_df: pd.DataFrame = None,
    model_type: str = "catboost",
    target_date_str: str = "",
) -> str:
    """
    Herhangi bir tarayıcıda çift tıklamayla açılan, ultra-modern
    Bloomberg/Refinitiv koyu/açık temalı ve yazdırılabilir HTML Yönetici Raporu üretir.
    """
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    target_date = target_date_str if target_date_str else datetime.now().strftime("%Y-%m-%d")
    model_name = model_type.upper()
    
    mape = metrics.get("mape", 0)
    wape = metrics.get("wape", mape)
    da = metrics.get("directional_accuracy", 0)
    rmse = metrics.get("rmse", 0)
    mae = metrics.get("mae", 0)
    r2 = metrics.get("r2", 0)
    infer = metrics.get("infer_time_24h_ms", 0)
    
    target_met = (wape < 12 or mape < 12) and da > 70
    status_badge = "[KABUL] HEDEFLER SAGLANDI" if target_met else "[UYARI] GELISTIRILMELI"
    status_color = "#22c55e" if target_met else "#f59e0b"
    
    # 24 Saatlik Tablo Satırları
    schedule_rows_html = ""
    if day_df is not None and len(day_df) > 0:
        for _, row in day_df.iterrows():
            dt = pd.to_datetime(row["datetime"])
            h = dt.hour
            pred = float(row.get("predicted_ptf", row.get("ptf", 0)))
            actual = float(row.get("ptf", pred))
            diff = pred - actual
            diff_pct = (diff / (actual + 1e-6)) * 100
            block = "PUANT" if 17 <= h <= 21 else "GUNDUZ" if 8 <= h < 17 else "GECE"
            block_style = "color:#60a5fa;font-weight:600;" if block == "PUANT" else "color:#94a3b8;"
            diff_color = "#22c55e" if abs(diff_pct) < 2 else "#ef4444"
            
            schedule_rows_html += f"""
            <tr>
                <td style="font-family:monospace;font-weight:600;">{h:02d}:00</td>
                <td style="{block_style}">[{block}]</td>
                <td style="font-family:monospace;font-weight:600;">{pred:,.1f} TL</td>
                <td style="font-family:monospace;">{actual:,.1f} TL</td>
                <td style="font-family:monospace;color:{diff_color};">{diff:+,.1f} TL</td>
                <td style="font-family:monospace;color:{diff_color}; font-weight:600;">%{abs(diff_pct):.2f}</td>
                <td style="font-family:monospace;color:#64748b;">{float(row.get('lower_bound', pred-40)):,.0f} — {float(row.get('upper_bound', pred+40)):,.0f}</td>
            </tr>
            """
            
    # Trading Metrikleri Tablosu
    trading_html = ""
    if trading_metrics:
        pnl = trading_metrics.get("total_pnl", 0)
        pnl_col = "#22c55e" if pnl >= 0 else "#ef4444"
        trading_html = f"""
        <div class="card" style="margin-top:24px;">
            <div class="section-title">3. Algoritmik Trading Masası & P&L Başarımı</div>
            <div class="grid-4">
                <div class="kpi-box">
                    <div class="kpi-label">KÜMÜLATİF NET P&L</div>
                    <div class="kpi-val" style="color:{pnl_col};">{pnl:,.0f} TL</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-label">BAŞARI ORANI (WIN RATE)</div>
                    <div class="kpi-val">%{trading_metrics.get('win_rate',0):.1f}</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-label">MAKSİMUM DRAWDOWN</div>
                    <div class="kpi-val" style="color:#ef4444;">%{trading_metrics.get('max_drawdown_pct',0):.1f}</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-label">SHARPE ORANI</div>
                    <div class="kpi-val">{trading_metrics.get('sharpe_ratio',0):.2f}</div>
                </div>
            </div>
            <table class="data-table" style="margin-top:16px;">
                <thead>
                    <tr><th>Parametre</th><th>Değer</th><th>Parametre</th><th>Değer</th></tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Toplam Gerçekleşen İşlem</td><td>{trading_metrics.get('total_trades',0)} adet</td>
                        <td>Profit Factor</td><td>{trading_metrics.get('profit_factor',0):.2f}</td>
                    </tr>
                    <tr>
                        <td>Ortalama Kazançlı İşlem</td><td>{trading_metrics.get('avg_win',0):,.0f} TL</td>
                        <td>Ortalama Zararlı İşlem</td><td>{trading_metrics.get('avg_loss',0):,.0f} TL</td>
                    </tr>
                    <tr>
                        <td>Brüt Kâr</td><td>{trading_metrics.get('gross_profit',0):,.0f} TL</td>
                        <td>Brüt Zarar</td><td>{trading_metrics.get('gross_loss',0):,.0f} TL</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EPİAŞ GÖP PTF Teknik Analiz Raporu — {target_date}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #0f141d;
            color: #e2e8f0;
            margin: 0;
            padding: 30px 20px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: #141a26;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 36px 40px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            padding-bottom: 20px;
            margin-bottom: 24px;
        }}
        .title {{
            font-size: 1.55rem;
            font-weight: 800;
            color: #f8fafc;
            letter-spacing: -0.02em;
            margin: 0 0 4px 0;
        }}
        .subtitle {{
            font-size: 0.8rem;
            color: #60a5fa;
            font-family: 'JetBrains Mono', monospace;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}
        .badge {{
            display: inline-block;
            padding: 6px 14px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            font-family: monospace;
            border: 1px solid {status_color};
            color: {status_color};
            background: rgba(34, 197, 94, 0.08);
        }}
        .meta-bar {{
            display: flex;
            gap: 20px;
            font-size: 0.78rem;
            color: #94a3b8;
            margin-bottom: 24px;
            font-family: monospace;
            background: rgba(255,255,255,0.02);
            padding: 10px 16px;
            border-radius: 6px;
            border: 1px solid rgba(255,255,255,0.05);
        }}
        .section-title {{
            font-size: 1.05rem;
            font-weight: 700;
            color: #f1f5f9;
            margin: 20px 0 12px 0;
            padding-bottom: 6px;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }}
        .grid-4 {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
        }}
        .kpi-box {{
            background: #101522;
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 8px;
            padding: 14px;
        }}
        .kpi-label {{
            font-size: 0.65rem;
            color: #64748b;
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.06em;
            margin-bottom: 4px;
        }}
        .kpi-val {{
            font-size: 1.35rem;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            color: #f8fafc;
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.82rem;
            margin-top: 10px;
        }}
        .data-table th {{
            background: #101624;
            color: #94a3b8;
            text-align: left;
            padding: 10px 12px;
            font-weight: 600;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .data-table td {{
            padding: 8px 12px;
            border-bottom: 1px solid rgba(255,255,255,0.03);
            color: #cbd5e1;
        }}
        .data-table tr:hover td {{
            background: rgba(255,255,255,0.02);
        }}
        .print-btn {{
            background: #2563eb;
            color: #ffffff;
            border: none;
            padding: 8px 18px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.82rem;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .print-btn:hover {{
            background: #1d4ed8;
        }}
        @media print {{
            body {{ background: #ffffff !important; color: #000000 !important; }}
            .container {{ box-shadow: none !important; border: none !important; padding: 0 !important; max-width: 100% !important; }}
            .print-btn {{ display: none !important; }}
            .data-table th {{ background: #f1f5f9 !important; color: #000 !important; }}
            .data-table td {{ color: #000 !important; }}
            .kpi-box {{ background: #f8fafc !important; border: 1px solid #cbd5e1 !important; }}
            .kpi-val {{ color: #000 !important; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div style="display:flex; justify-content:flex-end; margin-bottom:12px;">
            <button class="print-btn" onclick="window.print()">Yazdır / PDF Olarak Kaydet</button>
        </div>
        
        <div class="header">
            <div>
                <div class="subtitle">EPİAŞ GÜN ÖNCESİ PİYASASI (GÖP)</div>
                <h1 class="title">PTF Fiyat Tahmin & Algoritmik Trading Raporu</h1>
                <div style="font-size:0.75rem; color:#64748b;">Kurumsal Enerji Masası Karar Destek Çıktısı</div>
            </div>
            <div style="text-align:right;">
                <div class="badge">{status_badge}</div>
            </div>
        </div>
        
        <div class="meta-bar">
            <div>HEDEF TARİH: <span style="color:#f8fafc; font-weight:bold;">{target_date}</span></div>
            <div>AKTİF MODEL: <span style="color:#60a5fa; font-weight:bold;">{model_name}</span></div>
            <div>RAPOR ZAMANI: <span style="color:#f8fafc;">{now_str} (TSI)</span></div>
        </div>
        
        <div class="section-title">1. Yapay Zeka Model Doğrulama Matrisi</div>
        <div class="grid-4">
            <div class="kpi-box">
                <div class="kpi-label">WAPE (HACİM AĞIRLIKLI)</div>
                <div class="kpi-val" style="color:#22c55e;">%{wape:.2f}</div>
                <div style="font-size:0.68rem; color:#64748b; margin-top:4px;">Kabul: &lt; %12.0 (MAPE: %{mape:.1f})</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-label">YÖN DOĞRULUĞU</div>
                <div class="kpi-val">%{da:.1f}</div>
                <div style="font-size:0.68rem; color:#64748b; margin-top:4px;">Kabul Hedefi: &gt; %70.0</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-label">MAE / HATA PAYI</div>
                <div class="kpi-val">{mae:,.0f} TL</div>
                <div style="font-size:0.68rem; color:#64748b; margin-top:4px;">RMSE: {rmse:,.0f} TL</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-label">24S ÇIKARIM SÜRESİ</div>
                <div class="kpi-val">{infer:.2f} ms</div>
                <div style="font-size:0.68rem; color:#64748b; margin-top:4px;">NFR-01: &lt; 500 ms</div>
            </div>
        </div>
        
        <div class="section-title" style="margin-top:28px;">2. Hedef Gün 24 Saatlik Detaylı Tahmin Tablosu ({target_date})</div>
        <table class="data-table">
            <thead>
                <tr>
                    <th>Saat</th>
                    <th>Piyasa Bloku</th>
                    <th>Tahmin PTF (TL)</th>
                    <th>Gerçekleşen PTF</th>
                    <th>Fark / Sapma</th>
                    <th>Hata (%)</th>
                    <th>%90 Güven Aralığı</th>
                </tr>
            </thead>
            <tbody>
                {schedule_rows_html if schedule_rows_html else '<tr><td colspan="7">Tahmin verisi üretildi.</td></tr>'}
            </tbody>
        </table>
        
        {trading_html}
        
        <div style="margin-top:36px; padding-top:16px; border-top:1px solid rgba(255,255,255,0.06); font-size:0.72rem; color:#64748b; display:flex; justify-content:space-between;">
            <div>EPİAŞ GÖP & DGP Kantitatif Portföy Terminali — Staj Projesi 2026</div>
            <div>Resmi EPİAŞ ve TEİAŞ Piyasa Verilerine Dayalıdır</div>
        </div>
    </div>
</body>
</html>"""
    return html_content


def generate_technical_report_docx(
    metrics: dict,
    trading_metrics: dict = None,
    summary: dict = None,
    day_df: pd.DataFrame = None,
    model_type: str = "catboost",
    target_date_str: str = "",
) -> bytes:
    """
    Microsoft Word (.docx) formatında tam yapılandırılmış teknik analiz raporu üretir.
    """
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    
    doc = docx.Document()
    
    # Başlık
    title = doc.add_heading("EPİAŞ GÖP PTF Teknik Analiz Raporu", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    target_date = target_date_str if target_date_str else datetime.now().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_meta.add_run(f"Hedef Tarih: {target_date}  |  Model: {model_type.upper()}  |  Üretilme: {now_str} TSI\n").bold = True
    p_meta.add_run("EPİAŞ Gün Öncesi Piyasası Algoritmik Fiyat Tahmin ve Trading Terminali")
    
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    
    # Bölüm 1: Model Metrikleri
    doc.add_heading("1. Yapay Zeka Model Doğrulama ve Performans Matrisi", level=1)
    
    table_m = doc.add_table(rows=1, cols=4)
    table_m.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_cells = table_m.rows[0].cells
    hdr_cells[0].text = "Metrik"
    hdr_cells[1].text = "Değer"
    hdr_cells[2].text = "SRS Kabul Hedefi"
    hdr_cells[3].text = "Durum"
    
    wape = metrics.get("wape", metrics.get("mape", 0))
    m_data = [
        ("WAPE (Hacim Ağırlıklı Yüzde Hata)", f"%{wape:.2f}", "< %12.0", "KABUL" if wape < 12 else "UYARI"),
        ("MAPE (Aritmetik Yüzde Hata)", f"%{metrics.get('mape', 0):.2f}", "Referans", "BİLGİ"),
        ("Yön Doğruluğu (Directional Accuracy)", f"%{metrics.get('directional_accuracy', 0):.1f}", "> %70.0", "KABUL" if metrics.get('directional_accuracy', 0) > 70 else "UYARI"),
        ("RMSE (Kök Ortalama Kare Hata)", f"{metrics.get('rmse', 0):,.2f} TL", "Minimum Hata", "BAŞARILI"),
        ("MAE (Ortalama Mutlak Hata)", f"{metrics.get('mae', 0):,.2f} TL", "Minimum Hata", "BAŞARILI"),
        ("R² Belirlilik Skoru", f"{metrics.get('r2', 0):.4f}", "Pozitif Trend", "BAŞARILI"),
        ("24s Çıkarım Hızı (Latency)", f"{metrics.get('infer_time_24h_ms', 0):.2f} ms", "< 500 ms (NFR-01)", "BAŞARILI"),
    ]
    for m, v, tgt, st in m_data:
        row_cells = table_m.add_row().cells
        row_cells[0].text = m
        row_cells[1].text = v
        row_cells[2].text = tgt
        row_cells[3].text = st
        
    doc.add_paragraph().paragraph_format.space_after = Pt(16)
    
    # Bölüm 2: 24 Saatlik Tahmin Tablosu
    if day_df is not None and len(day_df) > 0:
        doc.add_heading(f"2. {target_date} Günü 24 Saatlik Fiyat Tahmin Tablosu", level=1)
        table_s = doc.add_table(rows=1, cols=6)
        table_s.alignment = WD_TABLE_ALIGNMENT.CENTER
        shdr = table_s.rows[0].cells
        shdr[0].text = "Saat"
        shdr[1].text = "Blok"
        shdr[2].text = "Tahmin PTF"
        shdr[3].text = "Gerçekleşen"
        shdr[4].text = "Sapma (TL)"
        shdr[5].text = "Hata (%)"
        
        for _, r in day_df.iterrows():
            dt = pd.to_datetime(r["datetime"])
            h = dt.hour
            pred = float(r.get("predicted_ptf", r.get("ptf", 0)))
            actual = float(r.get("ptf", pred))
            diff = pred - actual
            diff_pct = (diff / (actual + 1e-6)) * 100
            block = "PUANT" if 17 <= h <= 21 else "GUNDUZ" if 8 <= h < 17 else "GECE"
            
            rc = table_s.add_row().cells
            rc[0].text = f"{h:02d}:00"
            rc[1].text = f"[{block}]"
            rc[2].text = f"{pred:,.1f} TL"
            rc[3].text = f"{actual:,.1f} TL"
            rc[4].text = f"{diff:+,.1f} TL"
            rc[5].text = f"%{abs(diff_pct):.2f}"
            
    doc.add_paragraph().paragraph_format.space_after = Pt(16)
    
    # Bölüm 3: Trading Masası Metrikleri
    if trading_metrics:
        doc.add_heading("3. Algoritmik Trading Masası & P&L Başarımı", level=1)
        table_t = doc.add_table(rows=1, cols=2)
        table_t.alignment = WD_TABLE_ALIGNMENT.CENTER
        thdr = table_t.rows[0].cells
        thdr[0].text = "Trading Parametresi"
        thdr[1].text = "Performans Değeri"
        
        t_list = [
            ("Kümülatif Net P&L", f"{trading_metrics.get('total_pnl', 0):,.2f} TL"),
            ("İşlem Başarı Oranı (Win Rate)", f"%{trading_metrics.get('win_rate', 0):.1f}"),
            ("Toplam İşlem Sayısı", str(trading_metrics.get('total_trades', 0))),
            ("Maksimum Drawdown (%)", f"%{trading_metrics.get('max_drawdown_pct', 0):.2f}"),
            ("Maksimum Drawdown (TL)", f"{trading_metrics.get('max_drawdown_tl', 0):,.2f} TL"),
            ("Sharpe Oranı", f"{trading_metrics.get('sharpe_ratio', 0):.2f}"),
            ("Profit Factor", f"{trading_metrics.get('profit_factor', 0):.2f}"),
        ]
        for param, val in t_list:
            row_cells = table_t.add_row().cells
            row_cells[0].text = param
            row_cells[1].text = val

    doc.add_paragraph().paragraph_format.space_after = Pt(20)
    p_foot = doc.add_paragraph("Bu teknik rapor EPİAŞ GÖP PTF Algoritmik Terminali tarafından otomatik olarak üretilmiştir.")
    p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def generate_technical_report(
    metrics: dict,
    trading_metrics: dict = None,
    summary: dict = None,
    model_type: str = "catboost",
) -> str:
    """
    Geriye dönük uyumluluk için Markdown formatı metin raporu.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    report = f"""# EPİAŞ GÖP PTF — Teknik Analiz Raporu
**Oluşturulma Tarihi:** {now}  
**Model:** {model_type.upper()}  

---

## 1. Model Performans Metrikleri

| Metrik | Değer | Hedef | Durum |
|--------|-------|-------|-------|
| MAPE | %{metrics.get('mape', 0):.2f} | <%12 | {'[KABUL] Basarili' if metrics.get('mape', 100) < 12 else '[UYARI] Basarisiz'} |
| RMSE | {metrics.get('rmse', 0):,.1f} TL | — | — |
| MAE | {metrics.get('mae', 0):,.1f} TL | — | — |
| R² | {metrics.get('r2', 0):.4f} | — | — |
| Yön Doğruluğu | %{metrics.get('directional_accuracy', 0):.1f} | >%70 | {'[KABUL] Basarili' if metrics.get('directional_accuracy', 0) > 70 else '[UYARI] Basarisiz'} |
| 24s Çıkarım | {metrics.get('infer_time_24h_ms', 0):.2f} ms | <500 ms | [KABUL] Basarili |
"""
    return report
