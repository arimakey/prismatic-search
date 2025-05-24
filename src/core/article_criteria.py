from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich import box
import questionary
from core import api
from utils.file_utils import save_data_to_file
from utils.console_formatter import print_formatted_text

load_dotenv()
console = Console()

def parse_generated_content(content):
    """
    Parsea y formatea el contenido generado eliminando dobles formatos y mejorando la indentación.
    """
    sections = {
        "inclusión": "",
        "exclusión": "",
        "filtros": ""
    }
    current_section = None
    lines = content.split('\n')
    item_number = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Reconoce las secciones según palabras clave.
        if "criterios de inclusión" in line.lower():
            current_section = "inclusión"
            item_number = 0
            continue
        elif "criterios de exclusión" in line.lower():
            current_section = "exclusión"
            item_number = 0
            continue
        elif "filtros metodológicos" in line.lower() or "filtros explícitos" in line.lower():
            current_section = "filtros"
            item_number = 0
            continue

        if current_section in sections:
            # Detectar nuevos puntos numerados o con viñeta
            if line.startswith(("1.", "- ", "•")):
                item_number += 1
                if ":" in line:
                    parts = line.split(":", 1)
                    title_part = parts[0].replace("1.", "").replace("- ", "").replace("•", "").strip()
                    content_part = parts[1].strip()
                    formatted_line = f"{item_number}. [bold magenta]{title_part}[/bold magenta]: {content_part}"
                else:
                    title = line.replace("1.", "").replace("- ", "").replace("•", "").strip()
                    formatted_line = f"{item_number}. [bold magenta]{title}[/bold magenta]"
            # Subelementos secundarios con viñeta
            elif line.startswith(("-", "•")) or line.startswith(("  -", "\\t-")):
                formatted_line = f"   - {line.lstrip('-• ').strip()}"
            else:
                # Continuación o línea sin formato claro
                formatted_line = f"   {line}"

            # Concatenar con salto de línea
            sections[current_section] += "\\n" + formatted_line if sections[current_section] else formatted_line

    return sections

