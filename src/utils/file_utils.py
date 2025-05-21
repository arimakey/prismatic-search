import time
import json

def save_results(topic, structure, search_queries, work_plan):
    """Guarda los resultados en un archivo JSON y de texto."""
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    
    # Crear diccionario con resultados
    results = {
        "topic": topic,
        "structure": structure,
        "search_queries": search_queries,
        "work_plan": work_plan,
        "timestamp": timestamp
    }
    
    # Guardar como JSON
    json_filename = f"revision_sistematica_{timestamp}.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    # Guardar como texto para fácil lectura
    txt_filename = f"revision_sistematica_{timestamp}.txt"
    with open(txt_filename, "w", encoding="utf-8") as f:
        f.write(f"REVISIÓN SISTEMÁTICA: {topic}\n")
        f.write("=" * 50 + "\n\n")
        f.write("ESTRUCTURA DE LA REVISIÓN:\n")
        f.write("-" * 30 + "\n")
        f.write(structure + "\n\n")
        f.write("CONSULTAS DE BÚSQUEDA OPTIMIZADAS:\n")
        f.write("-" * 30 + "\n")
        f.write(search_queries + "\n\n")
        f.write("PLAN DE TRABAJO:\n")
        f.write("-" * 30 + "\n")
        f.write(work_plan + "\n")
    
    print(f"[bold green]Resultados guardados en {json_filename} y {txt_filename}[/bold green]")
