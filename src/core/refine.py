from rich.console import Console
from rich.markdown import Markdown
from agents import api
import textwrap
import re

console = Console()

def refine_topic_interactive(topic: str) -> str:
    console.print("[bold blue]Starting interactive refinement (PRISMA)...[/bold blue]\n")

    system_message = textwrap.dedent(f"""
        You are an expert assistant in PRISMA systematic reviews.
        Given the following topic: "{topic}", generate up to 4 brief and specific questions
        to clarify the focus of the review, centered on:
        1. Population or target group
        2. Intervention or exposure
        3. Expected outcomes
        Do NOT ask about publication year or study type.
        Keep the questions clear, concise, and limited to a maximum of 4.
    """).strip()

    conversation = [{"role": "system", "content": system_message}]
    conversation.append({"role": "user", "content": "What questions do you need to ask me to clarify this topic?"})

    try:
        assistant_questions = api.get_completion(conversation)
    except Exception as e:
        console.print(f"[bold red]Error generating questions: {e}[/bold red]")
        return ""

    console.print("[bold yellow]Please answer the following questions:[/bold yellow]")
    console.print(Markdown(assistant_questions))

    user_answers = input("\nType your answers (you can use bullet points or a single block of text):\n").strip()

    system_message_final = textwrap.dedent(f"""
        Based on the original topic: "{topic}" and the following user answers:
        "{user_answers}"
        Write a refined and focused context suitable for a PRISMA systematic review.
        Be clear, concise, and focus exclusively on the topic and its scope.
        Do not include titles or references.
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
