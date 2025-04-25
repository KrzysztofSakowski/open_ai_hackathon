import asyncio
from settings import openai_client


async def main() -> None:
    print(f"Hello World {openai_client}")


if __name__ == "__main__":
    asyncio.run(main())
