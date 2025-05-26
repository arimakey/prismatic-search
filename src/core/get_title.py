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
        # Genera el título en inglés
        conversation_en = [
            {
                "role": "system",
                "content": (
                    "You are an assistant specialized in creating concise, informative titles for systematic reviews.\n"
                    "- Output only the final title, without any explanations or formatting.\n"
                    "- Limit the title to a maximum of 25 words.\n"
                    "- Ensure the title clearly conveys the main objective, population, intervention, or scope of the review.\n"
                    "- Prioritize clarity and relevance over generality or broad phrasing."
                    "- Give me a title in a single line without any extra formatting.\n"
                    "- Give me a title in English.\n"
                )
            },
            {
                "role": "user",
                "content": context
            }
        ]
        title_en = api.get_completion(conversation_en, model="deepseek-reasoner")

        # Traduce el título al español usando DeepL
        try:
            result = deepL_translator.translate_text(title_en, source_lang="EN", target_lang="ES")
            title_es = result.text
        except Exception as e:
            console.print(f"\n[bold red]Error al traducir con DeepL: {str(e)}[/bold red]")
            # Fallback a la API de IA si DeepL falla
            conversation_es = [
                {
                    "role": "system",
                    "content": (
                        "You are a professional translator.\n"
                        "Translate the following English title into fluent, academic style Spanish.\n"
                        "- Output **only** the translated title.\n"
                        "- Do not add any explanations or annotations."
                        "- Give me the translation in a single line without any extra formatting.\n"
                    )
                },
                {
                    "role": "user",
                    "content": title_en
                }
            ]
            title_es = api.get_completion(conversation_es)

        # Muestra ambos títulos en una tabla de una sola columna, uno arriba del otro
        table = Table(title="Títulos Generados")
        table.add_column("Título", style="cyan")
        table.add_row(f"[bold magenta]Inglés:[/bold magenta] {title_en}")
        table.add_row(f"[bold cyan]Español:[/bold cyan] {title_es}")
        console.print("\n")
        console.print(table)

        # Pregunta al usuario si le gusta el título
        confirm = input("¿Te gusta el título? (si/no): ").strip().lower()
        if confirm == "si":
            return {"en": title_en, "es": title_es}
        elif confirm != "no":
            print_formatted_text("[bold yellow]Entrada inválida. Por favor, escribe 'si' o 'no'.[/bold yellow]")
