import json
import time
from playwright.sync_api import sync_playwright, Page, Locator
from dotenv import load_dotenv
from get_recipes import RecipeInfo
from PIL import Image
import os

load_dotenv()

EMAIL = os.getenv("APP_BUILDER_USERNAME")
PASSWORD = os.getenv("APP_BUILDER_PASSWORD")


def __add_single_recipe(page: Page, folder_path: str):
    page.get_by_text("Adicionar item").click()
    title_input = page.locator("input[type=text]").all()[0]
    codigo_fonte_btn = page.get_by_text("Código-Fonte")

    with open(f"{folder_path}/info.json", "r") as file:
        recipe_info: RecipeInfo = json.load(file)

    source_image = Image.open(f"{folder_path}/image.webp")
    png_image = source_image.convert("RGBA")
    png_image.save(f"{folder_path}/image.png", "PNG")

    add_image_btn = page.locator("div.custom-file-image")

    with page.expect_file_chooser() as fc_info:
        add_image_btn.click()
        file_chooser = fc_info.value
        file_chooser.set_files(f"{folder_path}/image.png")

    time.sleep(4)
    title_input.fill(recipe_info["title"])
    codigo_fonte_btn.click()
    time.sleep(1)
    text_area = page.locator("*[role=presentation] textarea")
    text_area.fill(recipe_info["card_html"])
    codigo_fonte_btn.click()
    page.locator('button[type="submit"]').click()


def __add_recipes(page: Page):
    recipe_type = page.locator("div > input.mat-input-element").input_value()
    try:
        recipe_type_path = os.listdir(f"images/{recipe_type}".lower())
    except Exception as e:
        print(e)
        return
    for recipe_folder in recipe_type_path:
        recipe_path = f"images/{recipe_type}/{recipe_folder}".lower()
        print(recipe_path)
        __add_single_recipe(page, recipe_path)
        time.sleep(2)


def __delete_recipes(page: Page):
    time.sleep(1)
    existing_recipes = page.locator("div > div#pageItems > div").all()
    if len(existing_recipes) == 0:
        return
    existing_recipes[0].hover()
    existing_recipes[0].locator("mat-icon").all()[-1].click()
    page.locator("span").get_by_text("Excluir").click()
    time.sleep(2)
    __delete_recipes(page)


def __edit_recipe_types(page: Page, elements: list[Locator]):
    for element in elements:
        element.click()
        time.sleep(4)

        __delete_recipes(page)
        __add_recipes(page)

        page.locator("div.header > div > button").click()  # back button
        time.sleep(2)
        page.locator(
            "div:nth-child(5) > app-content-management-pages > div >  \
        div.page-draggable-wrapper > div.right-actions-container > \
        button > span.mat-button-wrapper > mat-icon"
        ).click()


def __edit_app(page: Page):
    time.sleep(3)
    page.get_by_text("Editar app").all()[0].click()

    time.sleep(3)

    page.locator("li:nth-of-type(2) span.mat-button-wrapper > mat-icon").click()

    time.sleep(3)

    page.locator(
        "div:nth-child(5) > app-content-management-pages > div >  \
        div.page-draggable-wrapper > div.right-actions-container > \
        button > span.mat-button-wrapper > mat-icon"
    ).click()

    time.sleep(2)
    recipe_type_elements = page.locator("div.-subpage").all()
    print(recipe_type_elements)
    __edit_recipe_types(page, recipe_type_elements)


def __access_app(page: Page):
    time.sleep(4)
    page.wait_for_selector("a[mat-tab-link]")
    access_app_btn = page.get_by_text("Acessar App")

    time.sleep(4)

    page.keyboard.press("Escape")
    access_app_btn.click()


def __login(page: Page):
    assert EMAIL is not None
    assert PASSWORD is not None
    page.wait_for_selector("input[formcontrolname]")
    email_input = page.get_by_placeholder("E-mail")

    email_input.fill(EMAIL)

    advance_btn = page.locator("button span[matripple]").all()[-1]

    advance_btn.click(timeout=1000)

    time.sleep(2)

    password_input = page.get_by_placeholder("Digite sua senha")

    password_input.fill(PASSWORD)

    login_btn = page.locator("span.mat-button-wrapper").all()[-1]

    login_btn.click()


def build_app():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://studio.fabricadeaplicativos.com.br/painel/signin")

        __login(page)
        __access_app(page)
        __edit_app(page)
        print("done")


if __name__ == "__main__":
    build_app()
