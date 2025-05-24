from core.delimit_topic_context import delimit_topic_context
from core.get_title import generate_title
from core.get_query import generate_query
from core.article_criteria import generate_criteria
from core.refine import refine_topic_interactive
from search_engines.counter import counter
from search_engines.soft_search_google import download_google_scholar_articles
from search_engines.deep_search_scopus import download_scopus_articles
from rich.console import Console

console = Console()

def main(project_name):
    google_count = 1000
    scopus_count = 1000
    
    context = input("¿De qué tema te gustaría hacer tu revisión sistemática? ")
    console.print(f"[green]Tema seleccionado:[/green] {context}\n")

    title = generate_title(context)

    while google_count > 950 or scopus_count > 950:  
        search_query = generate_query(title, context)
        google_count, scopus_count = counter(search_query)
        
        if google_count > 950 or scopus_count > 950:
            context = refine_topic_interactive(context)
            title = generate_title(context)

    # download_google_scholar_articles(search_query, max_results=10, project_name=project_name)
    # download_scopus_articles(search_query, max_results=10, project_name=project_name)

    # generate_criteria(title, context, project_name)

if __name__ == "__main__":
    project_name = input("Enter the project name: ")
    main(project_name)