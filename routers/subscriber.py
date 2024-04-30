from typing import List
from fastapi import APIRouter, Body, Request, BackgroundTasks
from tqdm import tqdm
from models.llm import PostAnalysis, PostQuery, PostsAnalysisQuery
from models.utils.constants import DB_HOST, LLM_HOST, SCRAPER_HOST, RECOMMENDER_HOST
from models.pub_sub import AggregatorMessage
from models.utils.funcs import add_data_to_api, get_data_from_api, Response
from models.post import Post
from models.source import Source
from models.scraper import ScrapeQuery, ScrapeData
from models.recommendation import RecommendationQuery
from bundle.clustering import cluster_by_topic
from datetime import datetime
import requests
from PIL import Image
from io import BytesIO
from urllib.parse import unquote


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
        if (
            source_data := get_data_from_api(
                DB_HOST, "aggregator/get-aggregation", {"source_id": source_id}
            )
        ) != Response.FAILURE:
            source = Source(**source_data["source"])
            scrape_query = ScrapeQuery(source_id=source_id, link=source.link)

            if (
                scraped_json := get_data_from_api(
                    SCRAPER_HOST, "scraper/get-scrape-data", scrape_query
                )
            ) != Response.FAILURE:
                scrape_data = ScrapeData(**scraped_json)
                documents.append(scrape_data.content)
                sources.append(source)

    if documents:
        print("Clustering sources")

        cluster_topics, idx_to_topic = cluster_by_topic(
            MODEL_NAME, documents, num_clusters=len(sources)
        )

        list_post_queries: List[PostQuery] = []

        for cluster_idx, list_sources in cluster_topics.items():
            cluster_sources: List[Source] = []

            for source_idx in list_sources:
                source = sources[source_idx]
                cluster_sources.append(source)
#-----------------Collage Creation---------------------------------------------------------------
            links = []
            index=0;
            while len(links) != 4:
                if cluster_sources[index].media != "[Removed]":
                    links.append(cluster_sources[index].media)
            links = [unquote(link) for link in links]
            collage = Image.new("RGBA", (500,500), color = (255,255,255,255))
            responses = [requests.get(image_link) for image_link in links]
            photos = [Image.open(BytesIO(response.content)).convert("RGBA") for response in responses]
            photos = [photos.resize((250,250)) for photos in photos]
            index = 0
            for i in range(0,500,250):
                for j in range(0,500,250):
                    if(index < len(photos)):
                        collage.paste(photos[index], (i,j))
                        index+=1
                    else:
                        break

#-----------------Collage Creation--------------------------------------------------------------
            post = Post(
                source_ids=[source.id for source in cluster_sources],
                topics=idx_to_topic[cluster_idx],
                date=get_min_date([source.date for source in cluster_sources]),
                media=collage,
            )

            if add_data_to_api(DB_HOST, "annotator/add-post", post) != Response.FAILURE:
                cur_documents = [documents[source_idx] for source_idx in list_sources]
                text_content = "\n ".join(cur_documents)
                list_post_queries.append(
                    PostQuery(post_id=str(post.id), text=text_content)
                )

        if list_post_queries:
            llm_post_analysis = PostsAnalysisQuery(post_queries=list_post_queries)
            add_data_to_api(LLM_HOST, "llm/add-analysis", llm_post_analysis)

            recommender_query = RecommendationQuery(
                post_ids=[post_query.post_id for post_query in list_post_queries]
            )
            add_data_to_api(
                RECOMMENDER_HOST, "recommender/add-recommendations", recommender_query
            )


def get_min_date(list_dates: List[str]) -> str:
    DT_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    list_dt = [datetime.strptime(date, DT_FORMAT) for date in list_dates if date]
    return min(list_dt).strftime(DT_FORMAT)
