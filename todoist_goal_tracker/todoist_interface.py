import requests
import pandas as pd
from todoist_api_python.api import TodoistAPI
import numpy as np
import datetime
from datetime import timezone, timedelta


class Todoist_Interface():


    def __init__(self, api_key):
        self.__api_key = api_key
        self.__completed_tasks_url = "https://api.todoist.com/sync/v9/completed/get_all"
        self.__tasks_info_url = "https://api.todoist.com/sync/v9/items/get"
        self.__api = TodoistAPI(self.__api_key)



    @property
    def tasks_df(self):
        return self.__tasks_df



    def get_labels(self):
        try:
            labels = self.__api.get_labels()
        except Exception as error:
            print(error)

        labels_names = []
        for label in labels:
            labels_names.append(label.name)

        return labels_names



    def get_projects(self):
        try:
            projects = self.__api.get_projects()
        except Exception as error:
            print(error)

        projects_names = []
        for project in projects:
            projects_names.append(project.name)

        return projects_names



    def get_sections(self):
        try:
            sections = self.__api.get_sections()
        except Exception as error:
            print(error)

        sections_names = []
        for section in sections:
            sections_names.append(section.name)

        return sections_names



    def __get_open_tasks(self):
        try:
            open_tasks_data = self.__api.get_tasks()
        except Exception as error:
            print(error)

        open_tasks = []
        for task in open_tasks_data:
            task_id = task.id
            try:
                open_task_data = requests.get(self.__tasks_info_url, headers={"Authorization": "Bearer {}".format(self.__api_key)}, params={"item_id":task_id}).json()
                open_task = open_task_data["item"]
                if open_task["section_id"] != None:
                    open_task["section"] = open_task_data["section"]["name"]
                else:
                    open_task["section"] = "-"
                open_task["project"] = open_task_data["project"]["name"]
                open_tasks.append(open_task)
            except Exception as error:
                print(error)

        self.__open_tasks = open_tasks



    def __get_completed_tasks(self, since):
        #since e until : str -> date format "2022-1-15T00:00:00"
        #LIMITE DE COMPLETED TASKS É 200 (DA PARA PAGINAS PELO RESTANTE USANDO O PARAMETRO OFFSET) (NÃO SEI SE É NECESSÁRIO MAIS QUE 200, POIS NO DASHBOARD É POSSIVEL ESCOLHER A DATA PARA DIFERENTES "200"s)
        try:
            completed_tasks_data = requests.get(self.__completed_tasks_url, headers={"Authorization": "Bearer {}".format(self.__api_key)}, params={"limit": "200", "since":since}).json()["items"]
        except Exception as error:
            print(error)

        completed_tasks = []
        for task in completed_tasks_data:
            task_id = task["task_id"]
            try:
                completed_task_data = requests.get(self.__tasks_info_url, headers={"Authorization": "Bearer {}".format(self.__api_key)}, params={"item_id":task_id}).json()
                completed_task = completed_task_data["item"]
                if completed_task["section_id"] != None:
                    completed_task["section"] = completed_task_data["section"]["name"]
                else:
                    completed_task["section"] = "-"
                completed_task["project"] = completed_task_data["project"]["name"]
                completed_tasks.append(completed_task)
            except Exception as error:
                print(error)

        self.__completed_tasks = completed_tasks



    def get_tasks_df(self, since):
        self.__get_open_tasks()
        self.__get_completed_tasks(since)

        open_tasks_df = pd.DataFrame(self.__open_tasks)
        completed_tasks_df = pd.DataFrame(self.__completed_tasks)

        tasks_df = pd.concat([open_tasks_df, completed_tasks_df])
        tasks_df = tasks_df.reset_index()

        #consertando os due dates que veem da API como dicionários
        due_dates = []
        is_recurring = []
        for is_completed, due in zip(tasks_df["checked"], tasks_df["due"].tolist()):
            if is_completed == False:
                due_dates.append(due["date"])
                is_recurring.append(due["is_recurring"])
            else:
                due_dates.append(None)
                is_recurring.append(False)

        tasks_df["Due"] = due_dates
        tasks_df["Is Recurring"] = is_recurring
        tasks_df = tasks_df[tasks_df["Is Recurring"] == False]

        #ajeitando o dataframe
        tasks_df = tasks_df.drop(columns=["Is Recurring", "added_by_uid", "assigned_by_uid", "child_order", "collapsed", "parent_id", "responsible_uid", "sync_id", "user_id", "section_id", "project_id", "duration", "is_deleted", "due"])
        column_order = ['id', 'content', 'priority', "description", "labels", "section", "checked", "Due", "completed_at", "added_at", "project"]
        tasks_df = tasks_df[column_order]
        tasks_df = tasks_df.rename(columns={"id": "Id", "content": "Content", "priority": "Priority", "description": "Description", "labels": "Labels", "section": "Section", "checked": "Is Completed", "completed_at": "Completed At", "added_at": "Created At", "project": "Project"})

        #Transformando strings em datas
        tasks_df['Due'] = pd.to_datetime(tasks_df['Due'], format='ISO8601').dt.date
        tasks_df['Completed At'] = pd.to_datetime(tasks_df['Completed At'], format='ISO8601')
        tasks_df['Created At'] = pd.to_datetime(tasks_df['Created At'], format='ISO8601')

        #consertando fuso horário de UTC para Brasilia
        fuso_brasilia = timezone(timedelta(hours=-3))
        tasks_df['Completed At'] = pd.to_datetime(tasks_df['Completed At']).apply(lambda x: x.replace(tzinfo=timezone.utc).astimezone(fuso_brasilia) if pd.notna(x) else x)
        tasks_df['Created At'] = pd.to_datetime(tasks_df['Created At'].apply(lambda x: x.replace(tzinfo=timezone.utc).astimezone(fuso_brasilia)))
        tasks_df['Completed At'] = tasks_df['Completed At'].dt.date
        tasks_df['Created At'] = tasks_df['Created At'].dt.date

        tasks_df.loc[tasks_df['Description'] == "", 'Description'] = np.nan
        if tasks_df['Description'].str.isnumeric().all():
            tasks_df["Complexity"] = tasks_df["Description"]
            tasks_df.loc[tasks_df['Complexity'] == "", 'Complexity'] = np.nan
            tasks_df["Complexity"] = tasks_df["Complexity"].astype(float)
        else:
            tasks_df["Complexity"] = np.nan

        tasks_df["Is Delayed"] = (tasks_df["Due"] < datetime.datetime.now().date())&(tasks_df["Is Completed"] == False)

        status = []
        for task_bool in tasks_df["Is Completed"]:
            if task_bool == True:
                status.append("Completed")
            else:
                status.append("Open")

        tasks_df["Status"] = status

        #colocando a mesma data em que a tarefa foi completada na coluna "due" para que o dashboard possa filtrar melhor
        tasks_df.loc[tasks_df['Due'].isna(), 'Due'] = tasks_df.loc[tasks_df['Due'].isna(), 'Completed At']

        self.__tasks_df = tasks_df
        return self.__tasks_df
