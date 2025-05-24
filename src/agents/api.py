import os
from openai import OpenAI
from dotenv import load_dotenv
from rich.console import Console
from rich.status import Status

# Cargar variables de entorno
load_dotenv()

# Inicializar el cliente de API
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# Inicializar la consola de Rich
console = Console()

def get_completion(messages):
    """Obtiene la respuesta del modelo."""
    try:
        # Mostrar animación de 'escribiendo...' mientras se espera la respuesta
        with Status("[bold cyan]Escribiendo...[/bold cyan]", spinner="dots", console=console) as status:
            response = client.chat.completions.create(
                model="deepseek-chat", 
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            # Extraer el texto de la respuesta
            response_text = response.choices[0].message.content
        
        # Comprobar si el mensaje contiene la etiqueta pero también hace preguntas
        if "[INFORMACIÓN SUFICIENTE]" in response_text and ("?" in response_text or "¿" in response_text):
            # Si contiene preguntas, quitar la etiqueta para no finalizar el diálogo prematuramente
            response_text = response_text.replace("[INFORMACIÓN SUFICIENTE]", "")
            print("[bold yellow]Nota: El asistente todavía tiene preguntas, continuando el diálogo...[/bold yellow]")
            
        # Añadir la respuesta a la conversación para mantener el contexto
        messages.append({"role": "assistant", "content": response_text})
        return response_text
    except Exception as e:
        print(f"[bold red]Error al comunicarse con la API: {str(e)}[/bold red]")
        return "Lo siento, ha ocurrido un error al procesar tu solicitud."
