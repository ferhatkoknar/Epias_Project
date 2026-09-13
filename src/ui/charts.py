"""
Plotly Grafik Modülü (FR-05)
Etkileşimli, koyu tema, profesyonel finansal grafikler.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ─── Ortak Layout ───
DARK_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(12, 15, 20, 0.6)",
    font=dict(family="Inter, sans-serif", color="#9ca3af", size=11),
    title_font=dict(family="Inter, sans-serif", color="#c8cdd6", size=13, ),
    legend=dict(
        bgcolor="rgba(20, 24, 32, 0.8)",
        bordercolor="rgba(255,255,255,0.04)",
        borderwidth=1,
        font=dict(size=10, color="#9ca3af"),
    ),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.03)",
        zerolinecolor="rgba(255,255,255,0.05)",
        tickfont=dict(family="JetBrains Mono, monospace", size=10),
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.03)",
        zerolinecolor="rgba(255,255,255,0.05)",
        tickfont=dict(family="JetBrains Mono, monospace", size=10),
    ),
    margin=dict(l=56, r=24, t=44, b=44),
    hoverlabel=dict(
        bgcolor="rgba(20, 24, 32, 0.95)",
        bordercolor="rgba(255,255,255,0.08)",
        font=dict(family="JetBrains Mono, monospace", size=11, color="#e5e7eb"),
    ),
)


def create_ptf_forecast_chart(
    actual_df: pd.DataFrame,
    forecast_df: pd.DataFrame = None,
    title: str = "24 Saatlik PTF Fiyat Projeksiyonu",
    height: int = 460,
    show_rangeslider: bool = True,
) -> go.Figure:
    """Gerçekleşen PTF vs Model Tahmini."""
    fig = go.Figure()
    
    # Gerçekleşen PTF
    fig.add_trace(go.Scatter(
        x=actual_df["datetime"],
        y=actual_df["ptf"],
        mode="lines",
        name="Gerçekleşen PTF",
        line=dict(color="#3b82f6", width=1.8),
        fill="tozeroy",
        fillcolor="rgba(59, 130, 246, 0.04)",
        hovertemplate="<b>Gerçek</b>: %{y:,.0f} TL/MWh<br>%{x|%d %b %H:%M}<extra></extra>",
    ))
    
    if forecast_df is not None and len(forecast_df) > 0:
        # Güven aralığı
        if "upper_bound" in forecast_df.columns and "lower_bound" in forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=forecast_df["datetime"],
                y=forecast_df["upper_bound"],
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
            ))
            fig.add_trace(go.Scatter(
                x=forecast_df["datetime"],
                y=forecast_df["lower_bound"],
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(245, 158, 11, 0.06)",
                name="Güven Aralığı",
                hoverinfo="skip",
            ))
        
        # Tahmin
        fig.add_trace(go.Scatter(
            x=forecast_df["datetime"],
            y=forecast_df["predicted_ptf"],
            mode="lines+markers",
            name="Model Tahmini",
            line=dict(color="#f59e0b", width=1.8, dash="dot"),
            marker=dict(size=4, color="#f59e0b"),
            hovertemplate="<b>Tahmin</b>: %{y:,.0f} TL/MWh<br>%{x|%d %b %H:%M}<extra></extra>",
        ))
    
    xaxis_config = dict(
        gridcolor="rgba(255,255,255,0.03)",
        zerolinecolor="rgba(255,255,255,0.05)",
        tickfont=dict(family="JetBrains Mono, monospace", size=10),
    )
    if show_rangeslider:
        xaxis_config["rangeslider"] = dict(
            visible=True,
            bgcolor="rgba(15, 23, 42, 0.6)",
            thickness=0.08,
            bordercolor="rgba(255, 255, 255, 0.08)",
        )
        xaxis_config["rangeselector"] = dict(
            buttons=[
                dict(count=6, label="6 Saat", step="hour", stepmode="backward"),
                dict(count=12, label="12 Saat", step="hour", stepmode="backward"),
                dict(count=24, label="24 Saat (1G)", step="hour", stepmode="backward"),
                dict(count=3, label="3 Gun", step="day", stepmode="backward"),
                dict(count=7, label="7 Gun", step="day", stepmode="backward"),
                dict(step="all", label="Tumu"),
            ],
            bgcolor="rgba(16, 22, 34, 0.9)",
            activecolor="rgba(59, 130, 246, 0.4)",
            font=dict(color="#9ca3af", size=10, family="Inter, sans-serif"),
            bordercolor="rgba(255, 255, 255, 0.1)",
            borderwidth=1,
            y=1.12,
            x=0.0,
        )
    
    layout_opts = {**DARK_LAYOUT}
    layout_opts["xaxis"] = xaxis_config
    
    fig.update_layout(
        **layout_opts,
        title=dict(text=title, x=0.01, y=0.97),
        xaxis_title="",
        yaxis_title="TL/MWh",
        height=height,
        hovermode="x unified",
    )
    
    return fig


def create_error_distribution_chart(
    actual: np.ndarray,
    predicted: np.ndarray,
    hours: np.ndarray = None,
    height: int = 380,
) -> go.Figure:
    """Saatlik hata dağılımı."""
    errors = predicted - actual
    
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.55, 0.45],
        subplot_titles=("Saatlik Tahmin Sapması", "Hata Dağılımı"),
    )
    
    # Saatlik sapma
    if hours is not None:
        hourly_errors = pd.DataFrame({"hour": hours, "error": errors})
        hourly_mean = hourly_errors.groupby("hour")["error"].mean()
        colors = ["#22c55e" if e >= 0 else "#ef4444" for e in hourly_mean.values]
        
        fig.add_trace(go.Bar(
            x=hourly_mean.index,
            y=hourly_mean.values,
            marker_color=colors,
            marker_line_width=0,
            name="Sapma",
            hovertemplate="Saat %{x}:00<br>%{y:,.0f} TL<extra></extra>",
        ), row=1, col=1)
    else:
        colors = ["#22c55e" if e >= 0 else "#ef4444" for e in errors[:24]]
        fig.add_trace(go.Bar(
            x=list(range(len(errors[:24]))),
            y=errors[:24],
            marker_color=colors,
            marker_line_width=0,
            name="Sapma",
        ), row=1, col=1)
    
    # Histogram
    fig.add_trace(go.Histogram(
        x=errors,
        nbinsx=40,
        marker_color="rgba(59, 130, 246, 0.35)",
        marker_line=dict(color="rgba(59, 130, 246, 0.6)", width=0.5),
        name="Dağılım",
        hovertemplate="%{x:,.0f} TL<br>Frekans: %{y}<extra></extra>",
    ), row=1, col=2)
    
    fig.update_layout(
        **DARK_LAYOUT,
        height=height,
        showlegend=False,
    )
    
    return fig


def create_pnl_chart(
    backtest_df: pd.DataFrame,
    height: int = 440,
) -> go.Figure:
    """Kümülatif P&L ve drawdown."""
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.65, 0.35],
        shared_xaxes=True,
        subplot_titles=("Kümülatif P&L (TL)", "Drawdown"),
        vertical_spacing=0.1,
    )
    
    cum_pnl = backtest_df["cumulative_pnl"]
    is_positive = cum_pnl.iloc[-1] >= 0
    line_color = "#22c55e" if is_positive else "#ef4444"
    fill_color = "rgba(34, 197, 94, 0.06)" if is_positive else "rgba(239, 68, 68, 0.06)"
    
    fig.add_trace(go.Scatter(
        x=backtest_df["datetime"],
        y=cum_pnl,
        mode="lines",
        name="P&L",
        line=dict(color=line_color, width=1.5),
        fill="tozeroy",
        fillcolor=fill_color,
        hovertemplate="%{y:,.0f} TL<extra></extra>",
    ), row=1, col=1)
    
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.08)", row=1, col=1)
    
    # Drawdown
    peak = cum_pnl.cummax()
    drawdown = ((cum_pnl - peak) / (peak.abs() + 1e-8)) * 100
    drawdown = drawdown.clip(upper=0)
    
    fig.add_trace(go.Scatter(
        x=backtest_df["datetime"],
        y=drawdown,
        mode="lines",
        name="Drawdown",
        line=dict(color="#ef4444", width=1),
        fill="tozeroy",
        fillcolor="rgba(239, 68, 68, 0.06)",
        hovertemplate="%{y:.1f}%<extra></extra>",
    ), row=2, col=1)
    
    fig.update_layout(
        **DARK_LAYOUT,
        height=height,
        hovermode="x unified",
    )
    
    fig.update_yaxes(title_text="TL", row=1, col=1)
    fig.update_yaxes(title_text="%", row=2, col=1)
    
    return fig


def create_spread_risk_chart(
    risk_df: pd.DataFrame,
    height: int = 380,
) -> go.Figure:
    """Spread ve risk bölgeleri."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=list(range(len(risk_df))),
        y=risk_df["spread"],
        mode="lines",
        name="PTF-SMF Spread",
        line=dict(color="#3b82f6", width=1.5),
        hovertemplate="%{y:,.0f} TL<extra></extra>",
    ))
    
    # Risk bölgeleri — çok hafif
    fig.add_hrect(y0=-50, y1=50, fillcolor="rgba(34,197,94,0.02)", line_width=0)
    fig.add_hrect(y0=50, y1=150, fillcolor="rgba(234,179,8,0.02)", line_width=0)
    fig.add_hrect(y0=-150, y1=-50, fillcolor="rgba(234,179,8,0.02)", line_width=0)
    fig.add_hrect(y0=150, y1=400, fillcolor="rgba(249,115,22,0.02)", line_width=0)
    fig.add_hrect(y0=-400, y1=-150, fillcolor="rgba(249,115,22,0.02)", line_width=0)
    
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.08)")
    
    fig.update_layout(
        **DARK_LAYOUT,
        title=dict(text="PTF-SMF Spread", x=0.01, y=0.97),
        xaxis_title="",
        yaxis_title="TL/MWh",
        height=height,
    )
    
    return fig


