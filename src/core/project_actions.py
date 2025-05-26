from core.get_title import generate_title
from core.get_query import generate_query
from core.article_criteria import generate_criteria
from core.refine import refine_topic_interactive
from search_engines.counter import counter
from utils.project_helper import (
    save_project_data,
    load_project_data,
    display_project_data
)

def handle_new_project_creation(console, questionary):
    """
    Handles the entire workflow for creating a new project.
    """
    project_name = questionary.text("Enter the new project name:").ask()
    if not project_name:
        console.print("[red]Project name cannot be empty. Exiting.[/red]")
        return None, None, 0, 0

    console.print(f"[green]Creating new project:[/green] {project_name}\n")

    # 1) Contexto / tema
    context = questionary.text("¿De qué tema te gustaría hacer tu revisión sistemática? ").ask()
    if not context:
        console.print("[red]Context cannot be empty. Exiting.[/red]")
        return None, None, 0, 0
    console.print(f"[green]Tema seleccionado:[/green] {context}\n")

    # 2) Generar título
    title = generate_title(context)

    # Variables para el bucle
    search_query = ""
    google_count = 0
    scopus_count = 0

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

            if decision is None: # User cancelled
                console.print("[yellow]Operation cancelled by user during refinement.[/yellow]")
                return None, None, 0, 0
            elif decision == "Volver a generar el título":
                title = generate_title(context)
            elif decision == "Solo volver a generar la query":
                continue
            elif decision == "Refinar manualmente el tema":
                context = refine_topic_interactive(context)
                if context is None: # User cancelled during refinement
                    console.print("[yellow]Operation cancelled by user during topic refinement.[/yellow]")
                    return None, None, 0, 0
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

    return project_name, search_query, google_count, scopus_count


def handle_load_existing_project(project_name_to_load, console):
    """
    Handles the workflow for loading an existing project.
    """
    console.print(f"[green]Loading existing project:[/green] {project_name_to_load}\n")
    general_data = load_project_data(project_name_to_load)

    if not general_data:
        console.print(f"[red]Error: Could not load data for project '{project_name_to_load}'.[/red]")
        return None, None, 0, 0

    # —— Inicializar todas las variables desde el JSON guardado ——
    context       = general_data.get("context", "")
    title         = general_data.get("title", {}) # Mantener como dict o string según esté guardado
    search_query  = general_data.get("search_query", "")
    counts        = general_data.get("search_number", {})
    google_count  = counts.get("google_scholar", 0)
    scopus_count  = counts.get("scopus", 0)
    # -----------------------------------------------------------

    display_project_data(general_data, console)

    return project_name_to_load, search_query, google_count, scopus_count
