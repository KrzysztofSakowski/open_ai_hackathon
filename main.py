import asyncio
from settings import openai_client


async def main() -> None:
    print("Hello World! The OpenAI client is initialized and ready to use.")


if __name__ == "__main__":
    asyncio.run(main())
