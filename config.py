import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Config:
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    USER_PROFILES_DIR = DATA_DIR / "user_profiles"

    DATA_DIR.mkdir(exist_ok=True)
    USER_PROFILES_DIR.mkdir(exist_ok=True)

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    @classmethod
    def get_display_info(cls) -> str:
        status = "Configured" if cls.OPENAI_API_KEY else "Missing"
        info = [
            "Configuration Status",
            "",
            f"OpenAI: {status}",
        ]
        return "\n".join(info)


config = Config()


def check_api_keys():
    if not config.OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. "
            "Please create a .env file with your OpenAI API key."
        )


if __name__ == "__main__":
    print(config.get_display_info())

    try:
        check_api_keys()
        print("\nAll required API keys are configured!")
    except ValueError as e:
        print(f"\nConfiguration Error: {e}")
