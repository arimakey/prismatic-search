from search_engines.soft_search_google import download_google_scholar_articles
from search_engines.deep_search_scopus import download_scopus_articles

def downloader(search_query, project_name, quantity_google=1000, quantity_scopus=1000):
    download_google_scholar_articles(search_query, project_name=project_name, max_results=quantity_google)
    download_scopus_articles(search_query, project_name=project_name)