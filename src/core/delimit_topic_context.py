from rich.console import Console
from agents import api
import re

console = Console()

def delimit_topic_context():
    console.print("[bold blue]Iniciando el proceso para generar contexto (PRISMA)...[/bold blue]")

    # Solicitar el tema de la revisión
    topic = input("¿De qué tema te gustaría hacer tu revisión sistemática? ")
    console.print(f"[green]Tema seleccionado:[/green] {topic}\n")

    # Configurar diálogo iterativo donde la IA decide cuándo parar
    conversation = [
        {
            "role": "system",
            "content": (
                "Eres un asistente experto en revisiones sistemáticas que utiliza el método PRISMA. "
                "Tu tarea es generar un contexto descriptivo lógico para la revisión. "
                "Realiza preguntas de refinamiento una a la vez. "
                "Cuando consideres que tienes suficiente información para crear un contexto coherente, termina tu mensaje con '[INFORMACIÓN SUFICIENTE]' seguido únicamente del contexto completo generado. "
                "No solicites al usuario que indique fin de información ni propongas ningún título."
                "No incluyas fechas, autores ni detalles específicos de artículos. "
                "El contexto debe ser claro y conciso, evitando ambigüedades. "
                "Si el usuario no responde a tus preguntas, dalo por terminado y genera el contexto con la información que tienes. "
                "No incluyas detalles innecesarios ni repitas información. "
            )
        },
        {"role": "user", "content": f"Quiero hacer una revisión sistemática sobre: {topic}."}
    ]

    console.print("[bold yellow]Comenzamos el refinamiento iterativo...[/bold yellow]")
    context_generated = ""

    while True:
        # La IA hace una pregunta o devuelve el contexto final
        assistant_msg = api.get_completion(conversation)
        console.print(f"[bold cyan]Asistente:[/bold cyan] {assistant_msg}\n")

        # Limpiar posibles asteriscos y espacios
        cleaned = re.sub(r"\*+", "", assistant_msg).strip()

        # Si la IA marca que ya tiene suficiente información, extraer contexto
        if '[INFORMACIÓN SUFICIENTE]' in cleaned:
            parts = cleaned.split('[INFORMACIÓN SUFICIENTE]', 1)
            context_generated = parts[1].strip()
            break

        # Si no, recoger respuesta del usuario y continuar
        user_response = input("Tu respuesta: ")
        conversation.append({"role": "user", "content": user_response})

    console.print("[bold green]\nContexto generado:[/bold green]")
    console.print(context_generated)
    
    context = """Esta revisión sistemática explora el impacto de la comunicación máquina a máquina (M2M) en las cadenas de suministro, centrándose en su influencia en la eficiencia operativa, la visibilidad en tiempo real, la
                reducción de costos y la sostenibilidad. Se analizan las aplicaciones clave de M2M en logística, gestión de inventarios y trazabilidad, evaluando cómo su implementación optimiza procesos, mejora la toma de
                decisiones y reduce errores humanos. Además, se discuten los desafíos técnicos y organizacionales asociados con su adopción."""
    
    console.print(context)
    return context_generated
