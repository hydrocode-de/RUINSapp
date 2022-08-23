import os
import streamlit as st
import pandas as pd
import numpy as np
import datetime
from plotly.subplots import make_subplots

from ruins.core import build_config, debug_view, DataManager, Config
from ruins.plotting import floodmodel
from ruins.processing import drain_cap


_INTRO_EN = dict(
    title='Extreme events & flooding',
    introduction="""
    In this section, a model is presented to assess the influence of sea level change, inland precipitation, and 
    management options on flooding risks in a below sea level and thus drained area in northern Germany.
""",
    introduction_slide1="""
    Das Experiment Extremereignisse betrachtet Inlandfluten in der Krummhörn.
    Etwa ein Drittel der Region wurde durch Eindeichung aus ehemaligem Meeresgebiet in bewirtschaftbares Gebiet umgewandelt und liegt unterhalb des mittleren Meeresspiegels. Niederschlagswasser, dass in diesem Gebiet anfällt, muss daher in einem künstlich angelegtem Entwässerungssystemen aus dem Gebiet geschafft werden.
    Das Entwässerungssystem besteht aus Kanälen, Pumpen und Sielen. Ein Siel ist ein Tor im Deich, durch das bei Ebbe Wasser aus den Kanälen in die Nordsee fließen kann. Die Kanäle sammeln das anfallende Wasser und leiten dieses zu den Pumpen oder Sielen.
""",
    introduction_slide2="""
    Die Wassermenge, die durch Siele und Pumpen entwässert werden kann, wird durch den Wasserstand der Nordsee bestimmt. Ist dieser höher als der Wasserspiegel an der Innenseite des Siels, kann nicht gesielt werden. Auch die Pumpen verlieren Leistung, wenn sie gegen einen höheren Außenwasserstand pumpen müssen. Der Tidegang der Nordsee führt zu sich ständig ändernden Wasserspiegeln und damit Pump-/Sielkapazitäten. Neben diesen haben auch die Kanäle nur eine begrenzte Fließkapazität, die Entwässerung kann also auch von der Kanalseite limitiert sein. 
""",
    introduction_slide3="""
    Neben der Wassermenge, die entwässert werden kann, ist das Auftreten von starken Niederschlägen und die Bodenwassersättigung relevant für Überflutungen in der Region. Niederschläge treten üblicherweise mit durchziehenden Tiefdruckgebieten auf. Im Sommer können die Böden der Region Wasser aufnehmen, weswegen nur ein geringer Anteil des Niederschlags in die Kanäle fließt. Im Winter sind die Böden weitestgehend gesättigt und ein großer Teil des Niederschlagswassers muss abgeführt werden. Neben den Niederschlägen können die Tiefdruckgebiete zusätzlich Sturmflutsituation verursachen, die den Wasserstand der Nordsee über den üblichen Tidegang hinaus anheben. In Folge werden die Pumpen insbesondere in den Wintermonaten stark ausgelastet.
""",
    introduction_slide4="""
    Übersteigt das anfallende Wasser die Entwässerungskapazität erhöht sich der Wasserstand in den Kanälen. Wenn bei starken Niederschlägen der Wasserstand in den Kanälen über einen kritischen Wasserstand steigt ist mit ersten Schäden zu rechnen.
""",
    introduction_slide5="""
    Ein steigender mittlerer Meeresspiegel wirkt sich direkt auf die Entwässerungskapazität der Region aus, da Sielen nicht mehr möglich und Pumpen weniger effizient sein wird. Hinsichtlich des Klimawandels stellen die Prognosen zum Meeresspiegelanstieg unter verschiedenen Emmisions-Szenarien und Annahmen zu Umweltprozessen somit eine weitere Quelle Knight’scher Unsicherheiten dar.
""",
    introduction_slide6="""
    Das Risiko erhöhter Wasserspiegel steigt mit steigendem Meeresspiegel. Ein vorausschauendes Absenken des Wasserspiegels in den Kanälen im Vorfeld eines Extremereignissen kann das Risiko von Überflutungen senken.
"""
)

