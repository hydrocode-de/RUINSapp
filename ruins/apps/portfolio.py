import streamlit as st
import pandas as pd

from ruins.core import Config, DataManager, build_config, debug_view
from ruins.plotting.ternary import build_ce_ternary


def load_data(config: Config, dataManager: DataManager) -> pd.DataFrame:
    """
    Return the data
    """
    # load the file
    df = dataManager['CEs_PCSE'].read()

    # calculate mean and var
    df['meanCE'] = df.loc[:,['CE_rcp85','CE_rcp45','CE_rcp26']].mean(axis=1)
    df['varCE'] = df.loc[:,['CE_rcp85','CE_rcp45','CE_rcp26']].var(axis=1)

    return df


def add_controls(df: pd.DataFrame, config: Config, container = st) -> None:
    """
    Add the controls for the user
    """
    with container.expander('Plot settings', expanded=True):
        st.write('Adjust the mixing colors')
        l, c, r = st.columns(3)
        # select the feature
        l.color_picker('Wheat' if config.lang == 'en' else 'Weizen', value='#1b9e77', key='color_wheat')
        c.color_picker('Maize' if config.lang == 'en' else 'Mais', value='#d95f02', key='color_maize')
        r.color_picker('Grassland' if config.lang == 'en' else 'Grünland', value='#7570b3', key='color_gr')
        


def add_plot(df: pd.DataFrame, config: Config, container=st) -> None:
    """
    Generate the terneray plot of CEs
    """
    # build the labels
    if config.lang == 'en':
        labels = dict(a='Wheat', b='Maize', c='Grassland')
    else:
        labels = dict(a='Weizen', b='Mais', c='Grünland')
    
    # get the colors
    colors = [st.session_state.color_wheat, st.session_state.color_maize, st.session_state.color_gr]

    # build the figure and add
    fig = build_ce_ternary(df, labels=labels, mix_colors=colors)
    container.plotly_chart(fig, use_container_width=True)
    

def main_app(**kwargs):
    """
    """
    url_params = st.experimental_get_query_params()
    config, dataManager = build_config(url_params=url_params, **kwargs)
    
    # debug view if configured
    debug_view.debug_view(dataManager, config, debug_name='Initial Application State')

    # try to load
    df = load_data(config, dataManager)

    # add the controls 
    add_controls(df, config, container=st.sidebar)
    add_plot(df, config)



if __name__ == '__main__':
    import fire
    fire.Fire(main_app)
