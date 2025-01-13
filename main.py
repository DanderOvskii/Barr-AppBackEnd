from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from database import get_session, init_db
from crud import  get_products,get_categories
from models import Products,Categories

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081"],  # Adjust this to your frontend's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Initialize the database
@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/Products/", response_model=list[Products])
def read_items(categoryId: int = None, session: Session = Depends(get_session)):
    return get_products(session, categoryId)

@app.get("/", response_model=list[Categories])  # New endpoint to get all items
def read_categories(session: Session = Depends(get_session)):
    return get_categories(session)

