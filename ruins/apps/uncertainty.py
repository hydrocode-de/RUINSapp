from typing import Tuple, List

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.express.colors import unlabel_rgb, label_rgb, n_colors, sequential
import numpy as np
from scipy.stats import norm

from ruins.core import Config, build_config, debug_view
from ruins.plotting import distribution_plot

_TRANSLATE_EN = dict(
    title='Uncertainty & Risk',
    introduction="""
This first playground app will illustrate how uncertainty and risk influence our everyday decisions.
It is quite important to understand the difference between [knightian uncertaintry](https://en.wikipedia.org/wiki/Knightian_uncertainty)
and risk at this simplified example, before we move to climate modeling and weather data.
Taking the whole earth system into account, these concepts apply and are of high importance,
but their interpretration is way more complicated.

DESCRIPTION OF THE SIMPLIFIED EXAMPLE
    """,
    event_1_desc="""
The first event has two possible outcomes, from which we know their expected return distributions,
but we lack knowledge about the probabilities of occurence. Use the slider below to adjust their 
mean outcome and the deviations from this mean.
""",
    event_2_desc="""
In the first event, there was an uncalculatable uncertainty, as we can't predict the outcome. Instead of
throw the dice every time and risk being way off in terms of return, we can take a save route and make
an active decision for another event. The second event has only one outcome, from which we know that the
expected return is worse than the better outcome of the first event. 
We trade off the posibility of very positive outcome at the cost of not being trapped into very bad outcomes.

But is that worth it?
"""
)

_TRANSLATE_DE = dict(
    title='Unsicherheit und Risiko',
    introduction="""
Dieses erste, vereinfachte Beispiel demonstriert wie sich Unsicherheit und Risiko auf
unsere alltäglichen Entscheidungen auswirkt. Es ist wichtig den Unterschied zwischen 
[Knightsche Unsicherheit](https://de.wikipedia.org/wiki/Knightsche_Unsicherheit) anhand dieses stark vereinfachten
Beispiels zu erkunden und zu verstehen, bevor wir die Modelle und Daten der letzten Kapitel betrachten.
Betrachtet man das gesamte Erdsystem, sind Unsicherheit und Risiko für die Interpretierbarkeit der Daten
von fundamentaler Bedeutng, stellen sich jedoch in wesentlich komplexeren Zusammenhängen dar.

BESCHREIBUNG DES VEREINFACHTEN BEISPIELS
""",
    event_1_desc="""
Das erste Ereignis hat zwei verschiedene Ergebnisse. Für jedes kennen wir die drchschnittliche Erwartung und deren
Verteilung, allerdings haben wir keine Information über die Wahrscheinlichkeit, dass eines der Ergebnisse eintritt.
Benutze die Schieberegler um die Verteilungen der Ergebnisse anzupassen.
""",
    event_2_desc="""
Im ersten Ereignis mussten wir mit einer unbestimmbaren Unsicherheit umgehen, da wir das Ergebnis nicht vorhersagen konnten.
Anstatt hier die Würfel entscheiden zu lassen und ein schlechtes Ergebnis zu riskieren, können wir uns gänzlich
umentscheiden und Ereignis 2 eintreten lassen, das nur ein einziges Ergebnis hat. Allerdings ist das Ergebnis hier
schlechter als der bessere Ausgang des ersten Erignisses. Wir erkaufen uns die Sicherheit keine sehr schlechten Ergbnisse
zu haben damit, dass wir auch auf sehr positive Ergebnisse verzichten.

Aber lohnt sich das?
"""
)

def concept_explainer(config: Config, **kwargs):
    """Show an explanation, if it was not already shown.
    """
    # check if we saw the explainer already
    if config.has_key('uncertainty_playground_explainer'):
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
        st.session_state.uncertainty_playground_explainer = True
        st.experimental_rerun()
    else:
        st.stop()


