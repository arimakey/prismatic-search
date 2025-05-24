import os
import csv

def save_data_to_file(project_name, filename, data):
    projects_dir = os.path.join(os.getcwd(), 'projects')
    if not os.path.exists(projects_dir):
        os.makedirs(projects_dir)
    project_dir = os.path.join(projects_dir, project_name)
    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
    filepath = os.path.join(project_dir, filename)
    with open(filepath, "w", encoding='utf-8') as f:
        f.write(data)


def read_data_from_file(project_name, filename):
    projects_dir = os.path.join(os.getcwd(), 'projects')
    project_dir = os.path.join(projects_dir, project_name)
    filepath = os.path.join(project_dir, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File {filename} not found in project {project_name}.")
    with open(filepath, "r", encoding='utf-8') as f:
        return f.read()


def save_csv(project_name, file_name, articles):
    if not articles:
        print(f"Warning: No articles to save for {file_name}")
        return
        
    projects_dir = os.path.join(os.getcwd(), 'projects')
    if not os.path.exists(projects_dir):
        os.makedirs(projects_dir)
    project_dir = os.path.join(projects_dir, project_name)
    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
    filepath = os.path.join(project_dir, file_name + ".csv")
    with open(filepath, "w", encoding='utf-8', newline="") as file:
        writer = csv.DictWriter(file, fieldnames=articles[0].keys())
        writer.writeheader()
        writer.writerows(articles)
