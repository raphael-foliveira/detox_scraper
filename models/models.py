from typing import TypedDict


class RecipeInfo(TypedDict):
    type: str
    title: str
    description: str
    image_url: str
    card_html: str