_INTRO_DE = dict(
    title='Extremereignisse & Überflutungen',
    introduction="""
    In diesem Abschnitt wird ein Modell vorgestellt, mit dem sich der Einfluss von Meeresspiegelveränderungen, 
    Inlandsniederschlägen und Managementoptionen auf Überflutungsrisiken in einem unterhalb des Meeresspiegels 
    liegenden und damit entwässerten Gebiet in Norddeutschland auswirken.
""",
    introduction_slide1="""
    Das Experiment Extremereignisse betrachtet Inlandfluten in der Krummhörn.
    Etwa ein Drittel der Region wurde durch Eindeichung aus ehemaligem Meeresgebiet in bewirtschaftbares Gebiet umgewandelt und liegt unterhalb des mittleren Meeresspiegels. Niederschlagswasser, dass in diesem Gebiet anfällt, muss daher in einem künstlich angelegtem Entwässerungssystemen aus dem Gebiet geschafft werden.
    Das Entwässerungssystem besteht aus Kanälen, Pumpen und Sielen. Ein Siel ist ein Tor im Deich, durch das bei Ebbe Wasser aus den Kanälen in die Nordsee fließen kann. Die Kanäle sammeln das anfallende Wasser und leiten dieses zu den Pumpen oder Sielen.
""",
    introduction_slide2="""
    Die Wassermenge, die durch Siele und Pumpen entwässert werden kann, wird durch den Wasserstand der Nordsee bestimmt. Ist dieser höher als der Wasserspiegel an der Innenseite des Siels, kann nicht gesielt werden. Auch die Pumpen verlieren Leistung, wenn sie gegen einen höheren Außenwasserstand pumpen müssen. Der Tidegang der Nordsee führt zu sich ständig ändernden Wasserspiegeln und damit Pump-/Sielkapazitäten. Neben diesen haben auch die Kanäle nur eine begrenzte Fließkapazität, die Entwässerung kann also auch von der Kanalseite limitiert sein. 
""",
    introduction_slide3="""
    Neben der Wassermenge, die entwässert werden kann, ist das Auftreten von starken Niederschlägen und die Bodenwassersättigung relevant für Überflutungen in der Region. Niederschläge treten üblicherweise mit durchziehenden Tiefdruckgebieten auf. Im Sommer können die Böden der Region Wasser aufnehmen, weswegen nur ein geringer Anteil des Niederschlags in die Kanäle fließt. Im Winter sind die Böden weitestgehend gesättigt und ein großer Teil des Niederschlagswassers muss abgeführt werden. Neben den Niederschlägen können die Tiefdruckgebiete zusätzlich Sturmflutsituation verursachen, die den Wasserstand der Nordsee über den üblichen Tidegang hinaus anheben. In Folge werden die Pumpen insbesondere in den Wintermonaten stark ausgelastet.
""",
    introduction_slide4="""
    Übersteigt das anfallende Wasser die Entwässerungskapazität erhöht sich der Wasserstand in den Kanälen. Wenn bei starken Niederschlägen der Wasserstand in den Kanälen über einen kritischen Wasserstand steigt ist mit ersten Schäden zu rechnen.
""",
    introduction_slide5="""
    Ein steigender mittlerer Meeresspiegel wirkt sich direkt auf die Entwässerungskapazität der Region aus, da Sielen nicht mehr möglich und Pumpen weniger effizient sein wird. Hinsichtlich des Klimawandels stellen die Prognosen zum Meeresspiegelanstieg unter verschiedenen Emmisions-Szenarien und Annahmen zu Umweltprozessen somit eine weitere Quelle Knight’scher Unsicherheiten dar.
""",
    introduction_slide6="""
    Das Risiko erhöhter Wasserspiegel steigt mit steigendem Meeresspiegel. Ein vorausschauendes Absenken des Wasserspiegels in den Kanälen im Vorfeld eines Extremereignissen kann das Risiko von Überflutungen senken.
"""
)


