import os

DB_HOST = os.getenv("DB_HOST", "localhost")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost")
SCRAPER_HOST = os.getenv("SCRAPER_HOST", "localhost")
RECOMMENDER_HOST = os.getenv("RECOMMENDER_HOST", "localhost")
LLM_HOST = os.getenv("LLM_HOST", "localhost")
