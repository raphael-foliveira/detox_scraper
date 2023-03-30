import asyncio
import json
from time import sleep
import os
from typing import TypedDict

import requests
from playwright.sync_api import (
    Page,
    sync_playwright,
    TimeoutError,
)


class RecipeInfo(TypedDict):
    type: str
    title: str
    description: str
    image_url: str
    card_html: str


def handle_modal(page: Page) -> None:
    modal_button = page.query_selector("ion-grid button")
    if modal_button is None:
        print("no modal detected")
        page.keyboard.press("Escape")
        return
    print("modal detected")
    page.keyboard.press("Escape")
    return


def click_back_button(page: Page, tries=0) -> None:
    try:
        back_button = page.locator("button.back-button").all()[-1]
        if back_button is None or not back_button.is_visible():
            print("back button not visible. returning...")
            page.keyboard.press("Escape")
            return
        back_button.click(timeout=1000)
        print("back button clicked")
    except Exception as e:
        print(e)
        page.keyboard.press("Escape")
        if tries > 3:
            return
        click_back_button(page, tries + 1)


def save_image(recipe: RecipeInfo):
    response = requests.get(recipe["image_url"])
    directory_path = f"./images/{recipe['type']}/{recipe['title']}/"
    os.makedirs(
        directory_path,
        exist_ok=True,
    )
    print("directory created")
    with open(f"{directory_path}/image.png", "wb") as f:
        print("saving image to:", directory_path)
        f.write(response.content)

    with open(f"{directory_path}/info.json", "w") as f:
        print("saving info to:", directory_path)
        json.dump(recipe, f)


def get_recipe_info(page: Page, recipe_type: str) -> RecipeInfo | None:
    card_handle = page.wait_for_selector("div.card", timeout=2000)
    if card_handle is None:
        print("no card detected")
        return None

    recipe_html = page.locator("div.card").inner_html()
    title = page.locator("div.card ion-card-title").inner_text()
    description = page.locator("div.card div.description-wrapper").inner_text()
    image_url = page.locator("div.card img").get_attribute("src")
    assert image_url is not None

    print("recipe title:", title)
    recipe = RecipeInfo(
        title=title,
        description=description,
        card_html=recipe_html,
        type=recipe_type,
        image_url=image_url,
    )
    save_image(recipe)
    return recipe


def get_recipes_from_recipes_list(page: Page) -> list[RecipeInfo]:
    sleep(2)
    recipes = []

    recipe_elements = page.locator(
        "page-moblets-list:nth-child(3) > ion-content > div.scroll-content > ion-list > button"
    ).all()
    print("recipe_elements:")
    print(recipe_elements)

    recipes_type = page.locator("div.toolbar-title").all()[-1].inner_text()
    recipe = None
    for recipe in recipe_elements:
        try:
            recipe.click()
            recipe = get_recipe_info(page, recipes_type.strip())
            recipes.append(recipe)
        except Exception as e:
            print("error:", e)
        finally:
            if recipe is not None:
                click_back_button(page)
    return recipes


def get_recipes() -> None:
    recipe_type_list_selector = "div.flat"

    with sync_playwright() as playwright:
        recipes: list[RecipeInfo] = []
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_default_timeout(5000)
        page.goto(
            "https://pwa.fabricadeaplicativos.com.br/protocolo_detox#/group/23357695",
            timeout=30000,
        )

        page.wait_for_selector(recipe_type_list_selector, timeout=10000)
        recipe_type_list = page.locator(recipe_type_list_selector).all()
        print("recipe_type_list:")
        print(recipe_type_list)
        curr_url = ""

        for rt in recipe_type_list:
            print("getting recipe list for type:", rt.inner_text().strip())
            try:
                rt.click()
                print("clicked recipe type:", rt.inner_text().strip())
                recipes = get_recipes_from_recipes_list(page)
                print("got recipes")
            except Exception as e:
                print("error:", e)
                rt.click()
            finally:
                if len(recipes) > 0:
                    click_back_button(page)
