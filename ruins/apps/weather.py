from faulthandler import disable
from typing import List, Callable, Tuple
import streamlit as st
import xarray as xr     # TODO: these references should be moved to DataManager
import pandas as pd     # TODO: these references should be moved to DataManager
import numpy as np
import matplotlib.pyplot as plt
from plotly.express.colors import named_colorscales

from ruins.plotting import kde, yrplot_hm, climate_projection_parcoords, plot_climate_indices, sunburst
from ruins.components import data_select, model_scale_select
from ruins.core import build_config, debug_view, DataManager, Config
from ruins.core.cache import partial_memoize
from ruins.processing.climate_indices import calculate_climate_indices, INDICES

# @CONRAD: DAS hier füllt die Spalten auf der neuen Homepage
_TRANSLATE_DE_HOME = dict(
    introduction="""Der Wetter- und Klimadaten Explorer führ in verschiedene Aspekte ....""",
    weather_title="Wetterdaten",
    weather_body="Mehr zu Wetterdaten",
    climate_title="Klimamodelle",
    climate_body="Aggregierte Informationen aus Klimamodellen",
    indices_title="Indices",
    indices_body="Aggregierte Indices zu zukünftigen Projektionen"
)
_TRANSLATE_EN_HOME = dict(
    introduction="""The weather and climate data explorer guides you through...""",
    weather_title="Weather data",
    weather_body="Learn more about our weather data",
    climate_title="Climate Models",
    climate_body="Aggregated information from climate models",
    indices_title="Indices",
    indices_body="Aggregated indices about predictions"
)

_TRANSLATE_DE_CLIMATE = dict(
    title="Unser Wetter in der Zukunft",
    introduction="""Schon die Betrachtung von aktuellen Wetterdaten zeigt, dass diese nicht immer eindeutig sind.
Unsicherheiten bei der Beobachtung von Wetterphänomenen Unwissen über Prozesse wirken sich
auf aktuellen Wetterbeschreibungen aus und erschweren z.B. die Wettervorhersage.

In der Klimaforschung müssen wir nun die nächsten **80 Jahre** vorhersagen. Neben Vorhersageunsicherheiten,
sind aber auch die **Voraussetzungen und Bedingungen** von denen wir ausgehen müssen nicht bekannt und 
auch nicht zu beziffern. 

Wie entwickelt sich die Weltbevölkerung? 

Wie viel CO2 stoßen wir in 30 Jahren aus?

Außerdem: Der Mensch wird durch Managemententscheidungen jene Bedingungen ständig ändern. Dennoch müssen wir heute 
schon Informationen bereitstellen und Abschätzungen liefern. Deshalb ist es so wichtig Wissenslücken zu
schließen und noch wichtiger, Unsicherheit durch Unwissen in Managaementprozesse einzubinden.

Mit dem **Klimamodell Explorer** können einige dieser Szenarien mit einander verglichen werden.
"""
)

_TRANSLATE_EN_CLIMATE = dict(
    title="Projecting weather into the future",
    introduction="""Schon die Betrachtung von aktuellen Wetterdaten zeigt, dass diese nicht immer eindeutig sind.
Unsicherheiten bei der Beobachtung von Wetterphänomenen Unwissen über Prozesse wirken sich
auf aktuellen Wetterbeschreibungen aus und erschweren z.B. die Wettervorhersage.

In der Klimaforschung müssen wir nun die nächsten **80 Jahre** vorhersagen. Neben Vorhersageunsicherheiten,
sind aber auch die **Voraussetzungen und Bedingungen** von denen wir ausgehen müssen nicht bekannt und 
auch nicht zu beziffern. 

Wie entwickelt sich die Weltbevölkerung? 

Wie viel CO2 stoßen wir in 30 Jahren aus?

Außerdem: Der Mensch wird durch Managemententscheidungen jene Bedingungen ständig ändern. Dennoch müssen wir heute 
schon Informationen bereitstellen und Abschätzungen liefern. Deshalb ist es so wichtig Wissenslücken zu
schließen und noch wichtiger, Unsicherheit durch Unwissen in Managaementprozesse einzubinden.

Mit dem **Klimamodell Explorer** können einige dieser Szenarien mit einander verglichen werden.
"""
)

