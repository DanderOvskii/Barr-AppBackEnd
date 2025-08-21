from fastapi import FastAPI, Depends, HTTPException,status
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from database import get_session, init_db
from crud import  get_products,get_categories,get_categories_with_products,update_product,create_product_db,delete_product,search_products,create_user,get_user_by_username,authenticate_user,get_user_stats,update_user,create_category,delete_category,get_product,create_purchase,get_user_purchases,get_stats
from models import Products,Categories,CategoryWithProducts,User,UserUpdate,productResponse,statsResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from auth import create_access_token, token_required, get_current_user, get_current_admin
from datetime import date


app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["exp://192.168.1.99:8081",  # Expo Go app
        "http://localhost:8081", ],  # Adjust this to your frontend's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Initialize the database
@app.on_event("startup")
def on_startup():
    init_db()

def cents_to_euros(cents: int) -> float:
    """Convert cents to euros with 2 decimal places"""
    return round(cents / 100, 2)

def euros_to_cents(cents: float) -> int:
    """Convert cents to euros with 2 decimal places"""
    return round(cents *100)

def cal_discount_price(price: int, discount: int) -> int:
    """Calculate the discounted price"""
    return price - (price * discount // 100)

#LOGIN REGESTRATION FUNCTIONS//////////////////////////////////////////////////////////////////////////////////////////////////////
@app.post("/register")
def register_user(
    username: str,
    password: str,
    birthdate: date,
    is_admin: bool = False,
    session: Session = Depends(get_session)
):
    db_user = get_user_by_username(session, username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    user = create_user(session, username, password,birthdate, is_admin)
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
#LOGIN REGESTRATION FUNCTIONS//////////////////////////////////////////////////////////////////////////////////////////////////////

@app.get("/", response_model=list[Categories])  # New endpoint to get all items
def read_categories(
    _: None = Depends(token_required),
    session: Session = Depends(get_session),
    ):
    return get_categories(session)

@app.get("/Products/", response_model=list[productResponse])
def read_items(
    categoryId: int = None, 
    _: None = Depends(token_required),
    session: Session = Depends(get_session),
    ):
    products = get_products(session, categoryId)
    # Convert prices to euros
    products_response = []
    for product in products:
        discount_price_cents = cal_discount_price(product.price, product.korting)
        discount_price = cents_to_euros(discount_price_cents)
        price = cents_to_euros(product.price)
        

        products_response.append(
            productResponse(
                id=product.id,
                name=product.name,
                price=price,
                amount=product.amount,
                category_id=product.category_id,
                calorien=product.calorien,
                alcohol=product.alcohol,
                vooraad=product.vooraad,
                korting=product.korting,
                discount_price=discount_price
            )
        )
    return products_response

@app.get("/Product/", response_model=productResponse)
def read_item(
    productId: int = None, 
    _: None = Depends(token_required),
    session: Session = Depends(get_session),
    ):
    product = get_product(session, productId)
    # Convert prices to euros
    discount_price_cents = cal_discount_price(product.price, product.korting)
    discount_price = cents_to_euros(discount_price_cents)
    price = cents_to_euros(product.price)

    product = productResponse(
        id=product.id,
        name=product.name,
        price=price,
        amount=product.amount,
        category_id=product.category_id,    
        calorien=product.calorien,
        alcohol=product.alcohol,
        vooraad=product.vooraad,
        korting=product.korting,
        discount_price=discount_price
    )
    return product






@app.get("/search", response_model=list[Products])
def search_items(
    q: str, 
    _: None = Depends(token_required),
    session: Session = Depends(get_session),
    ):
    results = search_products(session, q)
    # Convert prices to euros
    for product in results:
        product.price = cents_to_euros(product.price)
    return results






@app.get("/users/me")
async def get_user_info(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    ):
    user_stats = get_user_stats(session=session, user_id=current_user.id)
    return {
        "id": current_user.id,
        "username": current_user.username,
        "wallet": cents_to_euros(user_stats.wallet if user_stats else 0),
        "isAdmin": current_user.is_admin
    }
    
@app.post("/buy/{product_id}")
async def buy_product(
    product_id: int,
    amount: int = 1,  # Added amount parameter with default value
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Get product
    product = session.get(Products, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get user stats
    user_stats = get_user_stats(session, current_user.id)
    if not user_stats:
        raise HTTPException(status_code=404, detail="User stats not found")
    
    # Calculate total cost
    discountprice = cal_discount_price(product.price, product.korting)
    total_cost = discountprice * amount
    
    # Check if user has enough money
    if user_stats.wallet < total_cost:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Register the purchase in the purchase table
    try:
        purchase = create_purchase(session, current_user.id, product_id, amount)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Update wallet and product inventory
    user_stats.wallet -= total_cost
    user_stats.calories += product.calorien * amount
    user_stats.alcohol += product.amount * product.alcohol / 100 * amount
    product.vooraad -= amount
    
    session.commit()
    
    return {
        "message": "Purchase successful",
        "purchase_id": purchase.id,
        "new_balance": cents_to_euros(user_stats.wallet),
        "product_name": product.name,
        "amount_purchased": amount,
        "total_cost": cents_to_euros(total_cost),
        "purchase_date": purchase.purchase_date
    }

@app.get("/purchases")
async def get_purchase_history(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get purchase history for the current user"""
    purchases = get_user_purchases(session, current_user.id)
    
    # Convert prices to euros and add product names
    purchase_history = []
    for purchase in purchases:
        product = session.get(Products, purchase.product_id)
        purchase_history.append({
            "id": purchase.id,
            "product_name": product.name if product else "Unknown Product",
            "amount": purchase.amount,
            "product_price": cents_to_euros(purchase.product_price),
            "total_price": cents_to_euros(purchase.total_price),
            "discount": purchase.discount,
            "purchase_date": purchase.purchase_date
        })
    
    return purchase_history

@app.get("/stats/monthly")
async def get_stats_endpoint(
    date:date,
    period:int ,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get monthly stats for the current user"""
    stats = get_stats(session, current_user.id, date, period)
    
    
    total_spend=stats.total_spent or 0
    total_calories=stats.total_calories or 0
    total_alcohol=stats.total_alcohol or 0
    total_purchases=stats.total_purchases or 0
    

    

    
    return {
        "total_spent": cents_to_euros(total_spend),
        "calories_consumed": round (total_calories,2),
        "alcohol_consumed": round( total_alcohol,2),
        "products_bought": total_purchases
    }
       

#PRODUCT MANAGER FUNCTIONS//////////////////////////////////////////////////////////////////////////////////////////////////////
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
    
    
@app.get("/ProductManager/", response_model=list[CategoryWithProducts])
def read_categories_with_products(
    _: None = Depends(get_current_admin),
    session: Session = Depends(get_session),
):
    categories = get_categories_with_products(session)
    # Convert prices to euros for all products in all categories
    for category in categories:
        for product in category.products:
            product.price = cents_to_euros(product.price)
    return categories

@app.put("/ProductManager/{productId}", response_model=Products)
def update_item(
    productId: int, 
    updated_product: Products, 
    _: None = Depends(get_current_admin),
    session: Session = Depends(get_session)
    ):
    # Convert price from euros to cents before updating
    if updated_product.price is not None:
        updated_product.price = euros_to_cents(updated_product.price)
    product = update_product(session, productId, updated_product)
    # Convert price back to euros for response
    product.price = cents_to_euros(product.price)
    return product

@app.post("/ProductManager/", response_model=Products, status_code=status.HTTP_201_CREATED)
def create_product(
    product: Products, 
    _: None = Depends(get_current_admin),
    session: Session = Depends(get_session)
    ):
    try:
        return create_product_db(session, product)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.delete("/ProductManager/{productId}")
def delete_item(
    productId: int, 
    _: None = Depends(get_current_admin),
    session: Session = Depends(get_session)
    ):
    try:
        return delete_product(session, productId)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
#PRODUCT MANAGER FUNCTIONS//////////////////////////////////////////////////////////////////////////////////////////////////////
#ACCOUNT MANAGER FUNCTIONS//////////////////////////////////////////////////////////////////////////////////////////////////////
@app.put("/users/update", response_model=dict)
async def update_user_endpoint(
    user_data: dict,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Convert wallet amount from euros to cents before updating
    if "wallet" in user_data:
        user_data["wallet"] = euros_to_cents(user_data["wallet"])
    
    # Update user
    updated_user = update_user(session, current_user.id, user_data)
    
    # Convert wallet back to euros in response
    if "wallet" in updated_user:
        updated_user["wallet"] = cents_to_euros(updated_user["wallet"])
    
    return updated_user
    

#ACCOUNT MANAGER FUNCTIONS//////////////////////////////////////////////////////////////////////////////////////////////////////

    
