import os
import json
from typing import List, Dict, Optional
from rich.console import Console
from rich.table import Table

PROJECTS_DIR = "projects"

def list_existing_projects() -> List[str]:
    """
    Scans the projects directory and returns a list of valid project names.
    A valid project has a 'general_data.json' file.
    """
    existing_projects = []
    if not os.path.exists(PROJECTS_DIR):
        return existing_projects
    
    for item in os.listdir(PROJECTS_DIR):
        project_path = os.path.join(PROJECTS_DIR, item)
        if os.path.isdir(project_path):
            if os.path.exists(os.path.join(project_path, "general_data.json")):
                existing_projects.append(item)
    return existing_projects

def load_project_data(project_name: str) -> Optional[Dict]:
    """
    Loads general_data.json for a given project.
    Returns the data as a dictionary or None if not found/invalid.
    """
    json_file_path = os.path.join(PROJECTS_DIR, project_name, "general_data.json")
    if not os.path.exists(json_file_path):
        return None
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        return None
    except Exception:
        return None

def save_project_data(project_name: str, data: Dict) -> str:
    """
    Saves the provided data dictionary to general_data.json in the project's directory.
    Returns the path to the saved file.
    """
    project_dir = os.path.join(PROJECTS_DIR, project_name)
    os.makedirs(project_dir, exist_ok=True)
    
    json_file_path = os.path.join(project_dir, "general_data.json")
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return json_file_path

def display_project_data(data: Dict, console: Console):
    """
    Displays project data in a Rich table.
    """
    if not data:
        console.print("[red]No data to display.[/red]")
        return

    table = Table(title="Project General Data")
    table.add_column("Attribute", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    title_data = data.get("title", "N/A")
    if isinstance(title_data, dict):
        table.add_row("Title (en)", str(title_data.get('en', 'N/A')))
        table.add_row("Title (es)", str(title_data.get('es', 'N/A')))
    else:
        table.add_row("Title", str(title_data))
        
    table.add_row("Context", str(data.get("context", "N/A")))
    
    search_number = data.get("search_number", {})
    table.add_row("Google Scholar Results", str(search_number.get("google_scholar", "N/A")))
    table.add_row("Scopus Results", str(search_number.get("scopus", "N/A")))
    
    table.add_row("Project Name", str(data.get("project_name", "N/A")))
    table.add_row("Search Query", str(data.get("search_query", "N/A")))

    article_criteria = data.get("article_criteria")
    if article_criteria:
        table.add_row("Article Criteria", "Stored in JSON (see details below)")
        # Optionally, display a summary or key parts of criteria if needed
        # For now, just indicating it's stored.
    else:
        table.add_row("Article Criteria", "Not generated yet or not found")
        
    console.print(table)

    if article_criteria:
        console.print("\n[bold yellow]Article Criteria Details:[/bold yellow]")
        criteria_table = Table(title="Article Criteria Summary")
        criteria_table.add_column("Criteria Key", style="cyan")
        criteria_table.add_column("Value Summary", style="magenta")
        
        criteria_table.add_row("Population", str(article_criteria.get("población", "N/A")))
        criteria_table.add_row("Study Types", ", ".join(article_criteria.get("tipos_estudio", [])))
        criteria_table.add_row("Year Range", f"{article_criteria.get('año_minimo', 'N/A')} - {article_criteria.get('año_maximo', 'N/A')}")
        criteria_table.add_row("Languages", ", ".join(article_criteria.get("idiomas", [])))
        
        # Displaying parsed criteria sections if available
        parsed = article_criteria.get("criterios_parseados", {})
        criteria_table.add_row("Inclusion Criteria", f"{len(parsed.get('inclusión', '').splitlines())} lines" if parsed.get('inclusión') else "N/A")
        criteria_table.add_row("Exclusion Criteria", f"{len(parsed.get('exclusión', '').splitlines())} lines" if parsed.get('exclusión') else "N/A")
        criteria_table.add_row("Methodological Filters", f"{len(parsed.get('filtros', '').splitlines())} lines" if parsed.get('filtros') else "N/A")
        
        console.print(criteria_table)