def user_input_defaults():
    # streamlit input stuff:
    
    slr = 400   # sea level rise in mm (0, 400, 800, 1200, 1600)

    #recharge_vis = "absolute"   # "cumulative" or "absolute"
    
    # default event z.B.:
    time = "2012"

    #if time == "2012":
    t1 = datetime.date(2011, 12, 28)
    t2 = datetime.date(2012, 1, 12)

        
    ## KGE
    # kge = st.slider("Canal flow uncertainty [KGE * 100]",71,74, value = 74)
    kge = 74 # nicht mehr user input
    
    ## canal flow input
    # canal_flow_scale = st.number_input("Factor to canal capacity", min_value=0.5, max_value=3., value= 1.0, step=0.1) 
    canal_flow_scale = 1.0 # jetzt nicht mehr user input
    

    canal_area = 4 # user input: st.radio(
        #"Share of water area on catchment [%].",
        #(3, 4))
    
    ## pump before event
    advance_pump = 0. # user input: st.radio(
        #"Forecast Pumping",
        #(0, 4)

    ## visualisation of used pump capacity
    # pump_vis = st.radio("Pump capacity visualisation", ["absolute", "cumulative"])

    ## pump efficiency
    # maxdh = st.number_input("Stop pumping if dh at Knock is greater than x dm\n(technical limit = 70dm)", min_value=10, max_value=70, value= 40, step=2) 
    maxdh = 4000 # nicht mehr user input
        
    return slr, t1, t2, kge, canal_flow_scale, canal_area, advance_pump, maxdh


def timeslice_observed_data(dataManager: DataManager, t1, t2, slr):

    extremes = dataManager['hydro_krummh'].read()

    hourly_recharge = extremes['Prec'].to_dataframe().rolling("12h").mean()[t1:t2] # changed by Jonas
    
    tide = extremes['wl_Knock_Outer'].to_dataframe()[t1:t2]
    
    EVEx5_lw_pegel_timesliced = extremes['wl_LW'].to_dataframe()[t1:t2]
    
    pump_capacity_observed = extremes['Knock_pump_obs'].to_dataframe()[t1:t2] / 12.30
    
    return tide, hourly_recharge, EVEx5_lw_pegel_timesliced, pump_capacity_observed


def create_initial_x_dataset(tide_data, hourly_recharge):
    
    wig = tide_data*0
    # what is this and why? Unused!  # comment Jonas: Experimental option to account for a "Wind Induced Gradient" in the canals, which reduces the effective water flow gradient in the drain_cap model
    
    x = pd.DataFrame.from_dict({'recharge' : hourly_recharge,
                                'h_tide' : tide_data,
                                'wig' : wig})
    
    return x 


def create_model_runs_list(all_kge_canal_par_df, kge, canal_flow_scale, canal_area, x_df, advance_pump, maxdh):    
    model_runs = []
    
    kge_canal_par_df = all_kge_canal_par_df.loc[all_kge_canal_par_df.KGE == kge]
    canal_par_array = kge_canal_par_df[['parexponent', 'parfactor']].to_numpy()
    
    for z in canal_par_array:
    
        z[1] /= canal_flow_scale
        
        # run storage model
        (x_df['h_store'], 
         q_pump,
         x_df['h_min'], 
         x_df['flow_rec'], 
         pump_cost) = drain_cap.storage_model(x_df,
                                              z, 
                                              storage = 0, 
                                              h_store = -1350, # geändert von Jonas
                                              canal_area = canal_area, 
                                              advance_pump = advance_pump, 
                                              maxdh = maxdh)
        model_runs.append((x_df['h_store'], pump_cost))
        #pump_capacity_model_runs.append(pump_cost)
    
    # q_pump no usage later?
    
    # return hg_model_runs, pump_capacity_model_runs
    return model_runs


