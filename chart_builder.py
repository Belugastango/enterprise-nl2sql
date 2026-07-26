import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any, Optional

COLOR_PALETTE = [
    '#6366F1', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', 
    '#EC4899', '#06B6D4', '#3B82F6', '#84CC16', '#F97316'
]

def auto_detect_chart_config(df: pd.DataFrame) -> Dict[str, Any]:
    """Infers the best chart type and axis column mapping from a DataFrame's columns and data types."""
    if df is None or df.empty:
        return {"chart_type": "table", "x": None, "y": None}

    cols = list(df.columns)
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime', 'datetime64']).columns.tolist()

    # Detect date-like strings
    for col in cat_cols:
        if any(keyword in col.lower() for keyword in ['date', 'time', 'month', 'year', 'quarter', 'day']):
            datetime_cols.append(col)

    # 1. Single row / Scalar result -> KPI Metric
    if len(df) == 1 and len(num_cols) >= 1:
        return {
            "chart_type": "metric",
            "metric_col": num_cols[0],
            "label_col": cat_cols[0] if cat_cols else None
        }

    # 2. Time series / Date column present -> Line chart
    if datetime_cols and num_cols:
        return {
            "chart_type": "line",
            "x": datetime_cols[0],
            "y": num_cols[0],
            "color": cat_cols[0] if len(cat_cols) > 1 and cat_cols[0] != datetime_cols[0] else None
        }

    # 3. Category + 1 Metric -> Bar or Pie
    if len(cat_cols) >= 1 and len(num_cols) >= 1:
        # If 6 or fewer categories -> Pie / Donut chart
        if df[cat_cols[0]].nunique() <= 6 and len(df) <= 6:
            return {
                "chart_type": "donut",
                "names": cat_cols[0],
                "values": num_cols[0]
            }
        # Otherwise Bar chart
        return {
            "chart_type": "bar",
            "x": cat_cols[0],
            "y": num_cols[0],
            "color": cat_cols[1] if len(cat_cols) > 1 else None
        }

    # 4. Two Numeric columns -> Scatter Plot
    if len(num_cols) >= 2:
        return {
            "chart_type": "scatter",
            "x": num_cols[0],
            "y": num_cols[1],
            "color": cat_cols[0] if cat_cols else None
        }

    # Default fallback
    return {
        "chart_type": "bar",
        "x": cols[0] if cols else None,
        "y": cols[1] if len(cols) > 1 else cols[0]
    }


def create_plotly_figure(df: pd.DataFrame, config: Dict[str, Any], title: Optional[str] = None) -> Optional[go.Figure]:
    """Generates an interactive Plotly figure based on configuration and data."""
    if df is None or df.empty:
        return None

    chart_type = config.get("chart_type", "bar").lower()
    x_col = config.get("x")
    y_col = config.get("y")
    color_col = config.get("color")
    names_col = config.get("names")
    values_col = config.get("values")

    fig = None

    try:
        if chart_type in ["bar", "column"]:
            fig = px.bar(
                df, x=x_col, y=y_col, color=color_col,
                color_discrete_sequence=COLOR_PALETTE,
                text_auto='.2s' if df[y_col].dtype != 'object' else None,
                template="plotly_dark",
                title=title
            )
            fig.update_traces(textposition='outside')
            
        elif chart_type in ["line", "trend"]:
            fig = px.line(
                df, x=x_col, y=y_col, color=color_col,
                markers=True,
                color_discrete_sequence=COLOR_PALETTE,
                template="plotly_dark",
                title=title
            )
            
        elif chart_type in ["area"]:
            fig = px.area(
                df, x=x_col, y=y_col, color=color_col,
                color_discrete_sequence=COLOR_PALETTE,
                template="plotly_dark",
                title=title
            )

        elif chart_type in ["pie", "donut"]:
            fig = px.pie(
                df, names=names_col or x_col, values=values_col or y_col,
                hole=0.4 if chart_type == "donut" else 0.0,
                color_discrete_sequence=COLOR_PALETTE,
                template="plotly_dark",
                title=title
            )
            fig.update_traces(textinfo='percent+label')

        elif chart_type in ["scatter"]:
            fig = px.scatter(
                df, x=x_col, y=y_col, color=color_col,
                size=num_cols[2] if len(df.select_dtypes(include=['number']).columns) > 2 else None,
                color_discrete_sequence=COLOR_PALETTE,
                template="plotly_dark",
                title=title
            )

        if fig:
            fig.update_layout(
                paper_bgcolor='rgba(15, 23, 42, 0.6)',
                plot_bgcolor='rgba(15, 23, 42, 0.6)',
                font=dict(family="Inter, sans-serif", size=13, color="#E2E8F0"),
                margin=dict(l=40, r=40, t=60, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                hoverlabel=dict(bgcolor="#1E293B", font_size=13)
            )

        return fig
    except Exception as e:
        print(f"Chart creation failed: {e}")
        return None
