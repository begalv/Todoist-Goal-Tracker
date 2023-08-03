from todoist_goal_tracker.tracker import *

#testes
todoist_tasks_df = get_tasks_from_todois_csv()
gsheet_tasks_df = get_tasks_from_gsheet_csv()

tasks_df = get_tasks_df(todoist_tasks_df, gsheet_tasks_df)

print(tasks_df)
