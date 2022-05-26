"""
Topic Selector
This is a legacy component which is not used anymore (26.05.2022).
The code is moved to the legacy submodule to keep the code in case we need it again.
==============

"""
from typing import List
import streamlit as st
from PIL import Image

from ruins.core import Config
from ruins.core.debug_view import debug_view


def current_topic_selector(config: Config, expander_container = st.sidebar, **kwargs):
    """
    Select a topic from a list of topics with a short description and a 
    symbolic image.
    """
    container = st if 'container' not in kwargs else kwargs['container']

    if 'topic_list' in kwargs:
        topic_list = kwargs['topic_list']
    else:
        topic_list = config['topic_list']

    # check if the topic was set
    if config.has_key('current_topic'):
        expander_container.selectbox('Select topic:', topic_list, key='current_topic')
        return

    # From here on full topic select
    # introduction
    container.title("Select a topic you would like to explore")
    container.markdown("""Inside the RUINS App you can explore different topics. Please select one, you can select another topic later in the sidebar.""")

    # use a new container for each row
    row_container = st
    # column topic select (image, description, button)
    image_column, description_column, button_column = row_container.columns([1,3,1])
    
    # TODO: we should host the images in a static folder and use a url
    #image = Image.open('RUINS_logo_small.png') # idea: display symbol images for each topic
    
    image_column.image('https://placebear.com/640/360')
    warming = button_column.button("Click here to select topic Warming")
    description_column.markdown("""**Warming**: In this topic we provide visualisations to explore changes in observed weather data. Based on different variables and climate indices it is possible to investigate how climate change manifests itself in different variables, at different stations and with different temporal aggregation.""")
    row_container.markdown("""___""")

    row_container = st
    # column topic select (image, description, button)
    image_column, description_column, button_column = row_container.columns([1,3,1])

    image_column.image('https://placebear.com/640/360')
    weather_indices = button_column.button("Click here to select topic Weather indices")
    description_column.markdown("""**Weather indices**: Short weather indices description.""") # TODO
    row_container.markdown("""___""")
    
    if warming:
        st.session_state.current_topic = 'Warming'  
        st.experimental_rerun()  
    elif weather_indices:
        st.session_state.current_topic = 'Weather Indices'
        st.experimental_rerun()
    else:
        # dev only
        debug_view(dataManager=None, config=config)
        st.stop()



def topic_select(config: Config, expander_container=st.sidebar, **kwargs) -> str:
    """
    Through this function a topic is selected.
    If we are either not in story_mode or if a topic is already selected, 
    a topic can be selected in a selectbox in the sidebar 
    (compact_topic_selector()).
    Otherwise a topic is selected in the full_topic_selector() which 
    provides a list of topics with a short description and a symbolic 
    image.
    """
    # set default story mode 
    story_mode = config.get('story_mode', True)
    if 'story_mode' in kwargs:
        story_mode = kwargs['story_mode']

    # switch the story_mode
    if not story_mode:
        st.session_state.current_topic = 'Warming'
    
    # select topic
    current_topic_selector(config=config, expander_container=expander_container, **kwargs)

    
def debug_main(**kwargs):
    from ruins.core import build_config
    params = st.experimental_get_query_params()
    config, _ = build_config(omit_dataManager=True, url_params=params, **kwargs)

    topic_select(config=config)

    st.json(st.session_state)

if __name__ == '__main__':
    import fire
    fire.Fire(debug_main)
