from typing import List

import streamlit as st
import pandas as pd

from ruins.core import build_config, debug_view, Config, DataManager
from ruins.plotting import sunburst
from ruins.processing.sunburst import ordered_sunburst_data


_TRANSLATE_DE = dict(
    title='Verwendete Klimamodelle',
    intro="""Es gibt eine Vielzahl an unterschiedlichen Klimamodellen,
die auf unterschiedlichen Skalen arbeiten und von unterschiedlichen Voraussetzungen ausgehen.
Das macht es schwer von **dem Klimamodell** zu sprechen und reflektiert die 
Unsicherheit über die Zukunft.

In der Abbildung unten findest du alle Modelle, die für die Erstellung unserer 
Ergebnisse herangezogen wurden, kategorisiert nach dem Globalen und regionalen Modell, sowie
dem RCP Szenario.
"""
)

_TRANSLATE_EN = dict(
    title='Climate models in use',
    intro="""There are tons of different climate models, which operate at different
scales and have different underlying assumptions. That reflects the uncertainty about
our future and thus, there is not **the one correct climate model**.

All models used to calculate our results are shown in the chart. We categorized them by
the global and regional model in use as well as the RCP scenario.
"""
)


def plot_controls(config: Config, expander=st.sidebar) -> None:
    """Add the controls to the application"""
    with expander.expander('Hierachie' if config.lang=='de' else 'Hierachy', expanded=True):
        # set the order 
        o = st.radio('Reihenfolge' if config.lang=='de' else 'Order', options=['GCM -> RCM -> RCP', 'RCP -> GCM -> RCM', 'RCM -> GCM -> RCP'])
        st.session_state.sunburst_order = o.split(' -> ')

        # set the level
        LVL = {2: '1 level', 3: '2 levels', 4: '3 levels'}
        st.select_slider(
            'Anzahl Stufen' if config.lang=='de' else 'Show levels',
            options=list(LVL.keys()),
            value=4,
            format_func=lambda k: LVL.get(k),
            key='sunburst_maxdepth'
        ) 


@st.experimental_memo
def get_cached_data(_dataManager: DataManager, order: List[str]) -> pd.DataFrame:
    return ordered_sunburst_data(_dataManager, order)


def sunburst_plot(dataManager: DataManager, config: Config):
    """Add the plot"""
    # get the ordered data
    df = get_cached_data(dataManager, config['sunburst_order'])
    
    # get the figure
    fig = sunburst(df, maxdepth=config.get('sunburst_maxdepth', 4))

    # add
    st.plotly_chart(fig, use_container_width=True)


def main_app(**kwargs):
    """"""
    # build the config and dataManager from kwargs
    url_params = st.experimental_get_query_params()
    config, dataManager = build_config(url_params=url_params, **kwargs)

    # set page properties and debug view    
#    st.set_page_config(page_title='Climate Model Sunburst', layout=config.layout)
    debug_view.debug_view(dataManager, config, debug_name='DEBUG - initial state')

    # get a translator
    t = config.translator(de=_TRANSLATE_DE, en=_TRANSLATE_EN)

    st.title(t('title'))
    st.markdown(t('intro'))

    # main application
    plot_controls(config)
    sunburst_plot(dataManager, config)

    # end state debug
    debug_view.debug_view(dataManager, config, debug_name='DEBUG - finished app')

if __name__=='__main__':
    import fire
    fire.Fire(main_app)
