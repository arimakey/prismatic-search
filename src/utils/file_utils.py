import os

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
