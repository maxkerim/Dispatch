from fastapi import FastAPI

app = FastAPI(title="Dispatch API")


@app.get("/")
def root():
    return {"message": "Dispatch API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}