def create_feature_importance_chart(
    fi_df: pd.DataFrame,
    top_n: int = 15,
    height: int = 380,
) -> go.Figure:
    """Öznitelik önem sıralaması."""
    top = fi_df.head(top_n).sort_values("importance_pct")
    
    fig = go.Figure(go.Bar(
        x=top["importance_pct"],
        y=top["feature"],
        orientation="h",
        marker=dict(
            color=top["importance_pct"],
            colorscale=[[0, "#1e2433"], [0.5, "#3b82f6"], [1, "#60a5fa"]],
            line_width=0,
        ),
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
    ))
    
    fig.update_layout(
        **DARK_LAYOUT,
        title=dict(text=f"Öznitelik Önem Sıralaması (İlk {top_n})", x=0.01, y=0.97),
        xaxis_title="%",
        height=height,
    )
    
    return fig


def create_hourly_heatmap(df: pd.DataFrame, height: int = 380) -> go.Figure:
    """
    24 Saat x 7 Gün PTF Fiyat Isı Haritası (Heatmap).
    Piyasa saatlik ve haftalık fiyat döngülerini görselleştirir.
    """
    data = df.copy()
    if "hour" not in data.columns:
        data["hour"] = data["datetime"].dt.hour
    if "dayofweek" not in data.columns:
        data["dayofweek"] = data["datetime"].dt.dayofweek
        
    day_names = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    pivot = data.pivot_table(index="dayofweek", columns="hour", values="ptf", aggfunc="mean")
    pivot = pivot.reindex(index=range(7), columns=range(24))
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[f"{h:02d}:00" for h in range(24)],
        y=day_names,
        colorscale=[
            [0.0, "#0b1329"],
            [0.25, "#1e3a8a"],
            [0.55, "#2563eb"],
            [0.8, "#f59e0b"],
            [1.0, "#ef4444"],
        ],
        colorbar=dict(
            title=dict(text="TL/MWh", side="right"),
            tickfont=dict(family="JetBrains Mono, monospace", size=10, color="#9ca3af"),
            thickness=14,
        ),
        hovertemplate="<b>%{y}</b> - %{x}<br>Ort. PTF: %{z:,.0f} TL/MWh<extra></extra>",
    ))
    
    fig.update_layout(
        **DARK_LAYOUT,
        title=dict(text="24 Saatlik & Haftalık PTF Fiyat Yoğunluğu Isı Haritası", x=0.01, y=0.97),
        xaxis_title="Günün Saati",
        yaxis_title="",
        height=height,
    )
    return fig


