from fastapi import FastAPI
from routers import dash, reports, users
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# Configurar los orígenes permitidos
origins = [
    "http://localhost:4200",  # Especifica el origen de tu frontend
    # Si necesitas permitir otros orígenes, añádelos aquí.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

# Routers
app.include_router(users.router)
app.include_router(reports.router)
app.include_router(dash.router)



@app.get("/")
async def root():
    return {"message": "Hello World"}

