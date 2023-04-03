from get_recipes import get_recipes
from builder_bot import build_app


if __name__ == "__main__":
    print("starting...")
    get_recipes()
    print("done getting recipes")
    print("building app...")
    build_app()
    print("finished building app")
