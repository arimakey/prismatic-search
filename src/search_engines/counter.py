from search_engines.fast_google_search import count_google_scholar_articles_simple
from search_engines.fast_scopus_search import count_scopus_articles_simple
from utils.console_formatter import print_table

def counter(search_query):
    google_count = count_google_scholar_articles_simple(search_query)
    scopus_count = count_scopus_articles_simple(search_query)
    # print(google_count, scopus_count)
    data = [
        ["Search Engine", "Count"],
        ["Google Scholar", str(google_count)],
        ["Scopus", str(scopus_count)]
    ]
    
    print_table(data)
    return google_count, scopus_count