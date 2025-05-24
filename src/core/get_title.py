from dotenv import load_dotenv
from rich.console import Console
from agents import api
from rich.table import Table
from utils.file_utils import save_data_to_file
from utils.console_formatter import print_formatted_text
import deepl
import os

load_dotenv()
console = Console()

# Inicializar el cliente de DeepL
deepL_translator = deepl.Translator(auth_key=os.getenv("DEEPL_API_KEY"))

def generate_title(context):
    while True:
        # Genera el título en español
        conversation_es = [
            {
                "role": "system",
                "content": (
                    "You are an assistant specialized in crafting concise, highly descriptive titles "
                    "for systematic reviews.  \n"
                    "– Output **only** the title (no explanatory text, no bullet points).  \n"
                    "– Keep it under 20 words.  \n"
                    "– Make sure it clearly reflects the main objective or scope of the review."
                )
            },
            {
                "role": "user",
                "content": context
            }
        ]
        title_es = api.get_completion(conversation_es)

        # Traduce el título al inglés usando DeepL
        try:
            result = deepL_translator.translate_text(title_es, source_lang="ES", target_lang="EN-US")
            title_en = result.text
        except Exception as e:
            console.print(f"\n[bold red]Error al traducir con DeepL: {str(e)}[/bold red]")
            # Fallback a la API de IA si DeepL falla
            conversation_en = [
                {
                    "role": "system",
                    "content": (
                        "You are a professional translator.  \n"
                        "Translate the following Spanish title into fluent, academic‐style English.  \n"
                        "– Output **only** the translated title.  \n"
                        "– Do not add any explanations or annotations."
                    )
                },
                {
                    "role": "user",
                    "content": title_es
                }
            ]
            title_en = api.get_completion(conversation_en)

        # Muestra ambos títulos en una tabla de una sola columna, uno arriba del otro
        table = Table(title="Títulos Generados")
        table.add_column("Título", style="cyan")
        table.add_row(f"[bold cyan]Español:[/bold cyan] {title_es}")
        table.add_row(f"[bold magenta]Inglés:[/bold magenta] {title_en}")
        console.print("\n")
        console.print(table)

        # Pregunta al usuario si le gusta el título
        confirm = input("¿Te gusta el título? (si/no): ").strip().lower()
        if confirm == "si":
            return {"es": title_es, "en": title_en}
        elif confirm != "no":
            print_formatted_text("[bold yellow]Entrada inválida. Por favor, escribe 'si' o 'no'.[/bold yellow]")