_TRANSLATE_DE_INDICES = dict(
    title="Projektionen in einer Zahl darstellen",
    introduction="""Klimaprojektionen sind der Versuch möglichst viele verschiedene mögliche zukünftige
Szenarien mit in die Betrachtung des Klimawandels einzubeziehen. Durch verschiedene Unsicherheiten können
sich die einzelnen Modelle eines RCPs voneinander jedoch stärker unterscheiden, als zwei andere Modelle, die
sogar von unterschiedlichen Voraussetzungen ausgehen.
Hierdurch wird eine scharfe Aussage über die Folgen von Managementetscheidungen scheinbar unmöglich.
Vor allem, weil Trends in den Modellen so nur sehr schwer zu indentifizieren sind und entscheidende Änderungen
im Rauschen untergehen können.

Mit dem letzten Kapitel wird der Versuch unternommen, all die Variabilität und Unsicherheit auf eine Zahl
runterzubrechen, einem **Klimaindex**.
Dieser Index muss vor allem eine konkrete Bedeutung für einen Bestimmten **Kontext** haben, z.b. einem 
betriebswirtschaftlichen Entscheidungsprozess.

> *Soll ich in den nächsten Jahren eher Winterweizen oder Mais anbauen?*

Die Erkenntnis, dass alle Klimamodelle eine Erhöhung der Durchschnittstemperaturen in den nächsten Jahrzenten
vorhersagen ist für konkrete Entscheidungsprozesse nicht wichtig. Sondern, z.B. wenn Winterweizen weniger sensibel
auf Hitzetage reagiert, ist wichtig ob die Zahl dieser Tage erheblich zunimmt.

Für alle betrachteten Stationen in RUINS können im letzten Kapitel die Projektion der **Klimaindices** bis 2100 erforscht werden.
"""
)

_TRANSLATE_EN_INDICES = dict(
    title="Breaking down projections into one metric",
    introduction="""
"""
)


def climate_indices(dataManager: DataManager, config: Config, container=st, key: int = 1, **kwargs):
    """"""
    # make two selection columns
    left, right = container.columns(2)

    # Station selection
    stations = list(dataManager['weather'].read().keys())
    station_name = left.selectbox('Station Name', options=stations, key=f'climate_station_{key}')

    # Index selection
    ci = right.selectbox('Climate Index', options=list(INDICES.keys()), format_func= lambda k: INDICES.get(k), key=f'climate_index_{key}')
    if ci == 'prec':
        vari = 'Prec'
    elif ci in ('frost', 'tropic'):
        vari = 'Tmin'
    else:
        vari = 'Tmax'

    # calculate the stuff
    data = calculate_climate_indices(dataManager, station=station_name, variable=vari, ci=ci)

    # generate the plot
    fig = plot_climate_indices(data)
    container.plotly_chart(fig, use_container_width=True)

    # TODO: fix the part below
    return
    if ci_topic == 'Ice days (Tmax < 0°C)':
        st.markdown('''Number of days in one year which persistently remain below 0°C air temperature.''')
    elif ci_topic == 'Frost days (Tmin < 0°C)':
        st.markdown('''Number of days in one year which reached below 0°C air temperature.''')
    elif ci_topic == 'Summer days (Tmax ≥ 25°C)':
        st.markdown('''Number of days in one year which reached or exceeded 25°C air temperature.''')
    elif ci_topic == 'Hot days (Tmax ≥ 30°C)':
        st.markdown('''Number of days in one year which reached or exceeded 30°C air temperature.''')
    elif ci_topic == 'Tropic nights (Tmin ≥ 20°C)':
        st.markdown('''Number of days in one year which persistently remained above 20°C air temperature.''')
    elif ci_topic == 'Rainy days (Precip ≥ 1mm)':
        st.markdown('''Number of days in one year which received at least 1 mm precipitation.''')
    return


