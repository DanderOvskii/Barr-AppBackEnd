from fastapi import FastAPI, Depends, HTTPException,status
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from database import get_session, init_db
from crud import  get_products,get_categories,get_categories_with_products,update_product,create_product_db,delete_product,search_products,create_user,get_user_by_username,authenticate_user,get_user_stats,update_user,create_category,delete_category
from models import Products,Categories,CategoryWithProducts,User,UserUpdate
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from auth import create_access_token, verify_token
from datetime import date


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
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


@app.get("/ProductManager/", response_model=list[CategoryWithProducts])
def read_categories_with_products(session: Session = Depends(get_session)):
    return get_categories_with_products(session)

@app.put("/ProductManager/{productId}", response_model=Products)
def update_item(productId: int, updated_product: Products, session: Session = Depends(get_session)):
    return update_product(session, productId, updated_product)

@app.post("/ProductManager/", response_model=Products, status_code=status.HTTP_201_CREATED)
def create_product(product: Products, session: Session = Depends(get_session)):
    try:
        return create_product_db(session, product)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.delete("/ProductManager/{productId}")
def delete_item(productId: int, session: Session = Depends(get_session)):
    try:
        return delete_product(session, productId)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/search", response_model=list[Products])
def search_items(q: str, session: Session = Depends(get_session)):
    results = search_products(session, q)
    print('Search Results:', results)  # Print the data
    return results

@app.post("/register")
def register_user(
    username: str,
    password: str,
    birthdate: date,
    session: Session = Depends(get_session)
):
    db_user = get_user_by_username(session, username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    user = create_user(session, username, password,birthdate)
    access_token = create_access_token(user_id=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(user_id=user.id)
    return {"access_token": access_token, "token_type": "bearer"}



@app.get("/verify-token/{token}")
async def verify_token_token(token: str):
    verify_token(token=token)
    return {"token": token}

@app.get("/users/me", response_model=dict)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
):
    try:
        user_id = verify_token(token)
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        user_stats = get_user_stats(session, user.id)
        return {
            "id": user.id,
            "username": user.username,
            "wallet": user_stats.wallet if user_stats else 0.0
        }
    except HTTPException as e:
        raise e
    
@app.post("/buy/{product_id}")
async def buy_product(
    product_id: int,
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
):
    # Verify user
    user_id = verify_token(token)
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get product
    product = session.get(Products, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get user stats
    user_stats = get_user_stats(session, user.id)
    if not user_stats:
        raise HTTPException(status_code=404, detail="User stats not found")
    

    # Update wallet and product inventory
    user_stats.wallet -= product.price
    user_stats.calories += product.calorien
    user_stats.alcohol += product.amount*product.alcohol/100
    product.vooraad -= 1
    
    session.commit()
    
    return {
        "message": "Purchase successful",
        "new_balance": user_stats.wallet,
        "product_name": product.name
    }
    
@app.put("/users/update", response_model=dict)
async def update_user_endpoint(
    user_data: dict,
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
):
    try:
        # Verify token and get username
        user_id = verify_token(token)
        
        # Update user
        updated_user = update_user(session, user_id, user_data)
        return updated_user
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating user data"
        )
    
@app.post("/ProductManager/categories", response_model=Categories, status_code=status.HTTP_201_CREATED)
def create_category_endpoint(category: Categories, session: Session = Depends(get_session)):
    try:
        return create_category(session, category.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.delete("/ProductManager/categories/{categoryId}")
def delete_category_endpoint(categoryId: int, session: Session = Depends(get_session)):
    try:
        return delete_category(session, categoryId)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
