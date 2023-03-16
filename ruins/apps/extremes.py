import os
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import pickle
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

#load cached events
with open('cache/events.pkl', 'rb') as file:
    events = pickle.load(file)
with open('cache/canals.pkl', 'rb') as file:
    canal_par = pickle.load(file)

def user_input_defaults():
    # streamlit input stuff:
    
    slr = 400   # sea level rise in mm (0, 400, 800, 1200, 1600)
    prec_increase = 1 #Intensify precipitation by factor
    
    # default event z.B.:
    time = list(events.keys())[1]
    
    #if time == "2012":
    t1 = datetime.date(2011, 12, 28)
    t2 = datetime.date(2012, 1, 12)
    
    ## canal flow input
    # canal_flow_scale = st.number_input("Factor to canal capacity", min_value=0.5, max_value=3., value= 1.0, step=0.1) 
    canal_flow_scale = 1.0 # jetzt nicht mehr user input
    

    canal_area = 4 # user input: st.radio(
        #"Share of water area on catchment [%].",
        #(4, 6))
    
    ## pump before event
    advance_pump = 0. # user input: st.radio(
        #"Forecast Pumping",
        #(0, 50)

    ## visualisation of used pump capacity
    # pump_vis = st.radio("Pump capacity visualisation", ["absolute", "cumulative"])

    ## pump efficiency
    # maxdh = st.number_input("Stop pumping if dh at Knock is greater than x dm\n(technical limit = 70dm)", min_value=10, max_value=70, value= 40, step=2) 
    maxdh = 4000 # nicht mehr user input
        
    return slr, t1, t2, canal_flow_scale, canal_area, advance_pump, maxdh, prec_increase


def timeslice_observed_data(dataManager: DataManager, t1, t2, slr, prec_increase, prec_line):
    
    extremes = dataManager['hydro_krummh'].read()
    # recharge
    hourly_recharge = extremes[prec_line].to_dataframe().rolling("12h").mean()[t1:t2].squeeze() * prec_increase # changed by Jonas
    # tide data
    tide = (extremes['wl_Knock_Outer'].to_dataframe()[t1:t2] + slr).squeeze()
    # water level
    EVEx5_lw_pegel_timesliced = (extremes['wl_LW'].to_dataframe()[t1:t2]/1000).squeeze()

    pump_capacity_observed = extremes['Knock_pump_obs'].to_dataframe()[t1:t2].squeeze()
    
    # .squeeze() convertes single pd.DataFrame columns to pd.series objects

    return tide, hourly_recharge, EVEx5_lw_pegel_timesliced, pump_capacity_observed


def create_initial_x_dataset(tide_data, hourly_recharge):
    
    x = pd.DataFrame()
    x['h_tide'] = tide_data
    x['recharge'] = hourly_recharge
    x['wig'] = 0.  # what is this and why? Unused! # comment Jonas: Experimental option to account for a "Wind Induced Gradient" in the canals, which reduces the effective water flow gradient in the drain_cap model
    
    return x 


