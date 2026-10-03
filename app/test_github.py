import asyncio
import os

from dotenv import load_dotenv

from app.github_client import buscar_diff


load_dotenv()

REPO = os.getenv("GITHUB_TEST_REPO")
PR_NUMBER = os.getenv("GITHUB_TEST_PR")

if not REPO or not PR_NUMBER:
    raise RuntimeError(
        "Defina GITHUB_TEST_REPO e GITHUB_TEST_PR no arquivo .env."
    )

PR_NUMBER = int(PR_NUMBER)


async def main():
    diff = await buscar_diff(REPO, PR_NUMBER)

    print(diff)


if __name__ == "__main__":
    asyncio.run(main())