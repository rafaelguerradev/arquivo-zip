import asyncio
import os

from dotenv import load_dotenv

from app.github_client import comentar_pull_request


load_dotenv()

REPO = os.getenv("GITHUB_TEST_REPO")
PR_NUMBER = os.getenv("GITHUB_TEST_PR")

if not REPO or not PR_NUMBER:
    raise RuntimeError(
        "Defina GITHUB_TEST_REPO e GITHUB_TEST_PR no arquivo .env."
    )

PR_NUMBER = int(PR_NUMBER)


async def main():
    body = """
# 🤖 Teste do AI Code Review

Este é um comentário enviado automaticamente
pela API do projeto.

✅ Comunicação com GitHub funcionando.
"""

    response = await comentar_pull_request(
        REPO,
        PR_NUMBER,
        body,
    )

    print("Comentário criado!")
    print("ID:", response["id"])
    print("URL:", response["html_url"])


if __name__ == "__main__":
    asyncio.run(main())