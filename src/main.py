from core.delimit_topic_context import delimit_topic_context
from core.get_title import generate_title
from core.get_query import generate_query
from core.article_criteria import generate_criteria
from core.search_engines.google_search import count_google_scholar_articles_simple
from core.search_engines.scopus_search import count_scopus_articles_simple
from core import fast_search

def main(project_name):
    # context = delimit_topic_context()
    context = """ Esta revisión sistemática explora el impacto de la comunicación máquina a máquina (M2M) en las cadenas de suministro, centrándose en su influencia en la eficiencia operativa, la visibilidad en tiempo real, la
                    reducción de costos y la sostenibilidad. Se analizan las aplicaciones clave de M2M en logística, gestión de inventarios y trazabilidad, evaluando cómo su implementación optimiza procesos, mejora la toma de
                    decisiones y reduce errores humanos. Además, se discuten los desafíos técnicos y organizacionales asociados con su adopción.

                    [INFORMACIÓN SUFICIENTE]"""

    # title = generate_title(context, project_name)
    title = "Revisión sistemática sobre : evidencia actual y perspectivas futuras"

    # search_query = generate_query(title, context, project_name)
    search_query = """ 
( "cybersecurity" OR "cyber security" OR "computer security" OR "information security" ) AND ( "security incident response" OR "cybersecurity incident" OR "cyber incident management" OR "security incident handling" OR "dfir" ) AND ( "automation" OR "frameworks" ) AND ( "startup" OR "tech startup" OR "startups" )"""

    from core.entry_search import combined_search
    combined_search(search_query)


    # total_scopus = fast_search.count_scopus_articles(search_query, criteria, project_name)

    # print(f"Google Académico: {total_google} artículos encontrados.")
    # print(f"Scopus: {total_scopus} artículos encontrados.")

if __name__ == "__main__":
    project_name = input("Enter the project name: ")
    main(project_name)