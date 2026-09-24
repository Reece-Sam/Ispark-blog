from fastapi import FastAPI
import uvicorn

from routes import router

app = FastAPI()


app.include_router(router)


@app.get("/")
def home():
    return {
        "message": "iSpark Blog Service is running"
    }


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)