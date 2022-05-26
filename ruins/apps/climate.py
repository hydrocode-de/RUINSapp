import streamlit as st
import numpy as np

import pandas as pd
from plotly.express.colors import named_colorscales

from ruins.core import build_config, debug_view, Config, DataManager
from ruins.plotting import monthlyx, climate_projection_parcoords
from ruins.components import model_scale_select, data_select
from ruins.components.legacy import topic_select



def climate_data_selector(dataManager: DataManager, config: Config, it: int = 0, variable: str = 'T', expander_container = st.sidebar, layout: str = 'columns', **kwargs):
    """Handles the selection and display of one paralell coordinates plot"""
    # create a unique key
    key = f'rcp_reference_{it}'
    title = f'Select Station #{it + 1}' if config.lang == 'en' else f'Station #{it + 1} auswählen'

    # get the container
    container = kwargs['container'] if 'container' in kwargs else st

    # make the data selection
    data_select.rcp_selector(dataManager, config, title=title, expander_container=expander_container, elements='__all__', layout=layout, RCP_KEY=key, allow_skip=False)

    # get the reference from config
    ref = config[key]

    # make the data sub-selection
    if ref == 'weather':
        data = dataManager['weather'].read()
        drngx = (1980, 2000)
    else:
        data = dataManager['cordex_coast'].read()
        drngx = (2050, 2070)

    # filter for rcps
    if ref in ('rcp26', 'rcp45', 'rcp85'):
        data = data.filter_by_attrs(RCP=ref)

    # create the data range slider
    drng = [pd.to_datetime(data.isel(time=0, vars=1).time.values).year, pd.to_datetime(data.isel(time=-1, vars=1).time.values).year]
    datarng = expander_container.slider('Date Range', drng[0], drng[1], drngx, key=f'dr{it}')

    # switch the variable
    if variable == 'T':
        afu = np.mean
    elif variable == 'Tmin':
        afu = np.min
    elif variable == 'Tmax':
        afu = np.max

    # aggregate
    dyp = data.sel(vars=variable).to_dataframe().resample('1M').apply(afu)
    dyp = dyp.loc[(dyp.index.year>=datarng[0]) & (dyp.index.year<datarng[1]),dyp.columns[dyp.columns!='vars']]

    # plot
    fig = climate_projection_parcoords(data=dyp, colorscale=kwargs.get('colorscale', 'electric'))
    container.plotly_chart(fig, use_container_width=True)


# TODO refactor the plots into the plotting module
def warming_topic_plots(dataManager: DataManager, config: Config, expander_container = st.sidebar):
    """
    """
    cliproj = config['climate_scale']


    # TODO: build this into a Component ?
    if cliproj=='Regional':
        st.warning('Sorry, we currently have issues with the Regional model data. Please come back later.')
        st.stop()
        regaggs = ['North Sea Coast', 'Krummhörn',  'Niedersachsen', 'Inland']
        regagg = st.sidebar.selectbox('Spatial aggregation:', regaggs)

        if regagg=='North Sea Coast':
            climate = xr.load_dataset('data/cordex_coast.nc')
            climate.filter_by_attrs(RCP='rcp45')
        elif regagg=='Krummhörn':
            climate = xr.load_dataset('data/cordex_krummh.nc')

    # TODO: Refactor this part - similar stuff is used in weather explorer
    navi_vars = ['Maximum Air Temperature', 'Mean Air Temperature', 'Minimum Air Temperature']
    navi_var = expander_container.radio("Select variable:", options=navi_vars)
    if navi_var[:4] == 'Mini':
        vari = 'Tmin'
        afu = np.min
        ag = 'min'
    elif navi_var[:4] == 'Maxi':
        vari = 'Tmax'
        afu = np.max
        ag = 'max'
    else:
        vari = 'T'
        afu = np.mean
        ag = 'mean'

    # add plots as needed
    num_of_plots = st.sidebar.number_input('# of datasets to compare', min_value=1, max_value=5, value=1)

    for it in range(int(num_of_plots)):
        # create expander
        plot_expander = st.expander(f'Temperatur (°C) Monthly {ag}', expanded=(it==num_of_plots - 1))
        left, right = plot_expander.columns((2, 8))
        left.markdown('### Options')
        opt = left.container()
        # add the colorbar as option
        cmap = left.selectbox(f'Plot #{it + 1} Colorbar', options=named_colorscales(), format_func=lambda l: l.capitalize())

        # add the Parcoords plot
        climate_data_selector(dataManager, config, it=it, variable=vari, colorscale=cmap, expander_container=opt, container=right)


def main_app(**kwargs):
    """@TODO: describe kwargs here"""
    # build the config and dataManager from kwargs
    url_params = st.experimental_get_query_params()
    config, dataManager = build_config(url_params=url_params, **kwargs)

    # set page properties and debug view
    st.set_page_config(page_title='Climate Explorer', layout=config.layout)
    debug_view.debug_view(dataManager, config, debug_name='Startup')

    # TODO: This can be moved into a closable component. Ie. make the mdoel scale selection first and add it there
    st.header('Climate Projections Explorer')
    st.markdown('''In this section we add climate model projections to the table. The same variables and climate indices are used to explore the projections of different climate models and downscaling models. It is also possible to compare projections under different scenarios about the CO<sub>2</sub>-concentration pathways to observed weather and between different model projections.''',unsafe_allow_html=True)
    
    # ------------------------
    # MAIN APP

    # get model scale
    option_container = st.sidebar.expander('OPTIONS', expanded=True)
    model_scale_select.model_scale_selector(dataManager, config, expander_container=option_container)

    # topic selector
    topic_expander = st.sidebar.expander('Topic selection', expanded=True)
    topic = topic_select.topic_select(config=config, topic_list=['Warming'], expander_container=topic_expander)


    if config['current_topic'] == 'Warming':
        warming_topic_plots(dataManager, config, expander_container=option_container)
    else:
        st.warning(f"The Topic {config['current_topic']} is not available for the climate models explorer yet.")


if __name__ == '__main__':
    main_app()
