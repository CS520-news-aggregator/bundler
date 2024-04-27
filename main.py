from contextlib import asynccontextmanager
import os
from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from models.utils.funcs import subscribe_to_publisher
from routers.subscriber import subscriber_router
import sys


@asynccontextmanager
async def lifespan(_: FastAPI):
    subscribe_to_publisher(
        os.getenv("SUBSCRIBER_IP", "localhost"),
        8020,
        os.getenv("PUBLISHER_IP", "localhost"),
        8010,
    )
    yield


origins = ["*"]
app = FastAPI(title="News Annotator", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(subscriber_router)


@app.get("/")
async def root():
    return {"Hello": "World"}


def train_bert():
    from bundle.models.bert.data.social_animal_driver import (
        get_social_news_data,
    )
    from bundle.models.bert.train import create_model, save_model, load_model
    from bundle.models.bert.constants import FILE_DIR
    from bertopic import BERTopic

    prev_topic_model = load_model(
        os.path.join(os.path.join(FILE_DIR, "saved_models"), "bert_model_all_news.bin")
    )

    list_documents = get_social_news_data()
    cur_topic_model = create_model(list_documents)

    topic_model = BERTopic.merge_models([prev_topic_model, cur_topic_model])
    save_model(topic_model)


def debug():
    from routers.subscriber import process_sources

    process_sources(
        [
            "22822f8d-2a6c-4706-91cf-77727a812497",
            "5c035810-ac1c-437d-b685-854154daedb4",
            "3409c980-04b5-4077-8121-94660e1b0dce",
            "a51b2f74-296c-4b19-957f-d354fb96522e",
            "7e9fcc63-d1b6-47b7-a8c3-2bb4579346c5",
            "63eacb14-67bd-4d2a-bf61-870ebecec788",
            "a5a257f0-23a8-48a3-b8d1-b12d03a01493",
            "0c723c45-584d-4f59-a7df-05b3088d7a80",
            "61eb20d5-4ab2-4985-ab8f-1852bd0f8480",
            "ec2e4414-6b53-4604-816a-663745de3473",
        ]
    )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        debug()
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=8020, reload=True, workers=1)
