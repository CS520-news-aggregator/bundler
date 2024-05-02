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
    from bundle.collage import make_collage

    link = make_collage(
        [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Taka_Shiba.jpg/1200px-Taka_Shiba.jpg",
            "https://cdn.britannica.com/71/234471-050-093F4211/shiba-inu-dog-in-the-snow.jpg",
            "https://www.akc.org/wp-content/uploads/2017/11/Shiba-Inu-standing-in-profile-outdoors.jpg",
            "https://www.akc.org/wp-content/uploads/2017/11/Shiba-Inu-puppy-standing-outdoors.jpg",
        ]
    )

    print(link)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        debug()
    else:
        uvicorn.run("main:app", host="0.0.0.0", port=8020, reload=True, workers=1)
