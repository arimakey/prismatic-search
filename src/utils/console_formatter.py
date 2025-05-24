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
