from dotenv import load_dotenv
from rich.console import Console
from agents import api
from rich.table import Table

load_dotenv()
console = Console()

def generate_query(title, context):
        conversation = [
            {
                "role": "system",
                "content": (
                    "You are an expert in constructing database search strategies.  \n"
                    "Combine the provided title and context into a single-line Boolean query.  \n"
                    "– Use only full words and Boolean operators (AND, OR, NOT) for logical grouping.  \n"
                    "– Do not use symbols like asterisks (*), greater than (>) or less than (<).  \n"
                    "– Use synonyms and related terms in logical groupings.  \n"
                    "– Follow this example style: (\"M2M\" OR \"machine to machine\") AND (\"cost\" OR \"efficiency\") AND (\"supply chain\" OR \"logistics\" OR \"inventory management\").  \n"
                    "Output only the one-line query, without any extra commentary."
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

        return query