@partial_memoize(hash_names=['name', 'station', 'variable', 'time', '_filter'])
def _reduce_weather_data(dataManager: DataManager, name: str, variable: str, time: str, station: str = None, _filter: dict = None) -> pd.DataFrame:
    # get weather data
    arr: xr.Dataset = dataManager.read(name)

    if _filter is not None:
        arr = arr.filter_by_attrs(**_filter)

    if station is None:
        base = arr
    else:
        base = arr[station]

    # reduce to station and variable
    reduced = base.sel(vars=variable).resample(time=time)

    if variable == 'Tmax':
        df = reduced.max(dim='time').to_dataframe()
    elif variable == 'Tmin':
        df = reduced.min(dim='time').to_dataframe()
    else:
        df = reduced.mean(dim='time').to_dataframe()
    
    if station is None:
        return df.loc[:, df.columns != 'vars']
    else:
        return df[station]       


def climate_data_selector(dataManager: DataManager, config: Config, it: int = 0, variable: str = 'T', expander_container = st.sidebar, layout: str = 'columns', **kwargs):
    """Handles the selection and display of one paralell coordinates plot"""
    # create a unique key
    key = f'rcp_reference_{it}'
    title = f'Select Station #{it + 1}' if config.lang == 'en' else f'Station #{it + 1} auswählen'

    # get the container
    container = kwargs['container'] if 'container' in kwargs else st

    # if this is not the first iteration, we pre-select an item for rcp
    if it > 0:
        st.session_state[key] = 'rcp45'

    # make the data selection
    data_select.rcp_selector(
        dataManager,
        config,
        title=title,
        expander_container=expander_container,
        elements='__all__',
        layout=layout,
        RCP_KEY=key,
        allow_skip=False
    )

    # get the reference from config
    ref = config[key]

    # make the data sub-selection
    if ref == 'weather':
        data = dataManager.read('weather')
        drngx = (1980, 2000)
    else:
        data = dataManager.read('climate')
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
def climate_plots(dataManager: DataManager, config: Config, expander_container = st.sidebar):
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
        ag = 'min'
    elif navi_var[:4] == 'Maxi':
        vari = 'Tmax'
        ag = 'max'
    else:
        vari = 'T'
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


