from typing import Optional

import dotenv


def load_env(dotenv_path: Optional[str] = None):
    # pylint: disable=broad-exception-caught
    try:
        dotenv.load_dotenv(dotenv_path)  # Load environment variables from .env file if present
    except Exception as e:  # noqa
        print(f"Error loading .env file: {e}")
        print("Continuing without .env file.")
    # if "pytest" in sys.modules:
    #     forbidden = ["ACCESS_KEY", "SECRET_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]
    #     for key in forbidden:
    #         if key in os.environ:
    #             os.environ.pop(key)