def create_model_runs_list(canal_flow_scale, canal_area, x_df, advance_pump, maxdh, canal_par_array):
    model_runs = []
    
    ### Canal flow parameters from fitting of runoff to canal gradient data
    #canal_par_array = [[1.112,4156.],[1.045 , 2820.],[0.9946,2142.]]

    ### Define parameters of the default pumping function / pump chart
    x = np.array([7.,6.,5.,4.,3.5,3.,2,1,0,5.,4.,3.5,3.,2]) * 1000 # water gradient [mm] (by factor 1000 from m)
    y = np.array([0,4.2,8.4,12.6,14.5,15.8,17.5,19,20.5,8.4,12.6,14.5,15.8,17.5]) * 3600 / (35000 * 100 * 100) * 1000 * 4  # "*3600 / (35000 * 100 * 100) * 1000 * 4)" converts m^3/s in mm/h
    pumpcap_fit = np.polynomial.polynomial.Polynomial.fit(x = x, y = y, deg = 2)

    for z in canal_par_array:
    
        z[1] /= canal_flow_scale
        
        # run storage model
        (x_df['h_store'], 
         q_pump,
         x_df['h_min'], 
         x_df['flow_rec'], 
         pump_cost,
         store_vol) = drain_cap.storage_model(forcing_data = x_df,
                                              canal_par = z, 
                                              v_store = 0, 
                                              h_store_target = -1350, # geändert von Jonas
                                              canal_area = canal_area, 
                                              h_forecast_pump = advance_pump, 
                                              h_grad_pump_max = maxdh,
                                              pump_par = pumpcap_fit)
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


    slr, t1, t2, canal_flow_scale, canal_area, advance_pump, maxdh, prec_increase = user_input_defaults()

    with st.sidebar.expander("Event selection"):
        time = st.radio(
            "Event",
            (events.keys())
        )
    t1 = events[time]
    t2 = events[time]+datetime.timedelta(days=14)
    
    with st.sidebar.expander("Sea level rise"):
        slr = st.radio(
            "Set SLR [mm]",
            (0,154,249,379,432,522,730,848,918,1143,1676)
        )

    with st.sidebar.expander("Precipitation"):
        prec_increase = st.radio(
            "Intensify precipitation by factor",
            (0.8, 0.9, 1, 1.1, 1.2, 1.3)
        )

        prec_line = st.selectbox(
            "Choose precipitation realization",
            ('Prec', 'Prec_dissagg_1', 'Prec_dissagg_2', 'Prec_dissagg_3', 'Prec_dissagg_4',
           'Prec_dissagg_5', 'Prec_dissagg_6', 'Prec_dissagg_7', 'Prec_dissagg_8',
           'Prec_dissagg_9', 'Prec_dissagg_10', 'Prec_dissagg_11',
           'Prec_dissagg_12', 'Prec_dissagg_13', 'Prec_dissagg_14',
           'Prec_dissagg_15', 'Prec_dissagg_16', 'Prec_dissagg_17',
           'Prec_dissagg_18', 'Prec_dissagg_19', 'Prec_dissagg_20',
           'Prec_dissagg_21', 'Prec_dissagg_22', 'Prec_dissagg_23',
           'Prec_dissagg_24', 'Prec_dissagg_25', 'Prec_dissagg_26',
           'Prec_dissagg_27', 'Prec_dissagg_28', 'Prec_dissagg_29',
           'Prec_dissagg_30', 'Prec_dissagg_31', 'Prec_dissagg_32',
           'Prec_dissagg_33', 'Prec_dissagg_34', 'Prec_dissagg_35',
           'Prec_dissagg_36', 'Prec_dissagg_37', 'Prec_dissagg_38',
           'Prec_dissagg_39', 'Prec_dissagg_40', 'Prec_dissagg_41',
           'Prec_dissagg_42', 'Prec_dissagg_43', 'Prec_dissagg_44',
           'Prec_dissagg_45', 'Prec_dissagg_46', 'Prec_dissagg_47',
           'Prec_dissagg_48', 'Prec_dissagg_49', 'Prec_dissagg_50',
           'Prec_dissagg_51', 'Prec_dissagg_52', 'Prec_dissagg_53',
           'Prec_dissagg_54', 'Prec_dissagg_55', 'Prec_dissagg_56',
           'Prec_dissagg_57', 'Prec_dissagg_58', 'Prec_dissagg_59',
           'Prec_dissagg_60', 'Prec_dissagg_61', 'Prec_dissagg_62',
           'Prec_dissagg_63', 'Prec_dissagg_64', 'Prec_dissagg_65',
           'Prec_dissagg_66', 'Prec_dissagg_67', 'Prec_dissagg_68',
           'Prec_dissagg_69', 'Prec_dissagg_70', 'Prec_dissagg_71',
           'Prec_dissagg_72', 'Prec_dissagg_73', 'Prec_dissagg_74',
           'Prec_dissagg_75', 'Prec_dissagg_76', 'Prec_dissagg_77',
           'Prec_dissagg_78', 'Prec_dissagg_79', 'Prec_dissagg_80')
        )

    with st.sidebar.expander("Management options"):
    # pump before event
    #    advance_pump = st.number_input("Additional spare volume in canals", min_value=-5., max_value=8., value= 0., step=0.1)
        advance_pump = st.radio(
            "Lower water level by x mm NHN before event.",
            (0, 50, 200)
        )
        canal_area = st.radio(
            "Share of water area on catchment [%].",
            (4, 6)
        )
        maxdh = st.radio(
            "Maximum pump gradient [mm]",
            (1, 4500, 6000)
        )

    # Model runs:

    (tide, 
    hourly_recharge, 
    EVEx5_lw_pegel_timesliced, 
    pump_capacity_observed) = timeslice_observed_data(dataManager, t1, t2, slr, prec_increase, prec_line)

    x = create_initial_x_dataset(tide, hourly_recharge)

    hg_model_runs = create_model_runs_list(canal_flow_scale, canal_area, x, advance_pump, maxdh, canal_par)

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
#    st.set_page_config(page_title='Sea level rise Explorer', layout=config.layout)
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