def warming_data_plotter(dataManager: DataManager, config: Config):
    weather: xr.Dataset = dataManager.read('weather')
    statios = list(weather.keys())
    stat1 = config['selected_station']

    # build the placeholders
    plot_area = st.container()
    control_left, control_right = st.columns((1, 3))

    # TODO refactor in data-aggregator and data-plotter for different time frames


    # ----
    # data-aggregator controls
    navi_vars = ['Maximum Air Temperature', 'Mean Air Temperature', 'Minimum Air Temperature']
    navi_var = control_left.radio("Select variable:", options=navi_vars)
    if navi_var[:4] == 'Mini':
        vari = 'Tmin'
        ag = 'min'
    elif navi_var[:4] == 'Maxi':
        vari = 'Tmax'
        ag = 'max'
    else:
        vari = 'T'
        ag = 'mean'

    # controls end
    # ----

    # TODO: this produces a slider but also needs some data caching
    if config['temporal_agg'] == 'Annual':
        wdata = _reduce_weather_data(dataManager, name='weather', station=config['selected_station'], variable=vari, time='1Y')
        allw = _reduce_weather_data(dataManager, name='weather', variable=vari, time='1Y')

        dataLq = float(np.floor(allw.min().quantile(0.22)))
        datamin = float(np.min([dataLq, np.round(allw.min().min(), 1)]))
        
        if config['include_climate']:
            # get the rcp
            rcp = config['current_rcp']

            data = _reduce_weather_data(dataManager, name='cordex_coast', variable=vari, time='1Y', _filter=dict(RCP=rcp))
            # data_ub = applySDM(wdata, data, meth='abs')
            data_ub = data

            dataUq = float(np.ceil(data_ub.max().quantile(0.76)))
            datamax = float(np.max([dataUq, np.round(data_ub.max().max(), 1)]))
        else:
            dataUq = float(np.ceil(allw.max().quantile(0.76)))
            datamax = float(np.max([dataUq,np.round(allw.max().max(), 1)]))

        datarng = control_right.slider('Adjust data range on x-axis of plot:', min_value=datamin, max_value=datamax, value=(dataLq, dataUq), step=0.1, key='drangew')

        # -------------------
        # start plotting plot
        if config['include_climate']:
            fig, ax = kde(wdata, data_ub.mean(axis=1), split_ts=3)
        else:
            fig, ax = kde(wdata, split_ts=3)

        ax.set_title(stat1 + ' Annual ' + navi_var)
        ax.set_xlabel('T (°C)')
        ax.set_xlim(datarng[0],datarng[1])
        plot_area.pyplot(fig)


    elif config['temporal_agg'] == 'Monthly':
        wdata = _reduce_weather_data(dataManager, name='weather', station=config['selected_station'], variable=vari, time='1M')

        ref_yr = control_right.slider('Reference period for anomaly calculation:', min_value=int(wdata.index.year.min()), max_value=2020,value=(max(1980, int(wdata.index.year.min())), 2000))

        if config['include_climate']:
            # get the rcp and data
            rcp = config['current_rcp']
            data = _reduce_weather_data(dataManager, name='cordex_coast', variable=vari, time='1M', _filter=dict(RCP=rcp))
            
            # make the plot
            fig = yrplot_hm(pd.concat([wdata.loc[wdata.index[0]:data.index[0] - pd.Timedelta('1M')], data.mean(axis=1)]), ref_yr, ag, li=2006, lang=config.lang)
            fig.update_layout(title = f"{stat1} {navi_var} anomaly to {ref_yr[0]}-{ref_yr[1]}")
            plot_area.plotly_chart(fig, use_container_width=True)

            # compare to second station
            sndstat = st.checkbox('Compare to a second station?')
            
        # TODO: break up this as well
        else:
            # make the figure
            fig = yrplot_hm(sr=wdata, ref=ref_yr, ag=ag, lang=config.lang)
            fig.update_layout(title = f"{stat1} {navi_var} anomaly to {ref_yr[0]}-{ref_yr[1]}")
            plot_area.plotly_chart(fig, use_container_width=True)


def inject_cordex_overview(dataManager: DataManager, expanded: bool = False):
     with st.expander('CLIMATE MODEL OVERVIEW', expanded=expanded):
            # laod the cordex overview data
            overview = dataManager['cordex_overview'].read()

            # build the plot
            st.info('The Graph below groups all climate models available to RUINS into their global and regional family. Click on any element to expand it')
            fig = sunburst(overview, maxdepth=4)
            st.plotly_chart(fig, use_container_width=True)


def quick_access_buttons(config: Config, container = st.sidebar):
    """Add quick access button to skip parts of the Weather explorer"""
    # get the current stage
    stage = config.get('quick_access')

    # make columns
    #b, l, r = container.columns(3)
    
    # add home button
    go_home = container.button('HOME', use_container_width=True)
    if go_home:
        st.session_state.quick_access = 'home'
        st.experimental_rerun()

    # make translations
    if config.lang == 'de':
        lab_weather = 'Wetterdaten Explorer'
        lab_climate = 'Klimamodell Explorer'
        lab_index = 'Klimadaten Indices'
    else:
        lab_weather = 'Weather explorer'
        lab_climate = 'Climate explorer'
        lab_index = 'Climate indices'

    # switch the cases
    if stage == 'climate':
        go_weather = container.button(lab_weather, use_container_width=True)
        go_climate = False
        go_idx = container.button(lab_index, use_container_width=True)
    elif stage == 'index':
        go_weather = container.button(lab_weather, use_container_width=True)
        go_climate = container.button(lab_climate, use_container_width=True)
        go_idx = False
    else:
        go_weather = False
        go_climate = container.button(lab_climate, use_container_width=True)
        go_idx = container.button(lab_index, use_container_width=True)

    # check if the Weather explorer is needed
    if go_weather:
        st.session_state.quick_access = 'weather'
        st.experimental_rerun()
    
    # check if the Climate explorer is needed
    if go_climate:
        if 'include_climate' in st.session_state:
            del st.session_state['include_climate']
        st.session_state.quick_access = 'climate'
        st.experimental_rerun()
    
    # check if the Climate indices are needed
    if go_idx:
        if 'include_climate' in st.session_state:
            del st.session_state['include_climate']
        st.session_state.quick_access = 'index'
        st.experimental_rerun()


