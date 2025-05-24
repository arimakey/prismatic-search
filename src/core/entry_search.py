from rich.console import Console
from rich.table import Table
from core.search_engines.google_search import count_google_scholar_articles_simple
from core.search_engines.scopus_search import count_scopus_articles_simple

def combined_search(search_query: str) -> None:
    """Perform a combined search in Google Scholar and Scopus, displaying results in a table.

    Args:
        search_query (str): The search query to use for both search engines
    """
    console = Console()
    table = Table(title="Search Results")

    table.add_column("Search Engine", style="cyan", no_wrap=True)
    table.add_column("Articles Found", style="magenta")

    # Perform searches
    google_results = count_google_scholar_articles_simple(search_query)
    scopus_results = count_scopus_articles_simple(search_query)

    # Add results to table
    table.add_row("Google Scholar", str(google_results))
    table.add_row("Scopus", str(scopus_results))

    # Display the table
    console.print(table)