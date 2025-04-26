import uvicorn

if __name__ == "__main__":
    env_settings.load()  # Sanity check env
    uvicorn.run("api:app", host="localhost", port=8000, reload=True)
