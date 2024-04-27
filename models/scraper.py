from pydantic import BaseModel, Field


class ScrapeQuery(BaseModel):
    source_id: str
    link: str


class ScrapeData(BaseModel):
    source_id: str
    content: str
