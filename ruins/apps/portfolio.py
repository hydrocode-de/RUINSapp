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


def add_controls(df: pd.DataFrame, container = st) -> None:
    """
    Add the controls for the user
    """
    # extract options - all column except the first 3
    col_opt = [col for col in df.columns][3:]
    
    with container.expander('Plot settings', expanded=True):
        # select the feature
        st.selectbox('Color by', options=col_opt, index=col_opt.index('meanCE'), key="port_feature", help="Choose a feature for coloring the terneray plot")


def add_plot(df: pd.DataFrame, config: Config, container=st) -> None:
    """
    Generate the terneray plot of CEs
    """
    # load the options from the session state
    feature = config.get('port_feature')

    # build the labels
    if config.lang == 'en':
        labels = dict(a='Wheat', b='Maize', c='Greenland')
    else:
        labels = dict(a='Weizen', b='Mais', c='Grünland')
    # get the figure

    # build the figure and add
    fig = build_ce_ternary(df, feature=feature, labels=labels)
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
    add_controls(df, container=st.sidebar)
    add_plot(df, config)

    st.dataframe(df)


if __name__ == '__main__':
    import fire
    fire.Fire(main_app)
