from core.delimit_topic_context import delimit_topic_context
from core.get_title import generate_title
from core.get_query import generate_query
from core.article_criteria import generate_criteria
from core.entry_search import combined_search
from core.search_engines.scopus_deep_search import download_scopus_articles
from core.search_engines.google_scholar_deep_search import download_google_scholar_articles
def main(project_name):
    # context = delimit_topic_context()
    context = """ Esta revisión sistemática explora el impacto de la comunicación máquina a máquina (M2M) en las cadenas de suministro, centrándose en su influencia en la eficiencia operativa, la visibilidad en tiempo real, la
                    reducción de costos y la sostenibilidad. Se analizan las aplicaciones clave de M2M en logística, gestión de inventarios y trazabilidad, evaluando cómo su implementación optimiza procesos, mejora la toma de
                    decisiones y reduce errores humanos. Además, se discuten los desafíos técnicos y organizacionales asociados con su adopción.

                    [INFORMACIÓN SUFICIENTE]"""

    # title = generate_title(context, project_name)
    title = "Revisión sistemática sobre : evidencia actual y perspectivas futuras"
    
    search_query = """ ( "cybersecurity" OR "cyber security" OR "computer security" OR "information security" ) AND ( "security incident response" OR "cybersecurity incident" OR "cyber incident management" OR "security incident handling" OR "dfir" ) AND ( "automation" OR "frameworks" ) AND ( "startup" OR "tech startup" OR "startups" )"""
    download_scopus_articles(search_query, max_results=10, project_name=project_name)
    download_google_scholar_articles(search_query, max_results=10, project_name=project_name)

if __name__ == "__main__":
    project_name = input("Enter the project name: ")
    main(project_name)