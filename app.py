import streamlit as st
#emoticono y demás

#st.set_page_config(
 #    page_title="Nirakara Flow App",
  #   page_icon="🤲🏼"

 #)


import pandas as pd
import plotly.express as px
from google.oauth2 import service_account
from google.cloud import bigquery

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from urllib.error import URLError
from pingouin import mixed_anova, read_dataset, pairwise_ttests
import pingouin as pg
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
    ## quito a Carola y beatriz
    df = df.loc[~df.Teacher.isin(["Carola", "Beatriz"])]
    df['id_subject'] = df.email + df.Generation_key
    return df

#Función para subrayar los valores significativos
def hightlight_p_value(row):

    highlight = 'background-color: lightcoral;'
    default = ''

    if type(row) in [float, int]:
        if row < 0.05:
            return highlight
    return default





try:
    df = run_query()
    option = st.sidebar.selectbox(
        'Which variable would you like to choose',
        ('Format', 'Teacher', 'Gender'))
    scales = st.sidebar.multiselect(
        "Choose scales", df.loc[:, 'DASS_depression':'RRS_brooding'].columns.tolist(),
        ['DASS_depression', "DASS_anxiety"]
    )

    if not scales:
        st.error("Please select at least one scale.")
    else:
        for escala in scales:
            height = len(df[option].unique().tolist()) * 400
            fig = px.box(df, x="Program", y=escala, points='all',
                         color="Form", title=escala + ' by ' + option, notched=True,
                         facet_row=option,
                         color_discrete_sequence=px.colors.qualitative.Pastel, template="plotly_dark",
                         height=height,facet_row_spacing = 0.01
                         )
            anova = df.mixed_anova(dv=escala, between="Program", within='Form', subject='id_subject', effsize="ng2",
                                   correction=True)
            anova = anova.style.applymap(hightlight_p_value, subset = ['p-unc'])
            posthocs_anova = pg.pairwise_ttests(dv=escala, within='Form', subject='id_subject', between="Program",
                                          parametric=False, effsize='cohen', interaction=True, correction=True,
                                          data=df).round(3).style.applymap(hightlight_p_value, subset = ['p-unc'])
            anova_mixed = df.mixed_anova(dv=escala, between=option, within='Form', subject='id_subject', effsize="ng2",
                                   correction=True).round(3).style.applymap(hightlight_p_value, subset = ['p-unc'])
            posthocs_anova_mixed = pg.pairwise_ttests(dv=escala, within='Form', subject='id_subject', between=option,
                                          parametric=False, effsize='cohen', interaction=True, correction=True,
                                          data=df).round(3).style.applymap(hightlight_p_value, subset = ['p-unc'])

            st.plotly_chart(fig, use_container_width=True)
            with st.expander("See " + escala + " ANOVA mixed  and Posthoc analysis (Time * " + option + ")"):
                st.markdown("""
                ### Mixed ANOVA (Between Program and Time)

                """)
                st.dataframe(anova)

                st.markdown("""
                ### Posthoc analysis (Between Program and Time)

                """)
                st.dataframe(posthocs_anova)


                st.markdown("""
                ### Mixed ANOVA
                
                """)
                st.dataframe(anova_mixed)
                st.markdown("""
                ### Post hoc

                """)
                st.dataframe(posthocs_anova_mixed)

except URLError as e:
    st.error(
        """
        **This demo requires internet access.**

        Connection error: %s
    """
        % e.reason
    )
