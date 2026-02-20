"""Entry point for running the FastAPI server."""

import uvicorn


def run():
    uvicorn.run(
        "ai_fish_tank.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    run()
