import uuid
from pydantic import BaseModel, Field


class Source(BaseModel):
    id: str = Field(default_factory=uuid.uuid4, alias="_id")
    title: str = "Unknown title"
    link: str = "Unknown link"
    media: str = "Unknown media"
    author: str = "Unknown author"
    date: str = "Unknown date"

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "title": "sample",
                "link": "sample",
                "media": "sample",
                "author": "sample",
                "date": "sample",
            }
        }
