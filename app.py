
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from google.cloud import bigquery
import streamlit as st
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from urllib.error import URLError

st.title("Inferencial data analysis tool")
st.write("Here, a dataframe of app and qualtrics questionnaires. You can interact with the data and answer your own questions. All the dataframe start from a question of author (=Gus)")
st.markdown("""
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
    option = st.selectbox(
        'Which variable would you like to choose',
        ('Format', 'Teacher', 'Gender'))
    scales = st.multiselect(
        "Choose scales", df.loc[:,'DASS_depression':'RRS_brooding'].columns.tolist(), ['DASS_depression', "DASS_anxiety"]
    )
    if not scales:
        st.error("Please select at least one scale.")
    else:
        for escala in scales:
            height = len(df[option].unique()) * 300
            fig = px.box(df, x="Program", y=escala, points='all',
                         color="Form", title=escala + ' by ' + option, notched=True,
                         facet_row=option,
                         color_discrete_sequence=px.colors.qualitative.Pastel, template="plotly_dark",
                         height=height
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
