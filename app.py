import streamlit as st
#emoticono y demás
st.set_page_config(
     page_title="Nirakara Flow App",
     page_icon="🤲🏼"

 )

import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from google.cloud import bigquery

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from urllib.error import URLError
#Oculatamiento de las mierdas de streamlit
st.markdown(""" <style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style> """, unsafe_allow_html=True)



from PIL import Image
image = Image.open('img/nirakara-lab.jpg')

st.sidebar.image(image, width=250)

st.sidebar.markdown("## Data Exploration tool")
st.sidebar.markdown("""
In this application you can explore the boxplot of each programme (CCT and MBSR) before and after the intervention.
- We have chosen only the people who have filled in the pre and post questionnaire.
- You can explore the different boxplots by choosing a classifier variable.
- You can choose the questionnaires you want to explore. We advise you not to choose too many at once.
""")



# Create API client.
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = bigquery.Client(credentials=credentials)

# Perform query.
# Uses st.cache to only rerun when the query changes or after 10 min.
@st.cache(ttl=600)
def run_query():
    df_1 = client.query("select * from psycho_research.df_scales").to_dataframe()
    df_2 = client.query("select * from psycho_research.df_demographics").to_dataframe()
    df = pd.merge(df_1, df_2, how = 'left', left_on = ['email', 'Generation_key'], right_on = ['email', 'Generation_key'])
    #me quedo sólo con los completos:
    df = df.loc[df.Completion_prepost == 'Completed']
    return df



try:
    df = run_query()
    option = st.sidebar.selectbox(
        'Which variable would you like to choose',
        ('Format', 'Teacher', 'Gender', 'Completion_prepost'))
    scales = st.sidebar.multiselect(
        "Choose scales", df.loc[:, 'DASS_depression':'RRS_brooding'].columns.tolist(),
        ['DASS_depression', "DASS_anxiety"]
    )

    if not scales:
        st.error("Please select at least one scale.")
    else:
        for escala in scales:
            height = len(df[option].unique()) * 400
            fig = px.box(df, x="Program", y=escala, points='all',
                         color="Form", title=escala + ' by ' + option, notched=True,
                         facet_row=option,
                         color_discrete_sequence=px.colors.qualitative.Pastel, template="plotly_dark",
                         height=height,facet_row_spacing = 0.01
                         )
            st.plotly_chart(fig, use_container_width=True)

except URLError as e:
    st.error(
        """
        **This demo requires internet access.**

        Connection error: %s
    """
        % e.reason
    )
