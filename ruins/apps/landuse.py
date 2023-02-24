from typing import List
from itertools import product

import streamlit as st
from streamlit_graphic_slider import graphic_slider
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

from ruins.core import build_config, debug_view, DataManager, Config
from ruins.plotting import pdsi_plot, tree_plot, variable_plot, windpower_distplot, ternary_provision_plot, management_scatter_plot
from ruins.processing.pdsi import multiindex_pdsi_data
from ruins.processing.windpower import windpower_actions_projection, create_action_grid, uncertainty_analysis


_TRANSLATE_EN = dict(
    title='Land use, climate change & uncertainty',
    introduction="""
    In this section, we provide visualizations to assess the impacts of climate change on yields of different crops 
    and the uncertainty of these impacts. Under these uncertainties, farmers must make decisions that also involve 
    uncertainty.
"""
)

_TRANSLATE_WIND_EN = dict(
    title_dim="Dimensioning a wind turbine",
    description_dim="""Introducing the example how wind turbines are dimensioned
""",
    title_upscale="Upscale to Krummhörn",
    description_upscale="""In this example you can balance out the three kinds of turbines,
E53, E115 and E126 to compare them in terms of number of turbines and total installed capacity.
See also, how the chosen specification will perform in the future using the most recent
climate models for the region.
"""
)

_TRANSLATE_DE = dict(
    title='Landnutzung, Klimawandel und Unsicherheiten',
    introduction="""
    In diesem Abschnitt stellen wir Visualisierungen zur Verfügung, um die Auswirkungen des Klimawandels auf die 
    Erträge verschiedener Kulturpflanzen und die Unsicherheit dieser Auswirkungen zu bewerten. 
    Unter diesen Ungewissheiten müssen Landwirte Entscheidungen treffen, die ihrerseits mit Ungewissheit verbunden sind.
"""
)

_TRANSLATE_WIND_DE = dict(
    title_dim="Dimensioniere eine Windkraftanlage",
    description_dim="""Einführung in die Dimensionierung eines Windkraftparks
""",
    title_upscale="Ein Windpark für die Krummhörn",
    description_upscale="""In diesem Beispiel kannst du einen Windpark für die Krummhörn planen,
indem du die drei Windkraftanlagen E53, E115 und E126 ausbalancierst. Untersuche, wie sich die 
Aufteilung auf die Gesamtanzahl an WIndkraftanlagen und die gesamte Nennleistung auswirkt.
Zusätzlich stehen moderne Klimamodelle für die Region zur Verfügung, um die Leistungsfähigkeit des
Windparks in Zukunft zu bewerten.
"""
)

def concept_explainer(config: Config, **kwargs):
    """Show an explanation, if it was not already shown.
    """
    # check if we saw the explainer already
    if not config.get('story_mode', True) or config.get('landuse_step', 'intro') != 'intro':
        return
    
    # get the container and a translation function
    container = kwargs['container'] if 'container' in kwargs else st
    t = config.translator(en=_TRANSLATE_EN, de=_TRANSLATE_DE)

    # place title and intro
    container.title(t('title'))
    container.markdown(t('introduction'), unsafe_allow_html=True)

    # check if the user wants to continue
    accept = container.button('WEITER' if config.lang == 'de' else 'CONTINUE')
    if accept:
        st.session_state.landuse_step = 'pdsi'
        st.experimental_rerun()
    else:
        st.stop()


def quick_access(config: Config, container=st.sidebar) -> None:
    """Add quick access buttons"""
    # get the step
    step = config.get('landuse_step', 'intro')

    # make translations
    if config.lang == 'de':
        lab_drought = 'Dürreindex'
        lab_crop = 'Wuchsmodelle'
        lab_wind = 'Windenergie'
    else:
        lab_drought = 'Drought index'
        lab_crop = 'Crop models'
        lab_wind = 'Wind power'
    
    # build the colums
    cols = container.columns(2 if step != 'intro' else 3)

    # switch the cases
    if step == 'intro':
        go_pdsi = cols[0].button(lab_drought)
        go_crop = cols[1].button(lab_crop)
        go_wind = cols[2].button(lab_wind)
    elif step == 'pdsi':
        go_pdsi = False
        go_crop = cols[0].button(lab_crop)
        go_wind = cols[1].button(lab_wind)
    elif step == 'crop_model':
        go_pdsi = cols[0].button(lab_drought)
        go_crop = False
        go_wind = cols[1].button(lab_wind)
    elif step == 'wind':
        go_pdsi = cols[0].button(lab_drought)
        go_crop = cols[1].button(lab_crop)
        go_wind = False
    
    # navigate the user
    if go_pdsi:
        st.session_state.landuse_step = 'pdsi'
        st.experimental_rerun()
    
    if go_crop:
        st.session_state.landuse_step = 'crop_model'
        st.experimental_rerun()

    if go_wind:
        st.session_state.landuse_step = 'wind'
        st.experimental_rerun()