def create_base_peak_chart(df: pd.DataFrame, height: int = 360) -> go.Figure:
    """
    Taban Yük (00-24), Puant Yük (08-20) ve Süper Puant (17-21) Fiyat Kıyaslaması.
    """
    data = df.copy()
    data["date"] = data["datetime"].dt.date
    data["hour"] = data["datetime"].dt.hour
    
    base = data.groupby("date")["ptf"].mean()
    peak = data[(data["hour"] >= 8) & (data["hour"] <= 20)].groupby("date")["ptf"].mean()
    super_peak = data[(data["hour"] >= 17) & (data["hour"] <= 21)].groupby("date")["ptf"].mean()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(base.index), y=base.values,
        mode="lines", name="Taban Yük (00:00-24:00)",
        line=dict(color="#64748b", width=1.5, dash="dot"),
        hovertemplate="Taban: %{y:,.0f} TL<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=list(peak.index), y=peak.values,
        mode="lines+markers", name="Puant Yük (08:00-20:00)",
        line=dict(color="#3b82f6", width=2),
        marker=dict(size=4),
        hovertemplate="Puant: %{y:,.0f} TL<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=list(super_peak.index), y=super_peak.values,
        mode="lines", name="Süper Puant (17:00-21:00)",
        line=dict(color="#f59e0b", width=2),
        hovertemplate="Süper Puant: %{y:,.0f} TL<extra></extra>",
    ))
    
    fig.update_layout(
        **DARK_LAYOUT,
        title=dict(text="Kontrat Bazlı Günlük Fiyat Dinamiği (Taban vs Puant vs Süper Puant)", x=0.01, y=0.97),
        yaxis_title="TL/MWh",
        height=height,
        hovermode="x unified",
    )
    return fig