def generate_criteria(title, context_additional, project_name):
    """
    Solicita criterios al usuario y genera criterios estructurados para una revisión sistemática.
    """
    # Seleccionar población de estudio
    population = questionary.select(
        "¿Qué población objetivo desea estudiar?",
        choices=[
            "Adultos (18+ años)",
            "Niños y adolescentes (<18 años)",
            "Ambos (todas las edades)",
            "Poblaciones específicas (se te pedirá especificar)"
        ]
    ).ask()
    
    if population == "Poblaciones específicas (se te pedirá especificar)":
        population_detail = questionary.text("Describa la población específica:").ask().strip()
        population = f"Población específica: {population_detail}"
    
    # Tipos de estudio
    study_types = questionary.checkbox(
        "Seleccione los tipos de estudios que desea incluir:",
        choices=[
            "Ensayos clínicos aleatorizados",
            "Ensayos clínicos no aleatorizados",
            "Estudios observacionales",
            "Estudios de cohorte",
            "Estudios de casos y controles",
            "Estudios transversales",
            "Revisiones sistemáticas",
            "Meta-análisis",
            "Estudios cualitativos"
        ]
    ).ask() or []

    # Rango temporal
    min_year = questionary.text("Año mínimo de publicación (Ej: 2015):").ask().strip() or "Sin restricción"
    max_year = questionary.text("Año máximo de publicación (dejar vacío para presente):").ask().strip() or "Presente"
    
    # Idiomas
    languages = questionary.checkbox(
        "Seleccione los idiomas permitidos:",
        choices=["Inglés", "Español", "Portugués", "Francés", "Alemán", "Italiano", "Otros"]
    ).ask() or []
    if "Otros" in languages:
        languages.remove("Otros")
        other_languages = questionary.text("Especifique otros idiomas (separados por comas):").ask().strip()
        languages.extend([lang.strip() for lang in other_languages.split(",") if lang.strip()])

    # Criterios específicos de exclusión
    exclusion_criteria = questionary.checkbox(
        "Seleccione criterios específicos de exclusión:",
        choices=[
            "Estudios en animales",
            "Estudios in vitro",
            "Artículos sin resumen disponible",
            "Cartas al editor, comentarios y editoriales",
            "Protocolos de estudio sin resultados",
            "Estudios de caso único",
            "Literatura gris"
        ]
    ).ask() or []

    # Enfoque metodológico
    methodological_approach = questionary.checkbox(
        "Requisitos metodológicos importantes:",
        choices=[
            "Accesibilidad de texto completo",
            "Rigor científico verificable",
            "Metodología explícita",
            "Resultados cuantitativos",
            "Resultados cualitativos"
        ]
    ).ask() or []

    # Criterios adicionales
    additional_criteria = questionary.text("Criterios adicionales específicos para esta revisión (opcional):").ask().strip()

    # Construir prompt para la IA
    prompt = (
        f"Título: {title}. "
        f"Población: {population}. "
        f"Tipos de estudio: {', '.join(study_types)}. "
        f"Rango temporal: {min_year} a {max_year}. "
        f"Idiomas: {', '.join(languages)}. "
        f"Tema específico: {title}. "
        f"Criterios de exclusión: {', '.join(exclusion_criteria)}. "
        f"Requisitos metodológicos: {', '.join(methodological_approach)}. "
        f"Criterios adicionales: {additional_criteria}. "
        f"Contexto: {context_additional}."
    )

    conversation = [
        {
            "role": "system",
            "content": (
                "Eres un asistente experto en metodología científica especializado en revisiones sistemáticas. "
                "Genera criterios de inclusión y exclusión estructurados, precisos y académicos para una revisión sistemática "
                "basándote en la información proporcionada. Organiza tu respuesta en exactamente tres secciones con los siguientes títulos:\\n"
                "1. 'Criterios de inclusión'\\n"
                "2. 'Criterios de exclusión'\\n"
                "3. 'Filtros metodológicos'\\n\\n"
                "Para cada sección:\\n"
                "- Enumera puntos principales numerados con títulos en negrita seguidos de dos puntos (ejemplo: '1. [bold magenta]Población[/bold magenta]: Adultos mayores de 65 años')\\n"
                "- Bajo cada punto principal, usa guiones para listar subelementos específicos\\n"
                "- Utiliza un formato consistente y lenguaje académico preciso\\n"
                "- Incluye una nota breve al final que resuma el enfoque metodológico"
            )
        },
        {"role": "user", "content": prompt}
    ]
    
    generated = api.get_completion(conversation)
    
    save_data_to_file(project_name, "criteria.txt", generated)

    # Mostrar resultados en una tabla con estilo mejorado
    table = Table(
        title=f"Criterios para Revisión Sistemática: {title}",
        box=box.ROUNDED,
        border_style="blue",
        header_style="bold yellow",
        expand=True
    )
    table.add_column("Sección", style="cyan", justify="center", no_wrap=True)
    table.add_column("Criterios", style="bright_magenta", justify="left")

    sections = parse_generated_content(generated)
    table.add_row("Criterios de inclusión", sections.get("inclusión", "") or "")
    table.add_row("Criterios de exclusión", sections.get("exclusión", "") or "")
    table.add_row("Filtros metodológicos", sections.get("filtros", "") or "")

    console.width = min(console.width, 120)
    print_formatted_text(table)

    return {
        "titulo": title,
        "población": population,
        "tipos_estudio": study_types,
        "año_mínimo": min_year,
        "año_máximo": max_year,
        "idiomas": languages,
        "tema_específico": title,
        "criterios_exclusión": exclusion_criteria,
        "requisitos_metodológicos": methodological_approach,
        "criterios_adicionales": additional_criteria,
        "criterios_generados": generated
    }