#@st.experimental_memo
@st.cache_data
def cached_pdsi_plot(_data, group_by: List[str] = None, add_tree: bool = True, lang='de'):
    # build the multiindex and group if needed
    if group_by is not None:
        _data = multiindex_pdsi_data(_data, grouping=group_by, inplace=True)

    # next check the figure layout
    use_subplots = group_by is not None and add_tree
    if use_subplots:
        # build the figure
        fig = make_subplots(2, 1, shared_xaxes=True, vertical_spacing=0.0, row_heights=[0.35, 0.65])
        fig = tree_plot(_data, fig=fig, row=1, col=1)
        fig.update_layout(height=600)
    else:
        fig = make_subplots(1, 1)

    # run heatmap plot    
    fig = pdsi_plot(_data, fig=fig, row=2 if use_subplots else 1, col=1, lang=lang)

    # return
    return fig


def drought_index(dataManager: DataManager, config: Config) -> None:
    """Loading Palmer drought severity index data for the region"""
    st.title('Drought severity index')
    
    # add some controls
    pdsi_exp = st.sidebar.expander('PDSI options', expanded=True)
    
    # grouping order
    group_by = pdsi_exp.multiselect('GROUPING ORDER', options=['rcp', 'gcm', 'rcm'], default=['rcp', 'gcm'], format_func=lambda x: x.upper())
    if len(group_by) == 0:
        group_by = None
    
    # add tree plot
    if group_by is not None:
        add_tree = pdsi_exp.checkbox('Add a structural tree of model grouping', value=False)
    else:
        add_tree = False

    # load the data
    pdsi = dataManager.read('pdsi').dropna()

    # use the cached version
    fig = cached_pdsi_plot(pdsi, group_by=group_by, add_tree=add_tree)

    # add the figure
    st.plotly_chart(fig, use_container_width=True)


def crop_models(dataManager: DataManager, config: Config) -> None:
    """Load and visualize crop model yields"""
    st.title('Crop models')
    st.warning('Crop model output is not yet implemented')


def windspeed_rcp_plots(dataManager: DataManager, config: Config, key: str = 'windspeed') -> None:
    # get the filter options
    options = ['rcp26', 'rcp45', 'rcp85']
    rcps = st.multiselect('Group by RCP', options=options, key=key)
    if len(rcps) == 0:
        rcps = None
    
    # get the data
    climate = dataManager.read('climate')

    # single plot
    if rcps is None:
        fig = variable_plot(climate, 'u2', rcp=None)
    else:
        colors = [('green', 'lightgreen'), ('blue', 'lightblue'), ('orange', 'yellow')]
        fig = make_subplots(len(rcps), 1, shared_xaxes=True, vertical_spacing=0.0)
        for i, rcp in enumerate(rcps):
            fig = variable_plot(climate, 'u2', rcp=rcp, fig=fig, row= i + 1, color=colors[i][0], bgcolor=colors[i][1])
        fig.update_layout(**{f'xaxis{i + 1}': dict(title='Year' if config.lang=='en' else 'Jahr'), 'height': 600})
    
    # add the plot
    fig.update_layout(legend=dict(orientation='h'), template='plotly_white')
    st.plotly_chart(fig, use_container_width=True)