def flood_model(dataManager: DataManager, config:Config, **kwargs):
    """
    Version of the flooding model in which the user can play around with the parameters.
    """
    container = kwargs['container'] if 'container' in kwargs else st
    t = config.translator(de=_INTRO_DE, en=_INTRO_EN)

    st.sidebar.header('Control Panel')


    slr, t1, t2, kge, canal_flow_scale, canal_area, advance_pump, maxdh = user_input_defaults()

    with st.sidebar.expander("Event selection"):
        time = st.radio(
            "Event",
            ("2012", "2017", "choose custom period")    # reduced to 2 nice events -> "custom period" only in expert mode or for self hosting users?
        )
        if time == 'choose custom period':
            t1 = st.date_input("start", datetime.date(2017, 12, 1))
            dt2 = st.number_input("Number of days", min_value=3, max_value=20, value= 10, step=1) 
            t2 = t1 + datetime.timedelta(dt2)
    
    with st.sidebar.expander("Sea level rise"):
        slr = st.radio(
            "Set SLR [mm]",
            (0, 400, 800, 1200, 1600)
        )
    
    if time == "2012":
        t1 = datetime.date(2011, 12, 28)
        t2 = datetime.date(2012, 1, 12)

    if time == "2017":
        t1 = datetime.date(2017, 3, 15)
        t2 = datetime.date(2017, 3, 25)
    
    with st.sidebar.expander("Management options"):
    # pump before event
    #    advance_pump = st.number_input("Additional spare volume in canals", min_value=-5., max_value=8., value= 0., step=0.1)
        advance_pump = st.radio(
            "Forecast Pumping",
            (0, 4)
        )
        Canal_area = st.radio(
            "Share of water area on catchment [%].",
            (3, 4)
        )

    # Model runs:

    (tide, 
    hourly_recharge, 
    EVEx5_lw_pegel_timesliced, 
    pump_capacity_observed) = timeslice_observed_data(dataManager, t1, t2, slr)

    x = create_initial_x_dataset(tide, hourly_recharge)

    all_kge_canal_par_df = dataManager['kge_canal_par'].read()


    hg_model_runs = create_model_runs_list(all_kge_canal_par_df, kge, canal_flow_scale, canal_area, x, advance_pump, maxdh)

    # plotting:
    col1, col2 = container.columns(2)

    with col1:
        fig1 = make_subplots(2, 1)
        fig1 = floodmodel.sea_level(tide_data=tide, knock_level=6.5, fig=fig1, row=1, col=1)
        fig1 = floodmodel.canal_recharge(recharge_data=hourly_recharge, cumsum=False, fig=fig1, row=2, col=1)
        fig1.update_layout(height=600)
        st.plotly_chart(fig1, use_container_width=True)   
    
    with col2:
        fig2 = make_subplots(2, 1)
        fig2 = floodmodel.absolute_water_level(hg_model_runs, EVEx5_lw_pegel_timesliced, fig=fig2, row=1, col=1)
        fig2 = floodmodel.pump_capacity(hg_model_runs, pump_capacity_observed, cumsum=False, fig=fig2, row=2, col=1)
        fig2.update_layout(height=600, legend=dict(orientation="h"))
        st.plotly_chart(fig2, use_container_width=True)



def concept_explainer(config: Config, **kwargs):
    """Show an explanation, if it was not already shown.
    """
    # check if we saw the explainer already
    if config.has_key('extremes_explainer'):
        return
    
    # get the container and a translation function
    container = kwargs['container'] if 'container' in kwargs else st
    t = config.translator(en=_INTRO_EN, de=_INTRO_DE)

    # place title and intro
    container.title(t('title'))
    container.markdown(t('introduction'), unsafe_allow_html=True)

    # check if the user wants to continue
    accept = container.button('WEITER' if config.lang == 'de' else 'CONTINUE')
    if accept:
        st.session_state.extremes_explainer = True
        st.experimental_rerun()
    else:
        st.stop()

    

def main_app(**kwargs):
    """
    """
    # build the config and dataManager from kwargs
    url_params = st.experimental_get_query_params()
    config, dataManager = build_config(url_params=url_params, **kwargs)

    # set page properties and debug view    
    st.set_page_config(page_title='Sea level rise Explorer', layout=config.layout)
    debug_view.debug_view(dataManager, config, debug_name='DEBUG - initial state')

    # explainer
    concept_explainer(config)

    # TODO: expert mode: user takes control over model parameters
    flood_model(dataManager, config)

    # end state debug
    debug_view.debug_view(dataManager, config, debug_name='DEBUG - finished app')


if __name__ == '__main__':
    import fire
    fire.Fire(main_app)
