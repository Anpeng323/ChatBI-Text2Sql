"""图表服务：把查询结果 DataFrame 转为 ECharts option JSON（前端渲染，替代 matplotlib PNG）。

策略：
- 列 >= 2：首列作类目（轴），其余数值列作图。
- 类目名像时间/月份 → 折线；否则多数值列 → 分组柱状，单数值列 → 柱状。
- 单数值列且无类目 → 行号作类目柱状。
- 数值列仅 1 个且类目基数小（<= 12）→ 饼图更直观。
"""
from __future__ import annotations

import pandas as pd

from ..core.config import settings

_TIME_HINTS = ("time", "date", "月", "年", "week", "day")


def _pick(df: pd.DataFrame):
    cols = list(df.columns)
    if len(cols) >= 2:
        cat_col = cols[0]
        cats = [str(v) for v in df[cat_col].tolist()]
        value_cols = [c for c in cols[1:] if pd.api.types.is_numeric_dtype(df[c])]
        if not value_cols:
            return None
        return cats, value_cols, cat_col
    value_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    if not value_cols:
        return None
    return [str(i + 1) for i in range(len(df))], value_cols, None


def build_echarts_option(df: pd.DataFrame) -> dict | None:
    if df is None or df.empty:
        return None
    plot_df = df.head(settings.default_chart_limit).copy()
    picked = _pick(plot_df)
    if not picked:
        return None
    cats, value_cols, cat_col = picked

    looks_time = bool(cat_col) and any(k in str(cat_col).lower() for k in _TIME_HINTS)

    palette = ["#14B8A6", "#2563EB", "#A78BFA", "#F59E0B", "#EF4444", "#3B82F6"]
    text_color = "#E2E8F0"
    sub_color = "#94A3B8"
    grid_color = "#1E293B"

    series = []
    chart_type = "line" if looks_time else "bar"
    # 单数值列 + 类目基数小 → 饼图
    if len(value_cols) == 1 and cat_col and len(cats) <= 12 and not looks_time:
        col = value_cols[0]
        series = [
            {
                "type": "pie",
                "radius": ["38%", "70%"],
                "center": ["50%", "52%"],
                "itemStyle": {"borderColor": "#0B1220", "borderWidth": 2},
                "label": {"color": text_color},
                "data": [
                    {"name": c, "value": float(plot_df[col].tolist()[i])}
                    for i, c in enumerate(cats)
                ],
            }
        ]
    else:
        for i, c in enumerate(value_cols):
            if chart_type == "line":
                series.append(
                    {
                        "name": c,
                        "type": "line",
                        "smooth": True,
                        "symbol": "circle",
                        "symbolSize": 7,
                        "lineStyle": {"width": 2.2},
                        "itemStyle": {"color": palette[i % len(palette)]},
                        "data": [round(float(v), 4) for v in plot_df[c].tolist()],
                    }
                )
            else:
                series.append(
                    {
                        "name": c,
                        "type": "bar",
                        "itemStyle": {"color": palette[i % len(palette)], "radius": [4, 4, 0, 0]},
                        "data": [round(float(v), 4) for v in plot_df[c].tolist()],
                        "barMaxWidth": 36,
                    }
                )

    option: dict = {
        "backgroundColor": "transparent",
        "color": palette,
        "tooltip": {
            "trigger": "axis" if chart_type != "pie" else "item",
            "backgroundColor": "#16203A",
            "borderColor": "#24314F",
            "textStyle": {"color": text_color},
        },
        "legend": (
            {"textStyle": {"color": text_color}, "top": 4}
            if len(value_cols) > 1
            else {"show": False}
        ),
        "grid": {"left": 48, "right": 24, "top": 40, "bottom": 48, "containLabel": True},
        "xAxis": (
            {
                "type": "category",
                "data": cats,
                "axisLabel": {
                    "color": sub_color,
                    "rotate": 30 if len(cats) > 8 else 0,
                    "hideOverlap": True,
                },
                "axisLine": {"lineStyle": {"color": "#334155"}},
            }
            if chart_type != "pie"
            else {"show": False}
        ),
        "yAxis": (
            {
                "type": "value",
                "axisLabel": {"color": sub_color},
                "splitLine": {"lineStyle": {"color": grid_color}},
            }
            if chart_type != "pie"
            else {"show": False}
        ),
        "series": series,
        "title": {
            "text": "查询结果可视化",
            "left": "center",
            "textStyle": {"color": text_color, "fontSize": 13, "fontWeight": 600},
        },
    }
    return option
