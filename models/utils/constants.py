import os

DB_HOST = os.getenv("DB_HOST", "localhost") + ":8000"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "localhost") + ":11434"
SCRAPER_HOST = os.getenv("SCRAPER_HOST", "localhost") + ":8050"
RECOMMENDER_HOST = os.getenv("RECOMMENDER_HOST", "localhost") + ":8030"
LLM_HOST = os.getenv("LLM_HOST", "localhost") + ":8040"
