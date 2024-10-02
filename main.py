from fastapi import FastAPI
from routers import reports, users

app = FastAPI()

# Routers
app.include_router(users.router)
app.include_router(reports.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