def weather_stage(dataManager: DataManager, config: Config, data_expander=st.sidebar):
    # Story mode - go through each setting
    # update session state with current data settings
    data_expander = st.sidebar.expander('Data selection', expanded=True)
    data_select.data_select(dataManager, config, expander_container=data_expander, container=st)
    
    
    # build the app
    st.header('Weather Data Explorer')
    # TODO: move this text also into story mode?
    st.markdown('''In this section we provide visualisations to explore changes in observed weather data. Based on different variables and climate indices it is possible to investigate how climate change manifests itself in different variables, at different stations and with different temporal aggregation.''',unsafe_allow_html=True)

    warming_data_plotter(dataManager, config)

    # transition page
    st.markdown("""<hr style="margin-top: 4rem; margin-bottom: 2rem;" />""", unsafe_allow_html=True)
    st.success('Even about the present there is uncertainty! What about the future?')
    ok = st.button('LEARN MORE')

    if ok:
        st.session_state.quick_access = 'transition_climate'
        st.experimental_rerun()


def climate_stage(dataManager: DataManager, config: Config):
    # Story mode - go through each setting

    # update session state with current settings
    # get model scale
    option_container = st.sidebar.expander('OPTIONS', expanded=True)
    model_scale_select.model_scale_selector(dataManager, config, expander_container=option_container)

    # inject the overview
    inject_cordex_overview(dataManager)
    
    # run main visualization
    climate_plots(dataManager, config, expander_container=option_container)

    # transition page
    st.markdown("""<hr style="margin-top: 4rem; margin-bottom: 2rem;" />""", unsafe_allow_html=True)
    st.success('How do we make sense of this? Can we identify trends?')
    ok = st.button('LEARN MORE')

    if ok:
        st.session_state.quick_access = 'transition_index'
        st.experimental_rerun()


def indices_stage(dataManager: DataManager, config: Config, data_expander=st.sidebar):
    # Story mode - go through each setting
    # update session state with current data settings
    # data_expander = st.sidebar.expander('Data selection', expanded=True)
    # data_select.selected_station_selector(dataManager, config, expander_container=data_expander)
    # data_select.rcp_selector(dataManager, config, expander_container=data_expander)

    # build the panel
    N = int(st.sidebar.number_input('Anzahl Abbildungen' if config.lang == 'de' else 'Number of Plots', min_value=1, max_value=10, value=1))

    for i in range(N):
        with st.expander(f'CLIMATE PLOT #{i + 1}', expanded=i == N - 1):
            # run actual visualization
            climate_indices(dataManager, config, key=i)


def transition_page(dataManager: DataManager, config: Config) -> None:
    """
    This Transition is shown when the user switches from weather explorer to
    climate projections or further to climate indices, without using the quick access buttons.
    The page can be used to present a primer how the two topics are related.
    """
    # check with transition page is needed
    if config['quick_access'] == 'transition_climate':
        t = config.translator(de=_TRANSLATE_DE_CLIMATE, en=_TRANSLATE_EN_CLIMATE)
        next_stage = 'climate'
    elif config['quick_access'] == 'transition_index':
        t = config.translator(de=_TRANSLATE_DE_INDICES, en=_TRANSLATE_EN_INDICES)
        next_stage = 'index'
    
    # build the page
    st.header(t('title'))
    st.markdown(t('introduction'), unsafe_allow_html=True)

    # add the sunburst plot
    if config['quick_access'] == 'transition_climate':
        inject_cordex_overview(dataManager, expanded=True)

    # add continue button
    ok = st.button('WEITER' if config.lang=='de' else 'CONTINUE')

    if ok:
        st.session_state.quick_access = next_stage
        st.experimental_rerun()
    else:
        st.stop()


