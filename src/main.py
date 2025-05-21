from core.delimit_topic_context import delimit_topic_context
from core.get_title import generate_title
from core.article_criteria import generate_criteria
from core.get_query import generate_query

if __name__ == "__main__":
    context = delimit_topic_context()
    title = generate_title(context)
    search_query = generate_query(title, context)
    criteria = generate_criteria(title, context)
