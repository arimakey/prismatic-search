from core.get_title import generate_title
from core.get_query import generate_query
from core.article_criteria import generate_criteria
from core.refine import refine_topic_interactive
from search_engines.downloader import downloader
from search_engines.counter import counter

from rich.console import Console
import questionary

from utils.project_helper import (
    list_existing_projects,
    load_project_data,
    save_project_data,
    display_project_data
)

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

    # Variables a inicializar en ambos casos
    project_name = ""
    general_data = {}
    search_query = ""
    title = {}
    context = ""
    google_count = 0
    scopus_count = 0

    if action == "Create New Project":
        project_name = questionary.text("Enter the new project name:").ask()
        if not project_name:
            console.print("[red]Project name cannot be empty. Exiting.[/red]")
            return

        console.print(f"[green]Creating new project:[/green] {project_name}\n")

        # 1) Contexto / tema
        context = input("¿De qué tema te gustaría hacer tu revisión sistemática? ")
        console.print(f"[green]Tema seleccionado:[/green] {context}\n")

        # 2) Generar título
        title = generate_title(context)

        # 3) Loop para query y contador
        while True:
            search_query = generate_query(title, context)
            google_count, scopus_count = counter(search_query)

            if google_count > 960 and scopus_count < 40:
                console.print(f"[yellow]Google Scholar count too high ({google_count}) "
                              f"and Scopus count too low ({scopus_count}).[/yellow]")

                decision = questionary.select(
                    "¿Qué quieres hacer?",
                    choices=[
                        "Volver a generar el título",
                        "Solo volver a generar la query",
                        "Refinar manualmente el tema",
                        "Continuar de todos modos"
                    ]
                ).ask()

                if decision == "Volver a generar el título":
                    title = generate_title(context)
                elif decision == "Solo volver a generar la query":
                    continue
                elif decision == "Refinar manualmente el tema":
                    context = refine_topic_interactive(context)
                    title = generate_title(context)
                elif decision == "Continuar de todos modos":
                    break
            else:
                break

        console.print(f"[green]Final search query generated.[/green]")
        console.print(f"[cyan]Google Scholar results: {google_count}, Scopus results: {scopus_count}[/cyan]")

        # 4) Generar criterios de artículo
        console.print("\n[bold blue]Proceeding to generate article criteria...[/bold blue]")
        title_for_criteria = title.get('en', str(title)) if isinstance(title, dict) else str(title)
        article_criteria_data = generate_criteria(title_for_criteria, context, project_name)

        # 5) Empaquetar y guardar datos
        general_data = {
            "title": title,
            "context": context,
            "search_query": search_query,
            "search_number": {
                "google_scholar": google_count,
                "scopus": scopus_count
            },
            "project_name": project_name,
            "article_criteria": article_criteria_data
        }

        saved_path = save_project_data(project_name, general_data)
        console.print(f"\n[bold green]General data saved to:[/bold green] {saved_path}")
        display_project_data(general_data, console)

    elif action in existing_projects:
        project_name = action
        console.print(f"[green]Loading existing project:[/green] {project_name}\n")
        general_data = load_project_data(project_name)

        if not general_data:
            console.print(f"[red]Error: Could not load data for project '{project_name}'.[/red]")
            return

        # —— Inicializar todas las variables desde el JSON guardado ——
        context       = general_data.get("context", "")
        title         = general_data.get("title", {})
        search_query  = general_data.get("search_query", "")
        counts        = general_data.get("search_number", {})
        google_count  = counts.get("google_scholar", 0)
        scopus_count  = counts.get("scopus", 0)
        # -----------------------------------------------------------

        display_project_data(general_data, console)

    else:
        console.print("[red]Invalid selection. Exiting.[/red]")
        return

    # Finalmente, si tenemos query y nombre de proyecto, lanzamos el downloader
    if search_query and project_name:
        console.print(f"\n[bold blue]Proceeding to download articles for project '{project_name}'...[/bold blue]")
        downloader(search_query, project_name, quantity_google=google_count)
    else:
        console.print("[yellow]Skipping downloader as search query or project name is missing.[/yellow]")

if __name__ == "__main__":
    main()
