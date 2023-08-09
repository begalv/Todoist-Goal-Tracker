import streamlit as st
import pandas as pd
import datetime
import numpy as np
from todoist_interface import Todoist_Interface
import os
from pathlib import Path
from dotenv import load_dotenv
import plotly.express as px


try:
    dotenv_path = Path('private/.env')
    load_dotenv(dotenv_path=dotenv_path)
    TODOIST_API_KEY = os.getenv("TODOIST_API_KEY")
except Exception as e:
    pass

#TODOIST_API_KEY = "YOUR PRIVATE API KEY GOES HERE" #UNCOMMENT THIS LINE



def at_least_one_in_list(x, y):
    """
    Returns True if at least one element of list y is in list x.

    Returns
    -------
    Bool
        Returns True if at least one element of list y is in list x.
    """
    for e in y:
        if e in x:
            return True
    return False

#------------ DASHBOARD --------------------------------------------------------

class Dashboard():


    def __init__(self, todoist_api):
        """
        data : dataframe
            Pandas dataframe com todos os dados das tarefas
            ----------------------------------------------------------------------------------------------------------------------------------------------------------------
            | Id  | Content | Priority | Description | Labels      | Section | Is Completed | Due  | Completed At | Created At | Project | Complexity | Is Delayed | Status |
            -----------------------------------------------------------------------------------------------------------------------------------------------------------------
            | int |   str   |   int    |     str     | list of str |   str   |     bool     | date |     date     |    date    |   str   |    int     |  bool      |   str  |

        """
        self.__todoist_api = todoist_api

# ---- Filtering ----

    def filter(self, filters):
        """
        Filtra o dataframe das tarefas baseado em uma lista de dicionários

        Parameters
        ----------
        filters : dict
            Dicionário com os filtros que serão aplicados no dataframe de tarefas
            {
                "start date": first date to filter the tasks date range                               | datetime.date
                "end date": last date to filter the tasks date range                                  | datetime.date
                "sections": list of sections to filter the tasks                                      | list of strings
                "goals": list of goals to filter the tasks                                            | list of strings
                "completion": list of completion status (open or completed) to filter the tasks       | list of strings
                "projects": list of projects to filter the tasks                                      | list of strings
            }

        Returns
        -------
        Dataframe
            Pandas dataframe com todos os filtros das tarefas
        """

        filtered_data = self.__data[
            (self.__data["Labels"].apply(lambda x: at_least_one_in_list(x, filters["goals"]))) &
            (self.__data["Section"].isin(filters["sections"])) &
            (self.__data["Project"].isin(filters["projects"])) &
            (self.__data["Status"].isin(filters["completion"])) &
            (self.__data["Due"] >= filters["start date"]) &
            (self.__data["Due"] <= filters["end date"])
            ]

        return filtered_data


# ---- Sidebar ----

    def update_sidebar(self):
        """
        Cria a barra lateral do dashboard que permite o usuário fazer o input dos filtros

        Returns
        -------
        Dict
            Dict with the filters choosen by the user through the sidebar.
            {
                "start date": first date to filter the tasks date range                               | datetime.date
                "end date": last date to filter the tasks date range                                  | datetime.date
                "sections": list of sections to filter the tasks                                      | list of strings
                "goals": list of goals to filter the tasks                                            | list of strings
                "completion": list of completion status (open or completed) to filter the tasks       | list of strings
                "projects": list of projects to filter the tasks                                      | list of strings
            }

        """
        goals = self.__todoist_api.get_labels()
        sections = self.__todoist_api.get_sections()
        projects = self.__todoist_api.get_projects()
        completion_options = ["Open", "Completed"]

        st.sidebar.header("Filters:")
        #st.sidebar.header("#")

        #-- date filter --
        start_date = st.sidebar.date_input(
            "Select the Start Date:",
            datetime.datetime(datetime.datetime.now().year, 1, 1)
        )

        end_date = st.sidebar.date_input(
            "Select the End Date:",
            datetime.datetime.now().date() + datetime.timedelta(days=5)
        )
        st.sidebar.header("#")

        #-- project filter --
        project_container = st.container()
        all_projects = st.sidebar.checkbox("Select all projects")
        if all_projects:
            project = st.sidebar.multiselect(
                "Select the projects:",
                options = projects,
                default = projects
            )
        else:
            project = st.sidebar.multiselect(
                "Select the projects:",
                options = projects
            )
        st.sidebar.header("#")

        #-- section filter --
        section_container = st.container()
        all_sections = st.sidebar.checkbox("Select all sections")
        if all_sections:
            section = st.sidebar.multiselect(
                "Select the sections:",
                options = sections,
                default = sections
            )
        else:
            section = st.sidebar.multiselect(
                "Select the sections:",
                options = sections
            )
        st.sidebar.header("#")

        #-- goal filter --
        goal_container = st.container()
        all_goals = st.sidebar.checkbox("Select all goals")
        if all_goals:
            goal = st.sidebar.multiselect(
                "Select the Goals:",
                options = goals,
                default = goals
            )
        else:
            goal = st.sidebar.multiselect(
                "Select the Goals:",
                options = goals
            )
        st.sidebar.header("#")

        #-- completion filter --
        completion_container = st.container()
        all_completions = st.sidebar.checkbox("Select all status")
        if all_completions:
            completion = st.sidebar.multiselect(
                "Select the Status of the Tasks:",
                options = completion_options,
                default = completion_options
            )
        else:
            completion = st.sidebar.multiselect(
                "Select the Status of the Tasks:",
                options = completion_options,
                default = ["Open"]
            )
        st.sidebar.header("#")
        st.sidebar.header("#")

        sidebar_filters = {
            "start date": start_date,
            "end date": end_date,
            "sections": section,
            "goals": goal,
            "completion": completion,
            "projects": project
        }

        return sidebar_filters