def upscaled_data_filter(dataManager: DataManager, expert_mode: bool = False, key='upscale_filter', container = st) -> dict:
    """Create a unified interface to filter the upscaled actions"""
    # create options
    filt = dict()

    # only joint data
    filt['joint'] = container.checkbox('Use only data available for all RCPs (N=16)', value=False, key=f'{key}_joint_checkbox')
    
    # filter by year
    _year  = container.slider('Years', value=[2075, 2095], min_value=2006, max_value=2099, step=1, key=f'{key}_year_slider')
    filt['year'] = slice(str(_year[0]), str(_year[1]))

    # this stuff is only expert mode
    if expert_mode:
        # get the data to filter for options
        ts = dataManager.read('wind_timeseries')
        
        # filter RCP
        RCP = {'all': 'All RCPs', 'rcp26': 'RCP 2.6', 'rcp45': 'RCP 4.5', 'rcp85': 'RCP 8.5'}
        _rcp = container.select_slider('Select RCP scenario', options=list(RCP.keys()), value='all', format_func=lambda k: RCP.get(k), key=f'{key}_rcp_slider')
        if _rcp != 'all':
            filt['rcp'] = _rcp

        if not filt['joint']:
            # filter GCMs
            if _rcp != 'all':
                gcms = ts[ts.RCP == _rcp].GCM.unique()
            else:
                gcms = ts.GCM.unique()
            _gcm = container.selectbox('Filter by GCM', options=['- all -', *gcms], format_func=lambda k: k.upper(), key=f'{key}_gcm_selectbox')
            if _gcm != '- all -':
                filt['gcm'] = _gcm

            # filter RCMSs
            if _gcm != '- all -':
                rcms = ts[ts.GCM == _gcm].RCM.unique()
            else:
                rcms = ts.RCM.unique()
            _rcm = container.selectbox('Filter by RCM', options=['- all -', *rcms], format_func=lambda k: k.upper(), key=f'{key}_rcm_selectbox')
            if _rcm != '- all -':
                filt['rcm'] = _rcm
    
    # finally return the filter
    return filt


def upscale_plots(dataManager: DataManager, config: Config, expert_mode: bool = False, key: str = 'upscale') -> None:
    """Show dist-plots for provisioned windpower in Krummhörn along with many filter options"""
    # helper
    turbines = ['E53', 'E115', 'E126']
    # create the layout
    left, right = st.columns((4, 6))
    left.markdown('##### Options')

    # create the filter interface
    filt = upscaled_data_filter(dataManager, expert_mode=expert_mode, key=key, container=left)

    # build a uniform action grid
    actions, scenarios = create_action_grid(dataManager, resolution=0.1, filter_=filt)


    # ugly fix to get the correct group
    COL = {0: 'rgba(255, 136, 0, %.2f)', 1: 'rgba(15, 133, 88, %.2f)', 2: 'rgba(27, 85, 131, %.2f)'}
    grp = [np.argmax(s) for s in scenarios]

    # fill
    plot_area = right.container()
    fill = right.checkbox('Fill PDFs', value=True)
    # create the plot
    fig = None
    for g in set(grp):
        # build the data for this group
        g_actions = [a for a, gr in zip(actions, grp) if gr == g]
        colors = [COL[g] % (i+ 1 / (len(g_actions) + 1)) for i in range(len(g_actions))]
        names = [f"{int(s[g] * 100)}% {turbines[g]}" for s, gr in zip(scenarios, grp) if gr == g]
        
        fig = windpower_distplot(g_actions, fill='tozeroy' if fill else None, colors=colors, names=names, fig=fig)
    
    # update the figure layout
    fig.update_layout(
        title=f"{'%s - ' % filt['rcp'].upper() if 'rcp' in filt else ''}Annual windpower distribution {filt['year'].start} - {filt['year'].stop}",
        height=600,
        xaxis=dict(title='Provisioned Windpower [MW]'),
        yaxis=dict(title='Probability Density'),
    )
    plot_area.plotly_chart(fig, use_container_width=True)


