import json
from time import sleep
import os

import requests
from playwright.sync_api import Page, sync_playwright, Locator
from models import RecipeInfo


def __click_back_button(page: Page, tries=0) -> None:
    try:
        back_button = page.locator("button.back-button").all()[-1]
        if back_button is None or not back_button.is_visible():
            print("back button not visible. clicking fallback  and returning...")
            page.keyboard.press("Escape")
            return
        back_button.click(timeout=1000)
        print("back button clicked")
    except Exception as e:
        print(e)
        page.keyboard.press("Escape")
        if tries > 3:
            return
        __click_back_button(page, tries + 1)


def __save_image(recipe: RecipeInfo):
    response = requests.get(recipe["image_url"])
    directory_path = f"./images/{recipe['type']}/{recipe['title']}/".lower()
    os.makedirs(
        directory_path.lower(),
        exist_ok=True,
    )
    print("directory created")
    with open(f"{directory_path}/image.webp", "wb") as f:
        print("saving image to:", directory_path)
        f.write(response.content)

    with open(f"{directory_path}/info.json", "w") as f:
        print("saving info to:", directory_path)
        json.dump(recipe, f)


def __get_recipe_info(page: Page, recipe_type: str) -> RecipeInfo | None:
    card_handle = page.wait_for_selector("div.card", timeout=2000)
    if card_handle is None:
        print("no card detected")
        return None

    recipe_html = page.locator("div.card > .card-content").inner_html()
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
    __save_image(recipe)
    return recipe


def __get_recipes_from_recipes_list(
    page: Page, recipe_type_element: Locator, start_from: int = 0
) -> list[RecipeInfo]:
    sleep(2)
    recipes = []

    recipe_elements = page.locator(
        "page-moblets-list:nth-child(3) > ion-content > div.scroll-content > ion-list > button"
    ).all()
    print("recipe_elements:")
    print(recipe_elements)

    recipes_type = page.locator("div.toolbar-title").all()[-1].inner_text()
    for recipe in recipe_elements[start_from:]:
        try:
            recipe.click()
            recipe = __get_recipe_info(page, recipes_type.strip())
            recipes.append(recipe)
            start_from += 1
            if recipe is not None:
                __click_back_button(page)
        except Exception as e:
            print("error:", e)
            __click_back_button(page)
            try:
                print("maybe stuck on recipe types page... clicking recipe type button")
                recipe_type_element.click()
                __get_recipes_from_recipes_list(page, recipe_type_element, start_from)
            except:
                print(
                    "unable to click recipe type. probably stuck somewhere else. returning..."
                )
                return recipes

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

        for recipe_type in recipe_type_list:
            print("getting recipe list for type:", recipe_type.inner_text().strip())
            type_name = recipe_type.inner_text().strip()

            try:
                recipe_type.click()
                print("clicked recipe type:", type_name)
                recipes = __get_recipes_from_recipes_list(page, recipe_type)
                print("got recipes")
            except Exception as e:
                print("error:", e)
            finally:
                if len(recipes) > 0:
                    __click_back_button(page)


if __name__ == "__main__":
    get_recipes()
