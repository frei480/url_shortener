import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Url shortener")


@app.get("/health", status_code=200)
def health_check():
    return {"status": "ok"}


def main():
    print("Hello from url-shortener!")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True)
