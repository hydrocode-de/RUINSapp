import streamlit as st

from ruins.core import build_config, debug_view, Config
from ruins.plotting import plot_extreme_pdf

_TRANSLATE_DE = dict(
    title="Temperaturen verschieben sich",
    intro="""Dies ist ein langer introtext für dieses Beispiel""",
    temp_intro="""
Wähle zuerst die **mittlere Temperatur** von der du ausgehen möchtest.

Im zweiten Slider musst du die *Variabilität* der mittleren Temperatur angeben.
""",
    temp_outro="""Nun beschreibt die Abbildung den **Ist**-Zustand, also die Häufigkeit
mit der kalte oder warme Tage vorkommen und wie häufig es zu extremen Ereignissen kommt.
Im nächsten Schritt können wir die Erde erwärmen.
""",
    increase_intro="""In diesem Schritt kannst du nun die Durchschnittstemperatur auf
der Erde erhöhen. Eine Erhöhung um **1°C** Celsius mag nicht nach sehr viel klingen, und
natürlich sind die Schwankungen an einem einzigen Tag sehr viel höher, doch beobachte
genau, was mit den **dunkelroten Punkten** in der Abbildung passiert, wenn die Temperatur
sich erhöht.
""",
    increase_outro="""Wenn du die Abbildung genauer betrachtest siehst du zwei Dinge:

  * Es gibt deutlich mehr heiße Tage
  * Es gibt deutlich weniger kalte Tage

Mehr heiße Tage können wir gut mit Wetterbeobachtungen belegen. Allerdings kommt es 
nach wie vor zu **kalten** Extremereignissen. Dies legt nahe, dass sich auch die **Verteilung**
der durchschnittlichen Temperaturen geändert haben muss
""",
)

_TRANSLATE_EN = dict(
    title="Temperatures shift",
    intro="""This is a long intro-text for this example""",
    temp_intro="""
First select the **mean temperature** that you will rely on.

The second slider asks for the temperature's variability.
""",
    temp_outro="""The charts illustrates the current situation.
That is the frequency of warm and cold days as well as extremes.
As a next step, you can increase temperature on earth.
""",
    increase_intro="""Now it's time to increase the temperature on Earth.
A rise of **1°C** might not sound like much, and of course temperature is way more
volatile during the day, but watch out for the **darkred points** on the chart, when
you increase mean temperature.
""",
    increase_outro="""The chart suggest two main observations:

  * There are way more hot days
  * There are way less frost days

We find evidence for more hot days in our observation data. But other than the 
graph suggests, we still have cold and frost days. 
This implies that also the **distribution** of mean temperatures must have changed.
""",
)


def explainer(config: Config) -> None:
    """Introduce the concept"""
    # show the intro
    t = config.translator(de=_TRANSLATE_DE, en=_TRANSLATE_EN)
    st.title(t('title'))
    st.markdown(t('intro'))

    ok = st.button('GOT IT. Get started...')
    if ok:
        st.session_state.tshift_stage = 'temperature_intro'
        st.experimental_rerun()

    
def temperature_dist_intro(config: Config) -> None:
    """Introduce temperature distributions"""
    # explain
    t = config.translator(de=_TRANSLATE_DE, en=_TRANSLATE_EN)
    
    st.title(t('title'))
    plot = st.empty()
    st.markdown(t('temp_intro'))

    # build a slider
    mu = st.slider('Temperature', value=13.3, min_value=4., max_value=24., step=0.1, key='mu1')
    std = st.slider('Variability', value=0.1 * mu, min_value=0.0, max_value=10.0, step=0.01, key='std1')

    # make the plot
    fig = plot_extreme_pdf(mu, std)
    plot.plotly_chart(fig, use_container_width=True)

    # outro
    st.markdown("""<hr style="margin-top: 3rem; margin-bottom: 3rem;">""", unsafe_allow_html=True)
    st.markdown(t('temp_outro'))
    ok = st.button('ERDE ERWÄRMEN' if config.lang=='de' else 'WARM THE EARTH')
    if ok:
        st.session_state.tshift_stage = 't_increase'
        st.experimental_rerun()


def increase_temperatures(config: Config) -> None:
    """Increase the temperature on earth"""
    t = config.translator(de=_TRANSLATE_DE, en=_TRANSLATE_EN)

    # create the sidebar
    mu = st.sidebar.slider('Temperature', value=13.3, min_value=4., max_value=24., step=0.1, key='mu1')
    std = st.sidebar.slider('Variability', value=0.1 * mu, min_value=0.0, max_value=10.0, step=0.01, key='std1')

    # add the title
    st.title(t('title'))
    plot = st.empty()
    st.markdown(t('increase_intro'))

    # make the controller to increase temperature
    mu2 = st.slider('New temperature', min_value=mu, value=mu + 1.5, max_value=25., step=0.1, key='mu2')

    # make the plot
    fig = plot_extreme_pdf([mu, mu2], [std, std])
    plot.plotly_chart(fig, use_container_width=True)

    # outro
    st.markdown("""<hr style="margin-top: 3rem; margin-bottom: 3rem;">""", unsafe_allow_html=True)
    st.markdown(t('increase_outro'))
    
    # button
    ok = st.button('DIE VERTEILUNG ÄNDERN...' if config.lang=='de' else 'CHANGE THE DISTRIBUTION')
    if ok:
        st.session_state.tshift_stage = 'final'
        st.experimental_rerun()


def full_temperature_shift(config: Config) -> None:
    """Full application with all controls"""
    t = config.translator(de=_TRANSLATE_DE, en=_TRANSLATE_EN)

    # create sidebar
    st.sidebar.markdown('#### Present temperature')
    mu = st.sidebar.slider('Temperature', value=13.3, min_value=4., max_value=24., step=0.1, key='mu1')
    std = st.sidebar.slider('Variability', value=0.1 * mu, min_value=0.0, max_value=10.0, step=0.01, key='std1')
    
    st.sidebar.markdown('#### Future temperatures')
    mu2 = st.sidebar.slider('New temperature', min_value=mu, value=mu + 1.5, max_value=25., step=0.1, key='mu2')
    std2 = st.sidebar.slider('Variability', value=0.1 * mu2, min_value=0.0, max_value=10.0, step=0.01, key='std2')

    # add the title
    st.title(t('title'))
    
    # make the plot
    fig = plot_extreme_pdf([mu, mu2], [std, std2])
    fig = st.plotly_chart(fig, use_container_width=True)


def main_app(**kwargs):
    # build the config and dataManager from kwargs
    url_params = st.experimental_get_query_params()
    config, _ = build_config(url_params=url_params, omit_dataManager=True, **kwargs)

    # set page properties and debug view
#    st.set_page_config(page_title='Temperature shift', layout=config.layout)
    debug_view.debug_view(None, config, 'DEBUG - initial state')

    # MAIN APP
    # -----------
    stage = config.get('tshift_stage', 'intro')
    if stage == 'intro':
        explainer(config)
    elif stage == 'temperature_intro':
        temperature_dist_intro(config)
    elif stage == 't_increase':
        increase_temperatures(config)
    elif stage == 'final':
        full_temperature_shift(config)
    else:
        st.error("""The application is in an undefinded state. Please contact the developer with the info below""")
        st.json({'message': 'tshift_stage is unkown', 'value': stage, 'origin': 'temperature_shift.py',})
        st.stop()


    # end state debug
    debug_view.debug_view(None, config, 'DEBUG - final state')



if __name__ == '__main__':
    import fire
    fire.Fire(main_app)
