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
        hovertemplate="<b>Gerçek</b><br>%{x|%H:%M}<br>%{y:,.0f} TL/MWh<extra></extra>",
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
            hovertemplate="<b>Tahmin</b><br>%{x|%H:%M}<br>%{y:,.0f} TL/MWh<extra></extra>",
        ))
    
    fig.update_layout(
        **DARK_LAYOUT,
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
