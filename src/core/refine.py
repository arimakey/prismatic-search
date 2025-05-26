from rich.console import Console
from rich.markdown import Markdown
from agents import api
import textwrap
import re

console = Console()

def refine_topic_interactive(topic: str) -> str:
    console.print("[bold blue]Starting interactive refinement (PRISMA)...[/bold blue]\n")

    system_message = textwrap.dedent(f"""
    You are an expert assistant in systematic reviews using the PRISMA methodology.
    Your goal is to help the user clarify the focus of their review topic: "{topic}".

    Generate exactly ONE open-ended question that helps the user reflect on and define the scope of their topic.
    The question should encourage them to consider one of the following aspects:
    - Which population or target group to focus on
    - Which type of intervention, exposure, or technology to consider
    - What kind of outcomes or effects are of most interest

    The question must:
    - Be open and exploratory (avoid assuming details the user hasn’t provided)
    - Be phrased as a genuine inquiry to help define or narrow down the topic
    - Avoid suggesting specific answers

    Do NOT include explanations or extra text — only respond with the single question.
    """).strip()


    conversation = [{"role": "system", "content": system_message}]
    conversation.append({"role": "user", "content": "What question would help clarify this topic?"})

    try:
        assistant_question = api.get_completion(conversation, model="deepseek-reasoner")
    except Exception as e:
        console.print(f"[bold red]Error generating the question: {e}[/bold red]")
        return ""

    console.print("[bold yellow]Please answer the following question:[/bold yellow]")
    console.print(Markdown(assistant_question.strip()))

    user_answer = input("\nYour answer:\n").strip()

    system_message_final = textwrap.dedent(f"""
        Based on the original topic: "{topic}" and the user's answer: "{user_answer}",
        write a refined and focused context suitable for a PRISMA systematic review.
        Be concise, clear, and focused only on the scope and direction of the topic.
        Do not include any titles, lists, or references.
    """)

    conversation_final = [{"role": "system", "content": system_message_final}]
    conversation_final.append({"role": "user", "content": "Please generate the refined context."})

    try:
        refined_context = api.get_completion(conversation_final)
    except Exception as e:
        console.print(f"[bold red]Error generating refined context: {e}[/bold red]")
        return ""

    refined_context = re.sub(r"\*+", "", refined_context).strip()

    console.print("[bold green]\nRefined context:[/bold green]")
    console.print(refined_context)

    return refined_context
