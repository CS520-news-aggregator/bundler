from typing import List
from fastapi import APIRouter, Body, Request, BackgroundTasks
from tqdm import tqdm
from models.llm import PostAnalysis, PostQuery
from models.utils.constants import DB_HOST, LLM_HOST, SCRAPER_HOST, RECOMMENDER_HOST
from models.pub_sub import AggregatorMessage
from models.utils.funcs import add_data_to_api, get_data_from_api, Response
from models.post import Post
from models.source import Source
from models.scraper import ScrapeQuery, ScrapeData
from models.recommendation import RecommendationQuery
from bundle.clustering import cluster_by_topic


subscriber_router = APIRouter(prefix="/subscriber")
MODEL_NAME = "bert"


@subscriber_router.post("/update")
async def update_from_publisher(
    _: Request,
    background_tasks: BackgroundTasks,
    message: AggregatorMessage = Body(...),
):
    print(f"Received message: {message}")
    add_background_task(background_tasks, message.source_ids)
    return {"message": "Annotations in progress"}


def add_background_task(background_tasks: BackgroundTasks, list_source_ids: list[str]):
    background_tasks.add_task(process_sources, list_source_ids)


def process_sources(list_source_ids: list[str]):
    if not list_source_ids:
        print("No sources to process")
        return

    documents: List[str] = []
    sources: List[Source] = []

    # FIXME: extract parts of this code into a function
    for source_id in tqdm(list_source_ids, desc="Processing sources"):
        source_data = get_data_from_api(
            DB_HOST, "aggregator/get-aggregation", {"source_id": source_id}
        )

        source = Source(**source_data["source"])
        sources.append(source)
        scrape_query = ScrapeQuery(source_id=source_id, link=source.link)

        if scraped_json := get_data_from_api(
            SCRAPER_HOST, "scraper/get-scrape-data", scrape_query
        ):
            scrape_data = ScrapeData(**scraped_json["scrape_data"])
            documents.append(scrape_data.content)

    print("Clustering sources")

    cluster_topics, idx_to_topic = cluster_by_topic(
        MODEL_NAME, documents, num_clusters=len(list_source_ids)
    )

    list_post_queries: List[PostQuery] = []

    for cluster_idx, list_sources in cluster_topics.items():
        cluster_source_ids = []

        for source_idx in list_sources:
            source_id = list_source_ids[source_idx]
            cluster_source_ids.append(source_id)

        post = Post(
            source_ids=cluster_source_ids,
            topics=idx_to_topic[cluster_idx],
            date=sources[0].date,  # FIXME: for now, put the date of the first source
        )

        if add_data_to_api("annotator/add-post", post) != Response.FAILURE:
            cur_documents = [documents[source_idx] for source_idx in list_sources]
            text_content = "\n ".join(cur_documents)
            list_post_queries.append(PostQuery(post_id=str(post.id), text=text_content))

    if list_post_queries:
        llm_post_analysis = PostAnalysis(post_queries=list_post_queries)
        add_data_to_api(LLM_HOST, "llm/add-analysis", llm_post_analysis)

        recommender_query = RecommendationQuery(
            post_ids=[post.id for post in list_post_queries]
        )
        add_data_to_api(
            RECOMMENDER_HOST, "recommender/add-recommendations", recommender_query
        )
