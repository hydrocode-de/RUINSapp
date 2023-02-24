import plotly.graph_objects as go
from plotly.colors import n_colors, hex_to_rgb
import pandas as pd

def get_colors(n, breakpoints=['#1b9e77', '#d95f02', '#7570b3']):
    half_1 = int(n / 2)
    half_2 = n - half_1

    col_1 = n_colors(hex_to_rgb(breakpoints[0]), hex_to_rgb(breakpoints[1]), half_1, 'hex')
    col_2 = n_colors(hex_to_rgb(breakpoints[1]), hex_to_rgb(breakpoints[2]), half_2, 'hex')
    
    return [*col_1, *col_2]


def build_ce_ternary(data: pd.DataFrame, feature: str, labels=dict(a='A', b='B', c='C'), cmap_breakpoints=['#1b9e77', '#d95f02', '#7570b3']) -> go.Figure:
    """
    Build the ternary plot for the given dataframe.
    """
    colors = [f'rgb({r},{g},{b})' for _, (r, g, b) in sorted(zip(data[feature], get_colors(30, cmap_breakpoints)))]
    
    fig = go.Figure(go.Scatterternary(
        mode='markers',
        a=[row.iloc[0] for _, row in data.iterrows()],
        b=[row.iloc[1] for _, row in data.iterrows()],
        c=[row.iloc[2] for _, row in data.iterrows()],
        marker=dict(
            size=14,
            color=colors
        ),
        hovertemplate="<br>" + labels['a'] +  ": %{a}%<br>" + labels['b'] + ": %{b}%<br>" + labels['c'] + ": %{c}%<extra></extra>"
    ))

    fig.update_layout(ternary=dict(
        sum=100,
        aaxis=dict(title=labels['a']), 
        baxis=dict(title=labels['b']), 
        caxis=dict(title=labels['c']))
    )
    return fig
