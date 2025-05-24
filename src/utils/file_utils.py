import os

def save_data_to_file(project_name, filename, data):
    project_dir = os.path.join(os.getcwd(), project_name)
    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
    filepath = os.path.join(project_dir, filename)
    with open(filepath, "w") as f:
        f.write(data)