def management_plot(dataManager: DataManager, config: Config, expert_mode: bool = False, key: str = 'management') -> None:
    """"""
    # helper
    turbines = ['E53', 'E115', 'E126']
    # create the layout
    left, right = st.columns((4, 6))
    left.markdown('##### Options')

    # first add the controls for gamma and alpha
    gamma = left.slider('Risk aversion factor', value=1.2, min_value=0.0, max_value=5.0, key=f'{key}_gamm', help='Risk aversion factor. If higher, the decision maker is willing to take more risk.')
    alpha = left.slider('Uncertainty aversion coefficient.', value=0.75, min_value=0.0, max_value=10.0, key=f'{key}_alpha', help='Uncertainty aversion coefficient. If higher, the decision maker is more risk averse.')

    # create the filter interface
    filt = upscaled_data_filter(dataManager, expert_mode=expert_mode, key=key, container=left)

    # build a uniform action grid
    actions, scenarios = create_action_grid(dataManager, resolution=0.1, filter_=filt)

    # perform the uncertainty analysis
    result = uncertainty_analysis(actions, gamma=gamma, alpha=alpha)

    # put the plot
    plot_area = right.container()
    
    # axis options
    OPT = dict(
        eu='Expected utility E[U(x)]',
        ce='Certainty equivalen CER',
        ev='Expected value EV',
        rp='Risk premium RP',
        au='Utility U(x)',
        up='Utility premium UP',
    )
    x = left.selectbox('X-Axis', options=list(OPT.keys()), index=1, format_func=lambda k: OPT.get(k), key=f'{key}_xaxis')
    y = left.selectbox('Y-Axis', options=list(OPT.keys()), index=5, format_func=lambda k: OPT.get(k), key=f'{key}_yaxis')

    fig = management_scatter_plot(result, scenarios=scenarios, x=x, y=y)
    fig.update_layout(
        height=600,
        xaxis=dict(title=OPT.get(x)),
        yaxis=dict(title=OPT.get(y)),
    )
    plot_area.plotly_chart(fig, use_container_width=True)


def upscale_ternary_plot(dataManager: DataManager, config: Config, expert_mode: bool = False, key: str = 'ternary') -> None:
    """Show a ternerary plot for all turbine conbinations in 10% steps with the provisioned power as contour lines"""
    # create the layout
    left, right = st.columns((4, 6))
    left.markdown('##### Options')

    # create the filter interface
    filt = upscaled_data_filter(dataManager, expert_mode=expert_mode, key=key, container=left)

    # create the plot
    fig = ternary_provision_plot(dataManager, filter_=filt)
    fig.update_layout(height=600)
    right.plotly_chart(fig, use_container_width=True)


def wind_turbine_dimensions(config: Config):
    """Let the user play with some wind turbine dimensioning"""
    # get a translator
    t = config.translator(de=_TRANSLATE_WIND_DE, en=_TRANSLATE_WIND_EN)

    # set the introduction
    st.title(t('title_dim'))
    st.markdown(t('description_dim'))

    # build the columns
    mets = st.columns(3)
    l, r = st.columns(2)
    l.info('Use the Form below to check out how the turbines dimensions change the footprint of each wind turbine.')

    # check if there are already specs
    # specs = config.get('wind_dim_specs', [])

    # add the form
    with l.expander('Dimensions' if config.lang=='en' else 'Dimensionierung', expanded=True):
        # mw = st.number_input(
        #     'rated power  production [MW]' if config.lang=='en' else 'Nennleistung [MW]',
        #     value=0.8,
        #     min_value=0.0,
        #     max_value=100.0
        # )
        # dia = st.number_input('Rotor diameter [m]' if config.lang=='en' else 'Rotordurchmesser [m]', value=53, min_value=1, max_value=250)
        mw = st.slider('Rated power production [MW]', min_value=0.0, max_value=25.0, value=1.4)
        dia = st.slider('Rotor diameter [m]', min_value=1, max_value=200, value=64)

        # calculate the dimensions
        area = (5* dia * 3* dia) / 10000
        n_turbines = int(396. / area)
        prod = mw * n_turbines

        # add the metric
        mets[0].metric('Turbines [N]', value=n_turbines)
        mets[1].metric('Installed power [MW]', value=prod)
        mets[2].metric('Area / turbine [ha]', value=area)

        # add = st.button('Add to plot' if config.lang=='en' else 'Zur Abbildung hinzufügen')

        # if add:
        #     specs.append((prod, n_turbines))
        #     st.session_state.wind_dim_specs = specs
        #     st.experimental_rerun()

    # Create the plot
    fig = go.Figure()
    #fig.add_trace(go.Scatter(x=[_[1] for _ in specs], y=[_[0] for _ in specs], mode='markers', name='User defined turbines'))
    fig.add_trace(
        go.Scatter(x=[n_turbines], y=[prod], mode='markers', marker=dict(color='purple', size=35, opacity=0.8), name='User defined turbines')
    )

    # add all scenarios
    for d, name, color in zip([(74.4, 93), (57, 19), (120, 16)], ['E53', 'E115', 'E126'], ['orange', 'green', 'blue']):
        fig.add_trace(
            go.Scatter(x=[d[1]], y=[d[0]], mode='markers+text', text=name, marker=dict(color=color, size=30, opacity=0.3), name=name)
        )
    
    # add figure
    fig.update_layout(xaxis=dict(title='Number of Turbines [N]'), yaxis=dict(title='Installed power [MW]'), legend=dict(orientation='h'))
    r.plotly_chart(fig, use_container_width=True)

    st.markdown('<hr style="margin-top: 3rem; margin-bottom: 3rem;">', unsafe_allow_html=True)
    st.info('Once you got the idea how wind turbines are scaled to the Krummhörn region, we can continue to plan the wind farm based of three different turbines.')
    finish = st.button('CONTINUE' if config.lang=='en' else 'WEITER')
    if finish:
        st.session_state.windpower_stage = 'upscale'
        st.experimental_rerun()


