import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.colors import hex_to_rgb
import pandas as pd



def mix_color(weights, as_tuple=False, colors=['#1b9e77', '#d95f02', '#7570b3']):
    """mix the colors given the weights"""
    colors = [hex_to_rgb(c) for c in colors]
    r = sum([(w / 100) * c[0] for w, c in zip(weights, colors)])
    g = sum([(w / 100) * c[1] for w, c in zip(weights, colors)])
    b = sum([(w / 100) * c[2] for w, c in zip(weights, colors)])
    
    if as_tuple:
        return (r, g, b)
    else:
        return f"rgb ({r}, {g}, {b})"


def build_ce_ternary(data: pd.DataFrame, labels=dict(a='A', b='B', c='C'), mix_colors=['#1b9e77', '#d95f02', '#7570b3']) -> go.Figure:
    """
    Build the ternary plot for the given dataframe.
    """
    fig = make_subplots(rows=2, cols=2, specs=[[{'rowspan': 2}, {}], [None, {'type': 'ternary'}]])
    colors = [mix_color(row.iloc[:3].values, colors=mix_colors) for _, row in data.iterrows()]
    
    fig.add_trace(go.Scatterternary(
        mode='markers',
        a=[row.iloc[0] for _, row in data.iterrows()],
        b=[row.iloc[1] for _, row in data.iterrows()],
        c=[row.iloc[2] for _, row in data.iterrows()],
        marker=dict(
            size=14,
            color=colors
        ),
        hovertemplate="<br>" + labels['a'] +  ": %{a}%<br>" + labels['b'] + ": %{b}%<br>" + labels['c'] + ": %{c}%<extra></extra>",
        showlegend=False
    ), row=2, col=2)

    fig.add_trace(go.Scatter(
        x=data.meanCE,
        y=data.varCE,
        mode='markers',
        showlegend=False,
        marker=dict(
            size=14,
            color=colors
        ),
        text=[f"{labels['a']}: {row.iloc[0]}%<br>{labels['b']}: {row.iloc[1]}%<br>{labels['c']}: {row.iloc[2]}%" for _, row in data.
        iterrows()],
        hovertemplate="%{text}<extra></extra>"
    ))

    fig.update_layout(
        template='none',
        ternary=dict(
            sum=100,
            aaxis=dict(title=labels['a']), 
            baxis=dict(title=labels['b']), 
            caxis=dict(title=labels['c'])
        ),
        xaxis=dict(title="Variance"),
        yaxis=dict(title="Mean")
    )

    fig.add_trace(go.Bar(
        y=[0.1 for _ in range(len(colors))],
        x=[_ for _ in range(len(colors))],
        marker_color=colors,
        text=[f"{labels['a']}: {row.iloc[0]}%<br>{labels['b']}: {row.iloc[1]}%<br>{labels['c']}: {row.iloc[2]}%" for _, row in data.iterrows()],
        hovertemplate="%{text}<extra></extra>",
        showlegend=False
    ), row=1, col=2)

    fig.update_layout(
        yaxis2=dict(domain=[0.65,0.70], zeroline=False, visible=False),
        xaxis2=dict(domain=[0.65, 0.9], zeroline=False, visible=False),
        margin=dict(t=4, r=10),

    )
    
    return fig
