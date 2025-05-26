from rich.console import Console
import questionary

from utils.project_helper import list_existing_projects # Still needed here
from search_engines.downloader import downloader # Still needed here
# Import the new flow functions
from core.project_actions import handle_new_project_creation, handle_load_existing_project

console = Console()

def main():
    existing_projects = list_existing_projects()
    choices = ["Create New Project"] + existing_projects

    action = questionary.select(
        "What would you like to do?",
        choices=choices
    ).ask()

    if action is None:
        console.print("[yellow]Operation cancelled by user.[/yellow]")
        return

    project_name = None
    search_query = None
    google_count = 0
    scopus_count = 0 # scopus_count is not directly used by downloader, but kept for consistency from project_actions

    if action == "Create New Project":
        project_name, search_query, google_count, scopus_count = handle_new_project_creation(console, questionary)
    elif action in existing_projects:
        project_name_to_load = action
        project_name, search_query, google_count, scopus_count = handle_load_existing_project(project_name_to_load, console)
    else:
        console.print("[red]Invalid selection. Exiting.[/red]")
        return

    if not project_name: # If creation or loading failed and returned None for project_name
        console.print("[red]Project operation failed or was cancelled. Exiting.[/red]")
        return

    # Finalmente, si tenemos query y nombre de proyecto, lanzamos el downloader
    if search_query and project_name:
        console.print(f"\n[bold blue]Proceeding to download articles for project '{project_name}'...[/bold blue]")
        downloader(search_query, project_name, quantity_google=google_count)
    else:
        console.print("[yellow]Skipping downloader as search query or project name is missing.[/yellow]")

if __name__ == "__main__":
    main()
