from dotenv import load_dotenv
from rich.console import Console
from core import api
from rich.table import Table
from utils.file_utils import save_data_to_file
from utils.console_formatter import print_formatted_text

load_dotenv()
console = Console()

def generate_query(title, context, project_name):
    while True:
        # Build the message to have the AI generate an English search query.
        conversation = [
            {
            "role": "system",
            "content": (
                "Generate a search query by combining the title and the context. "
                "Use strategic parentheses with boolean operators for enhanced flexibility. "
                "Include synonyms, abbreviations, and truncation where possible. "
                "Example format: (\"M2M\" OR \"machine-to-machine\") AND (\"cost*\" OR \"efficien*\") AND "
                "(\"supply chain*\" OR \"logistics\" OR \"inventory management\"). "
                "Ensure that the query is generated in a single line without additional explanations."
            )
            },
            {
            "role": "user",
            "content": f"Title: {title['en']}\\nContext: {context}"
            }
        ]
        query = api.get_completion(conversation)

        # Display the generated query in a table
        table = Table(title="Generated Query")
        table.add_column("Query", style="cyan")
        table.add_row(query)
        console.print("\\n")
        console.print(table)

        # Ask the user if the query is liked
        confirm = input("Do you like the query? (yes/no): ").strip().lower()
        if confirm == "yes":
            save_data_to_file(project_name, "query.txt", query)
            return query
        elif confirm != "no":
            print_formatted_text("[bold yellow]Invalid input. Please type 'yes' or 'no'.[/bold yellow]")