def upscale_windpower(dataManager: DataManager, config: Config) -> None:        
    """Play with upscaling options to see how the wind farm will perform in the future"""
    # get a translator
    t = config.translator(de=_TRANSLATE_WIND_DE, en=_TRANSLATE_WIND_EN)

    # intro
    st.title(t('title_upscale'))
    st.markdown(t('description_upscale'))

    # collect the background images for turbins
    imgs = [
        'https://upload.wikimedia.org/wikipedia/commons/b/b6/Enercon_E53.JPG',
        'https://upload.wikimedia.org/wikipedia/commons/8/88/ENERCON_E-115_Gondel.jpg',
        'https://upload.wikimedia.org/wikipedia/commons/3/31/ENERCON_E-126_EP4_im_Windpark_Holdorf.jpg'
    ]
    attributions = [
        '<a href="https://commons.wikimedia.org/wiki/File:Enercon_E53.JPG">Joseph-Evan-Capelli</a>, <a href="https://creativecommons.org/licenses/by-sa/3.0">CC BY-SA 3.0</a>, via Wikimedia Commons',
        '<a href="https://commons.wikimedia.org/wiki/File:ENERCON_E-115_Gondel.jpg">Adl252</a>, <a href="https://creativecommons.org/licenses/by-sa/4.0">CC BY-SA 4.0</a>, via Wikimedia Commons',
        '<a href="https://commons.wikimedia.org/wiki/File:ENERCON_E-126_EP4_im_Windpark_Holdorf.jpg">Adl252</a>, <a href="https://creativecommons.org/licenses/by-sa/4.0">CC BY-SA 4.0</a>, via Wikimedia Commons'
    ]

    # create options above the image sources
    opts_container = st.sidebar.container()

    # add the attributions
    with st.sidebar.expander('Image sources', expanded=False):
        for attr, name in zip(attributions, ['E53', 'E115', 'E126']):
            st.markdown(f'<small><strong>{name}</strong> - {attr}</small>', unsafe_allow_html=True)
    
    # first add the container for the plots
    plot_area = st.container()

    # add the slider
    specs = graphic_slider([33, 33], images=imgs)

    # by default, the slider returns only the default if not used once
    if len(specs) == 2:
        specs.append(100 - specs[0] - specs[1])

    cols = st.columns(specs)
    for c, s, name in zip(cols, specs, ['E53', 'E115', 'E126']):
        c.markdown(f'<strong style="font-size: 120%">{name}: {s}%</strong>', unsafe_allow_html=True)
    specs = [tuple([_ / 100 for _ in specs])]

    # create the options
    with opts_container.expander('Filter Options', expanded=True):
        all_rcps = st.checkbox('Aggregate all RCPs', value=True)
        rcp26 = st.checkbox('Add RCP 2.6 only', value=False)
        rcp45 = st.checkbox('Add RCP 4.5 only', value=False)
        rcp85 = st.checkbox('Add RCP 8.5 only', value=False)
    
    # sorry, this is ugly...
    filt_opts = [opt for use, opt in zip([all_rcps, rcp26, rcp45, rcp85], [{}, {'rcp': 'rcp26'}, {'rcp': 'rcp45'}, {'rcp': 'rcp85'}]) if use]
    names = [n for use, n in zip([all_rcps, rcp26, rcp45, rcp85], ['All RCPs', 'RCP 2.6', 'RCP 4.5', 'RCP 8.5']) if use]

    # add the plot
    # go for each filter option
    data = []
    dims = []
    for filt in filt_opts:
        _dat, _dim = windpower_actions_projection(dataManager, specs, filter_=filt)
        data.extend(_dat)
        dims.extend(_dim)
    
    metric_exp = plot_area.expander('Statistics', expanded=True)
    metric_container = metric_exp.columns(len(data))

    # show the plot
    fig = windpower_distplot(data, fill='tozeroy', names=names, showlegend=True)

    fig.update_layout(xaxis=dict(title='Annual wind power [MW]'), legend=dict(orientation='h'))
    plot_area.plotly_chart(fig, use_container_width=True)

    for d, dim, name,  col in zip(data, dims, names, metric_container):
        col.markdown(f'#### {name}')
        col.metric('Annual Production [GW]', int(d.mean().sum() / 1000))
        col.metric('Turbines [N]', int(sum(dim)))
        
    st.markdown('<hr style="margin-top: 3rem; margin-bottom: 3rem;">', unsafe_allow_html=True)
    st.info('This was only one example how the windpower can be provisioned for Krummhörn. Make more in-depth in our final expert windpower explorer.')
    finish = st.button('CONTINUE' if config.lang=='en' else 'WEITER')
    if finish:
        st.session_state.windpower_stage = 'final'
        st.experimental_rerun()


