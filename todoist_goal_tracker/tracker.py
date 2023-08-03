import streamlit as st
import pandas as pd
import datetime
import locale
import numpy as np
from pathlib import Path

locale.setlocale(locale.LC_ALL, 'pt_BR.utf8') #para tratar as datas abreviadas pelo datetime em portugues (e.g. Ago ao invés de Aug)

#pegando os caminhos para os CSVs com as informações sobre as tarefas
TODOIST_CSV_PATH = Path("./data/Inbox.csv")
GSHEET_CSV_PATH = Path("./data/gsheet_inbox.csv")


#------------ FETCHING THE DATA ------------------------------------------------

def get_tasks_from_todois_csv():
    tasks_df = pd.read_csv(TODOIST_CSV_PATH)

    tasks_df = tasks_df.dropna(how="all")
    tasks_df = tasks_df.drop(columns=["INDENT", "AUTHOR", "RESPONSIBLE", "DATE", "DATE_LANG", "TIMEZONE", "DURATION", "DURATION_UNIT"])
    tasks_df = tasks_df.rename(columns={"TYPE": "Type", "CONTENT": "Content", "DESCRIPTION": "Description", "PRIORITY": "Priority"})
    tasks_df = tasks_df[tasks_df["Type"] == "task"].reset_index()
    tasks_df = tasks_df.drop(columns=["index"])

    return tasks_df



def get_tasks_from_gsheet_csv():
    gsheet_tasks_df = pd.read_csv(GSHEET_CSV_PATH)

    gsheet_tasks_df['createdDate'] = pd.to_datetime(gsheet_tasks_df['createdDate'], format='%Y-%m-%dT%H:%M:%S.%fZ')
    gsheet_tasks_df = gsheet_tasks_df[gsheet_tasks_df["createdDate"].dt.date >= datetime.datetime(2023,8,1).date()] #só conta tarefas depois de agosto de 2023
    gsheet_tasks_df = gsheet_tasks_df.drop(columns=["sectionId", "parentTaskId", "description", "parentTask", "section", "assignee", "priority"])

    #CONVERTENDO A COLUNA DUE DE STRING PARA DATETIME

    #consertando as strings da coluna due para as tasks que são recorrentes (every day, every workday)
    next_weekday = datetime.date.today() #para tasks every workday
    today = datetime.date.today() #para tasks every day
    if next_weekday.isoweekday() in set((6, 7)):
        next_weekday += datetime.timedelta(days=next_weekday.isoweekday() % 5)

    gsheet_tasks_df["due"] = gsheet_tasks_df["due"].replace("every workday", next_weekday.strftime('%b. %d'))
    gsheet_tasks_df["due"] = gsheet_tasks_df["due"].replace("every day", today.strftime('%b. %d'))

    gsheet_tasks_df['due'] = pd.to_datetime(gsheet_tasks_df['due'], format='%b. %d')
    gsheet_tasks_df['due'] = gsheet_tasks_df.apply(lambda x:x.due.replace(year=x.createdDate.year),axis=1) #convertendo o ano da coluna due para o mesmo ano da coluna createdDate

    return gsheet_tasks_df



def get_tasks_df(todoist_tasks, gsheet_tasks):
    #UNINDO OS 2 DATAFRAMES PELOS MESMOS IDS, ATRAVÉS DOS NOMES DAS TASKS
    task_ids = []
    for task_name in todoist_tasks["Content"]:
        task_name = task_name.split("@")[0].strip()

        for gsheet_task_name in gsheet_tasks["taskName"]:
            if task_name == gsheet_task_name:
                task_ids.append(gsheet_tasks.loc[gsheet_tasks['taskName'] == task_name, 'taskId'].iloc[0])
    todoist_tasks["id"] = task_ids
    tasks_df = todoist_tasks.merge(gsheet_tasks, left_on='id', right_on='taskId')

    tasks_df = tasks_df.drop(columns=["taskId", "Type"])
    tasks_df = tasks_df.rename(columns={"Content": "Label", "id": "Id", "taskName": "Name", "completed": "Completed", "due": "Due", "createdDate": "Created Date", "completedDate": "Completed Date"})

    #SEPARANDO OS LABELS DOS NOMES DAS TASKS (TODOIST JUNTA OS DOIS COM @S)
    tasks_df["Label"] = tasks_df["Label"].str.split("@")
    tasks_df = tasks_df.explode('Label')
    tasks_df = tasks_df[tasks_df["Label"].str.split() != tasks_df["Name"].str.split()]

    tasks_df["Created Date"] = tasks_df["Created Date"].dt.date #passando de datetime para date

    #DESCOBRE SE UMA TASK É RECORRENTE SE NA DESCRIÇÃO NÃO ESTÁ APENAS A COMPLEXIDADE DA TASK
    tasks_df["Is Recurrent"] = tasks_df["Description"].str.isdigit() == False

    #LIMPANDO AS DESCRIÇÕES (EXTENSÃO HABIT TRACKER TAMBÉM UTILIZA AS DESCRIÇÕES)
    tasks_df["Description"] = tasks_df["Description"].str.strip("**Current streak:**").str.strip("day").str.strip("").astype("float")
    tasks_df["Description"] = tasks_df["Description"].fillna(0)

    #SEPARANDO AS DESCRIÇÕES DE TASKS RECORRENTES (COMPLEXIDADES E DESCRIÇÕES DO HABIT TRACKER)
    tasks_df["Habit Streak"] = tasks_df["Description"] #quantos vezes seguidas uma task recorrente foi realizada pela última vez
    tasks_df["Complexity"] = tasks_df["Description"] #complexidade das tasks (adicionada nas descrições)
    tasks_df.loc[tasks_df['Is Recurrent'] == False, 'Habit Streak'] = np.nan
    tasks_df.loc[tasks_df['Is Recurrent'] == True, 'Complexity'] = np.nan

    #CONSERTAR AS PRIORIDADES (ESTÃO EM ORDEM REVERSA - 1 É O MAIS COMPLEXO)
    tasks_df['Priority'] = tasks_df['Priority'].replace({1: 4, 2: 3, 3: 2, 4: 1})
    #TIRA O BACKSLASH DO NOME DA TASK QUE O TODOIST ADICIONA
    tasks_df["Label"] = tasks_df["Label"].str.replace(r"\\" , "", regex=True).str.strip()

    return tasks_df

    #---------------------------------------------------------------------------