# ---- Mainpage ----

    def update_main_page(self, filtered_data):
        """
        Cria a página principal do dashboard com as tarefas filtradas. Calcula e mostra todas as KPIs, Gráficos e Tabelas.

        Parameters
        ----------
            filtered_data : dataframe
                Pandas dataframe com todos os dados das tarefas
            ----------------------------------------------------------------------------------------------------------------------------------------------------------------
            | Id  | Content | Priority | Description | Labels      | Section | Is Completed | Due  | Completed At | Created At | Project | Complexity | Is Delayed | Status |
            -----------------------------------------------------------------------------------------------------------------------------------------------------------------
            | int |   str   |   int    |     str     | list of str |   str   |     bool     | date |     date     |    date    |   str   |    int     |  bool      |   str  |
        """
        st.title(":memo: Effort Tracker Dashboard")
        #KPIS
        col1, col2, col3, col4 = st.columns(4)

        col1.metric(label="Tasks Qty", value=len(filtered_data))
        col2.metric(label="Priority Avg", value=int(filtered_data["Priority"].mean()))
        col3.metric(label="Complexity Avg", value=int(filtered_data["Complexity"][filtered_data["Complexity"].isna() == False].mean()))
        col4.metric(label="Delayed Tasks Qty", value=len(filtered_data[filtered_data["Is Delayed"]==True]))
        #---------------------
        #Charts

        #Tasks Qty by Date
        col1, col2 = st.columns(2)
        tasks_count = filtered_data['Due'].value_counts().reset_index()
        tasks_count.columns = ['Date', 'Qty']

        st.write("### Tasks Qty by Date")
        fig = px.bar(tasks_count, x='Date', y='Qty')
        st.plotly_chart(fig)

        #---------------------
        #Table
        st.dataframe(filtered_data)


# ---- Updating ----
    def update(self):
        st.set_page_config(page_title="Effort Tracker Dashboard", page_icon=":memo:", layout="wide")

        sidebar_filters = self.update_sidebar()

        since = sidebar_filters["start date"]
        self.__data = self.__todoist_api.get_tasks_df(since="{}-{}-{}T00:00:00".format(since.year, since.month, since.day))

        filtered_data = self.filter(sidebar_filters)

        self.update_main_page(filtered_data)

        #---------- STYLES ----------

        # ---- HIDE STREAMLIT STYLE ----
        hide_st_style = """
                    <style>
                    #MainMenu {visibility: hidden;}
                    footer {visibility: hidden;}
                    header {visibility: hidden;}
                    </style>
                    """
        st.markdown(hide_st_style, unsafe_allow_html=True)

        #---- FIX MAIN PAGE PADDING ----
        header_style = """
                <style>
                       .css-18e3th9 {
                            padding-top: 2rem;
                            padding-bottom: 10rem;
                            padding-left: 5rem;
                            padding-right: 5rem;
                        }
                """
        st.markdown(header_style, unsafe_allow_html=True)


#------------ RUNNING DASHBOARD ------------------------------------------------

if __name__ == "__main__":

    todoist = Todoist_Interface(TODOIST_API_KEY)

    dash = Dashboard(todoist)
    dash.update()