def homepage(config: Config):
    """
    Landing page for the weather explorer
    """
    # get a translator
    t = config.translator(de=_TRANSLATE_DE_HOME, en=_TRANSLATE_EN_HOME)

    # add a title 
    st.title('Weather and Climate explorer')
    st.markdown(t('introduction'))
    
    # add columns to make a quick access
    left, center, right = st.columns(3)

    # create each of the cards
    left.markdown(f"### {t('weather_title')}\n{t('weather_body')}")
    center.markdown(f"### {t('climate_title')}\n{t('climate_body')}")
    right.markdown(f"### {t('indices_title')}\n{t('indices_body')}")

    # add the buttons

    # go to weather explorer
    go_weather = left.button('OPEN APP', key="open1")
    if go_weather:
        st.session_state.quick_access = 'weather'
        st.experimental_rerun()

    # go to climate explorer
    go_climate = center.button('OPEN APP', key="open2")
    if go_climate:
        st.session_state.quick_access = 'climate'
        st.experimental_rerun()

    go_indices = right.button('OPEN APP', key="open3")
    if go_indices:
        st.session_state.quick_access = 'index'
        st.experimental_rerun()

    # Add the more info links
    st.markdown('<hr style="margin-top: 35px; margin-bottom: 15px">', unsafe_allow_html=True)
    if config.lang == 'en':
        lab = "Find more detailed info about some topics here"
    else:
        lab = "Detailierte Informationen zu einigen Themen können hier abgerufen werden"
    
    with st.expander(lab, expanded=False):
        go_rcp = st.button('Details on RCP Sceanrios', use_container_width=True)
        if go_rcp:
            st.warning('Sorry. Ich funktioniere leider noch nicht')
            #st.session_state.quick_access = 'transition_climate'
            #st.experimental_rerun()
        go_models = st.button('Einordnung aller verwendeten Klimamodelle.', use_container_width=True)
        if go_models:
            st.warning('Sorry. Ich funktioniere auch noch nicht.')
    


def main_app(**kwargs):
    """Describe the params in kwargs here

    The main app has three 'stages': 
      
      * learning about weather
      * learning about climate
      * condensing info into climate indices

    
    """
    # build the config and dataManager from kwargs
    url_params = st.experimental_get_query_params()
    config, dataManager = build_config(url_params=url_params, **kwargs)

    # set page properties and debug view    
#    st.set_page_config(page_title='Weather Explorer', layout=config.layout)
    debug_view.debug_view(dataManager, config, debug_name='DEBUG - initial state')

    # check if a stage was set
    if not config.has_key('quick_access'):
        st.session_state.quick_access = 'home'
    stage = config['quick_access']

    # home page has no quick access
    if stage == 'home':
        homepage(config)
        st.stop()
    # add the skip buttons
    btn_expander = st.sidebar.expander('QUICK ACCESS', expanded=True)
    quick_access_buttons(config, container=btn_expander)


    # -------------
    # Weather Stage
    if stage == 'weather':
        weather_stage(dataManager, config)
    elif stage == 'climate':
        climate_stage(dataManager, config)
    elif stage == 'index':
        indices_stage(dataManager, config)
    elif stage.startswith('transition'):
        transition_page(dataManager, config)
    else:
        st.error(f"We received weird data. A quick_access='{stage}' does not exist. Please contact the developer.")
        st.stop()
        
    # end state debug
    debug_view.debug_view(dataManager, config, debug_name='DEBUG - finished app')


if __name__ == '__main__':
    import fire
    fire.Fire(main_app)