def create_multi_model_comparison_chart(
    dates: pd.Series,
    actual: np.ndarray,
    models_dict: dict,
    height: int = 440,
) -> go.Figure:
    """
    Çoklu model tahminlerini gerçekleşen PTF ile karşılaştıran grafik.
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates, y=actual,
        mode="lines",
        name="Gerçekleşen PTF",
        line=dict(color="#94a3b8", width=2.2),
        hovertemplate="<b>Gerçekleşen</b>: %{y:,.0f} TL<extra></extra>",
    ))
    
    palette = {
        "CatBoost": ("#3b82f6", "solid"),
        "LightGBM": ("#10b981", "dash"),
        "Ensemble": ("#f59e0b", "longdashdot"),
    }
    
    for name, preds in models_dict.items():
        color, dash = palette.get(name, ("#8b5cf6", "dot"))
        fig.add_trace(go.Scatter(
            x=dates, y=preds,
            mode="lines",
            name=f"{name} Modeli",
            line=dict(color=color, width=1.8, dash=dash),
            hovertemplate=f"<b>{name}</b>: %{{y:,.0f}} TL<extra></extra>",
        ))
        
    fig.update_layout(
        **DARK_LAYOUT,
        title=dict(text="Model Karşılaştırmalı 24 Saatlik PTF Projeksiyonu", x=0.01, y=0.97),
        yaxis_title="TL/MWh",
        height=height,
        hovermode="x unified",
    )
    return fig


def create_stress_test_chart(
    shocked_df: pd.DataFrame,
    shock_name: str = "Gaz Arz Kesintisi",
    height: int = 400,
) -> go.Figure:
    """Stres testi senaryosu altında orijinal vs şoklanmış kümülatif P&L."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=shocked_df["datetime"],
        y=shocked_df["cumulative_pnl"],
        mode="lines",
        name="Normal Senaryo P&L",
        line=dict(color="#3b82f6", width=2),
        fill="tozeroy",
        fillcolor="rgba(59, 130, 246, 0.05)",
        hovertemplate="Normal P&L: %{y:,.0f} TL<extra></extra>",
    ))
    
    is_shock_pos = shocked_df["shocked_cumulative_pnl"].iloc[-1] >= 0
    s_col = "#22c55e" if is_shock_pos else "#ef4444"
    fig.add_trace(go.Scatter(
        x=shocked_df["datetime"],
        y=shocked_df["shocked_cumulative_pnl"],
        mode="lines",
        name=f"Stres Altında ({shock_name})",
        line=dict(color=s_col, width=2, dash="dash"),
        fill="tozeroy",
        fillcolor="rgba(239, 68, 68, 0.05)" if not is_shock_pos else "rgba(34, 197, 94, 0.05)",
        hovertemplate="Stres P&L: %{y:,.0f} TL<extra></extra>",
    ))
    
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.1)")
    fig.update_layout(
        **DARK_LAYOUT,
        title=dict(text=f"Stres Testi P&L Karşılaştırması: {shock_name}", x=0.01, y=0.97),
        yaxis_title="Kümülatif P&L (TL)",
        height=height,
        hovermode="x unified",
    )
    return fig
