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
                "You are an expert in designing precise search strategies for academic databases. "
                "Generate a concise one-line boolean search query in English that combines the core concepts from the title and context. "
                "Use only the boolean operators AND, OR, and parentheses '(' and ')' for logical grouping. "
                "Avoid using NOT, asterisks (*), symbols like > or <, or any truncation. "
                "Favor specificity: prefer AND over OR to narrow the scope and reduce irrelevant results. "
                "Use only complete, meaningful words with no extra punctuation or modifiers. "
                "Phrases containing more than one word must be enclosed in double quotes. "
                "The goal is to produce a focused and high-precision query. "
                "Output only the final query on a single line with no explanations or extra text."
                "Make the query granular, preferably word by word connected"
                "Query only in English, do not translate it to Spanish. "
            )

        },
        {
            "role": "user",
            "content": f"Title: {title['en']}\nContext: {context}"
        }
    ]
    query = api.get_completion(conversation, model="deepseek-reasoner")

    # Display the generated query in a table
    table = Table(title="Generated Query")
    table.add_column("Query", style="cyan")
    table.add_row(query)
    console.print("\n")
    console.print(table)

    return query