def windpower(dataManager: DataManager, config: Config) -> None:
    """Load and visualize wind power experiments"""
    st.title('Wind power experiments')

    PLOTS = dict(
        variable='Climate Model windspeeds',
        upscale='Provisioning windpower for Krummhörn', 
        ternary='Ternary surface plot for Krummhörn',
        management='Uncertainty analysis for windpower provisioning'
    )
    
    # add the expert Mode
    expert_mode = st.sidebar.checkbox('Unlock Expert mode', value=False)

    # add the plot controller
    n_plots = int(st.sidebar.number_input('Number of Charts', value=1, min_value=1, max_value=5))

    for i in range(n_plots):
        with st.expander(f'Detail Chart #{i + 1}', expanded=i == n_plots - 1):
            plt_type = st.selectbox('Chart Type', options=list(PLOTS.keys()), format_func=lambda k: PLOTS.get(k), key=f'plot_select_{i}')

            # switch the plots
            if plt_type == 'variable':
                windspeed_rcp_plots(dataManager, config, key=f'windspeed_{i + 1}')
            
            elif plt_type == 'upscale':
                upscale_plots(dataManager, config, expert_mode=expert_mode, key=f'upscale_{i + 1}')

            elif plt_type == 'ternary':
                upscale_ternary_plot(dataManager, config, expert_mode=expert_mode, key=f'ternary_{i + 1}')

            elif plt_type == 'management':
                management_plot(dataManager, config, expert_mode=expert_mode, key=f'management_{i + 1}')


def windpower_story(dataManager: DataManager, config: Config) -> None:
    """Guide the user through the windpower landuse example"""
    stage = config.get('windpower_stage', 'turbines')

    if stage == 'turbines':
        wind_turbine_dimensions(config)
    
    elif stage == 'upscale':
        upscale_windpower(dataManager, config)

    elif stage == 'final':
        windpower(dataManager=dataManager, config=config)


def main_app(**kwargs):
    """
    """
#    st.set_page_config(page_title='Land use Explorer', layout='wide')

    # build the config and dataManager from kwargs
    url_params = st.experimental_get_query_params()
    config, dataManager = build_config(url_params=url_params, **kwargs)

    # set page properties and debug view    
    debug_view.debug_view(dataManager, config, debug_name='DEBUG - initial state')

    if config.get('story_mode', True):
        step = config.get('landuse_step', 'intro')
    elif config.get('landuse_step', 'intro') == 'intro':
        # if not in story mode, skip the intro
        step = 'pdsi'
    
    # show the quick access buttons
    quick_expander = st.sidebar.expander('QUICK ACCESS', expanded=True)
    quick_access(config, quick_expander)
    
    # explainer
    if step == 'intro':
        concept_explainer(config)
    elif step == 'pdsi':
        drought_index(dataManager, config)
    elif step == 'wind':
        windpower_story(dataManager, config)
    elif step == 'crop_model':
        crop_models(dataManager, config)
    else:
        st.error(f"Got unknown input. Please tell the developer: landuse_step=='{step}'")
        st.stop()


    # end state debug
    debug_view.debug_view(dataManager, config, debug_name='DEBUG - finished app')


if __name__ == '__main__':
    import fire
    fire.Fire(main_app)
