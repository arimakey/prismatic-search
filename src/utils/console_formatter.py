import re
from rich.console import Console

console = Console()

def format_text(text):
    """
    Formats text with markdown-like syntax for console output using rich.
    """
    text = re.sub(r'\*\*(.*?)\*\*', r'[bold]\1[/bold]', text)
    text = re.sub(r'\*(.*?)\*', r'[italic]\1[/italic]', text)
    text = re.sub(r'__(.*?)__', r'[underline]\1[/underline]', text)
    return text

def print_formatted_text(text):
    """
    Prints formatted text to the console using rich.
    """
    if hasattr(text, '__str__'):
        text = str(text)
    formatted_text = format_text(text)
    console.print(formatted_text)

def print_table(data):
    """
    Prints data in a table format to the console using rich.
    Data should be a list of lists, where the first list is the header.
    """
    from rich.table import Table

    table = Table(title="Search Results")

    if not data:
        console.print("No data to display.")
        return

    # Add columns from the header row
    for header in data[0]:
        table.add_column(header)

    # Add rows from the rest of the data
    for row in data[1:]:
        table.add_row(*row)

    console.print(table)
