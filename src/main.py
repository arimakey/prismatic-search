from core.delimit_topic_context import delimit_topic_context
from core.get_title import generate_title
from core.article_criteria import generate_criteria
from core.get_query import generate_query

from core import fast_search

def main(project_name):
    context = delimit_topic_context()
    title = generate_title(context, project_name)
    search_query = generate_query(title, context, project_name)
    criteria = generate_criteria(title, context, project_name)
    fast_search.count_google_scholar_articles(search_query, project_name = project_name, criteria = criteria)
    fast_search.count_scopus_articles(search_query, api_key = "ddbd21300a00b5f5da2d75c7f33a7cac", project_name = project_name, criteria = criteria)

if __name__ == "__main__":
    project_name = input("Enter the project name: ")
    main(project_name)