def _helper_plot(ev1: List[Tuple[float, float]], ev2: Tuple[float, float] = None, **kwargs) -> go.Figure:
    # create figure
    fig = go.Figure()

    # build the colorscale with enough colors
    cscale = getattr(sequential, kwargs.get('colorscale', 'Greens'))
    cmap = n_colors(unlabel_rgb(cscale[-1]), unlabel_rgb(cscale[-3]), len(ev1))

    # get a common x
    x = np.linspace(0, 10, 200)

    # iterate over all outcomes
    for i,outcome in enumerate(ev1):
        mu, std = outcome
        y = norm.pdf(x, loc=mu, scale=std)
        y_sum = y.sum()
        y /= y_sum

        # add the traces
        fig.add_trace(
            go.Scatter(x=x, y=y * 100, mode='lines', line=dict(color=label_rgb(cmap[i])), name=f'Outcome #{i + 1}', fill='tozerox')
        )
        fig.add_trace(
            go.Scatter(x=[mu, mu], y=[0, norm.pdf(mu, loc=mu, scale=std) / y_sum * 100], mode='lines', line=dict(color=label_rgb(cmap[i]), width=3, dash='dash'), name=f'Mean #{i + 1}')
        )
    
    # handle second event
    if ev2 is not None:
        mu, std = ev2
        y = norm.pdf(x, loc=mu, scale=std)
        y_sum = y.sum()
        y /= y_sum
        
        # add distribution
        fig.add_trace(
            go.Scatter(x=x, y=y * 100, mode='lines', line=dict(color='orange', width=2), name='Alternative Event', fill='tozerox')
        )
        # add mean
        fig.add_trace(
            go.Scatter(x=[mu, mu], y=[0, norm.pdf(mu, loc=mu, scale=std) / y_sum * 100], mode='lines', line=dict(color='orange', width=2, dash='dash'), name='Alternative Event mean value')
        )

    # adjust figure
    fig.update_layout(
        template='plotly_white',
        legend=dict(orientation='h')
    )

    return fig


def concept_graph(config: Config, expander_container=st.sidebar, **kwargs) -> go.Figure:
    """
    # TODO: document this
    """
    # get the container and translator
    container = kwargs['container'] if 'container' in kwargs else st
    t = config.translator(de=_TRANSLATE_DE, en=_TRANSLATE_EN)

    # ------------------------
    # First PDF
    if not config.has_key('concept_event_1'):
        container.markdown(t('event_1_desc'))
        l1, c1, r1 = container.columns(3)
        l2, c2, r2 = container.columns(3)

        # outcome 1
        l1.markdown('### Outcome 1')
        ou1_mu = c1.slider('Expected value of outcome #1', min_value=1., max_value=10., value=2.5)
        ou1_st = r1.slider('Certainty of outcome #1', min_value=0.1, max_value=3.0, value=0.5)
        
        # outcome 2
        l2.markdown('### Outcome 2')
        ou2_mu = c2.slider('Expected value of outcome #2', min_value=1., max_value=10., value=6.0)
        ou2_st = r2.slider('Certainty of outcome #2', min_value=0.1, max_value=3.0, value=0.4)

        ev1 = [(ou1_mu, ou1_st), (ou2_mu, ou2_st)]
        # add the continue button
        ev1_ok = container.button('WEITER' if config.lang=='de' else 'CONTINUE')
        if ev1_ok:
            st.session_state.concept_event_1 = ev1
            st.experimental_rerun()
        else:
            fig = distribution_plot({'outcomes': ev1, 'coloscale': 'Greens'})
            return fig
    else:
        ev1 = config['concept_event_1']
        ev1_new = []
        for i, out in enumerate(ev1):
            e = expander_container.expander(f'Outcome #{i + 1}', expanded=True)
            mu = e.slider(f'Expected value of outcome # {i + 1}', min_value=1., max_value=10., value=out[0])
            std = e.slider(f'Certainty of outcome # {i + 1}', min_value=0.1, max_value=2.0, value=out[1])
            ev1_new.append((mu, std, ))

    # ------------------------
    # add second event
    container.markdown(t('event_2_desc'))
    l, c, r = container.columns(3)

    # second event
    l.markdown('### Second event')
    e2_mu = c.slider('Expected value of alternative event', min_value=1., max_value=10., value=5.5)
    e2_st = r.slider('Certainty of alternative event', min_value=0.1, max_value=3.0, value=0.2)

    fig = distribution_plot({'outcomes': ev1_new, 'name': 'Original Event', 'colorscale': 'Greens'}, {'outcomes': [(e2_mu, e2_st)], 'name': 'Alternative Event', 'colorscale': 'Oranges'})
    return fig




def concept_playground(config: Config) -> None:
    """
    The concept playground demonstrates how knightian uncertainty
    is different from risk and how it influences everyday decisions.
    """
    # TODO: add the story mode stuff here

    # explainer
    concept_explainer(config)

    # show the graph
    
    fig = concept_graph(config)
    plot_area = st.empty()
    plot_area.plotly_chart(fig, use_container_width=True)


def main_app(**kwargs):
    """
    """
    # build the config and the dataManager from kwargs
    url_params = st.experimental_get_query_params()
    config, dataManager = build_config(url_params=url_params, **kwargs)

    # set page config and debug view
#    st.set_page_config(page_title='Uncertainty Explorer', layout=config.layout)
    debug_view.debug_view(dataManager, config, debug_name='Initial Application State')

    # --------------------------
    # Main App

    # TODO: right now, we have only the playground here
    concept_playground(config)



if __name__ == '__main__':
    main_app()
