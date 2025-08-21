from sqlmodel import Session, select,func
from models import Products,Categories,CategoryWithProducts,User,UserStats,Purchase
from auth import get_password_hash, verify_password
from datetime import date, datetime, timedelta
from decimal import Decimal
from calendar import monthrange
def get_products(session: Session, categoryId: int = None):
    statement = (
        select(Products)
        .join(Categories, Products.category_id == Categories.id)
    )
    
    if categoryId is not None:
        statement = statement.where(Products.category_id == categoryId)
    
    return session.exec(statement).all()

def get_product(session: Session, productId: int = None):
    if productId is None:
        return None
    product = session.get(Products, productId)
    return(product)
    

def get_categories(session: Session):
    return session.exec(select(Categories)).all()

def get_categories_with_products(session: Session):
    statement = (
        select(Categories)
        .outerjoin(Products, Categories.id == Products.category_id)
    )
    
    categories = session.exec(statement).unique().all()
    result = []
    
    for category in categories:
        products_statement = select(Products).where(Products.category_id == category.id)
        products = session.exec(products_statement).all()
        
        category_data = CategoryWithProducts(
            id=category.id,
            name=category.name,
            products=products
        )
        result.append(category_data)
    
    return result

def update_product(session: Session, product_id: int, updated_product: Products):
    product = session.get(Products, product_id)
    if not product:
        raise ValueError("Product not found")
    
    for key, value in updated_product.dict(exclude_unset=True).items():
        setattr(product, key, value)
    
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

def create_product_db(session: Session, product: Products):
    # Verify if category exists
    category = session.get(Categories, product.category_id)
    if not category:
        raise ValueError(f"Category with id {product.category_id} does not exist")
    
    # Create new product
    db_product = Products(
        name=product.name,
        price=product.price,
        amount=product.amount,
        category_id=product.category_id,
        calorien=product.calorien,
        alcohol=product.alcohol,
        vooraad=product.vooraad,
        korting=product.korting,
    )
    
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product

def delete_product(session: Session, product_id: int):
    product = session.get(Products, product_id)
    if not product:
        raise ValueError("Product not found")
    
    session.delete(product)
    session.commit()
    return {"message": "Product deleted successfully"}

def search_products(session: Session, query: str):
    statement = select(Products).where(Products.name.contains(query))
    return session.exec(statement).all()

def get_user_by_username(session: Session, username: str):
    statement = select(User).where(User.username == username)
    return session.exec(statement).first()

def create_user(session: Session, username: str, password: str,birthdate: date, is_admin: bool = False):
    hashed_password = get_password_hash(password)
    db_user = User(username=username, password=hashed_password,birthdate=birthdate, is_admin=is_admin)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    create_user_stats(session, db_user.id)
    return db_user

def authenticate_user(session: Session, username: str, password: str):
    user = get_user_by_username(session, username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_user_stats(session: Session, user_id: int):
    user_stats = UserStats(user_id=user_id)
    session.add(user_stats)
    session.commit()
    session.refresh(user_stats)
    return user_stats

def get_user_stats(session: Session, user_id: int):
    statement = select(UserStats).where(UserStats.user_id == user_id)
    return session.exec(statement).first()


def update_user(session: Session, user_id: int, user_data: dict):
    # Get user and their stats
    user = session.get(User, user_id)
    if not user:
        raise ValueError("User not found")
    
    user_stats = get_user_stats(session, user.id)
    if not user_stats:
        raise ValueError("User stats not found")

    # Update username if provided and different
    if user_data.get("username") and user_data["username"] != user.username:
        # Check if new username is already taken
        existing_user = get_user_by_username(session, user_data["username"])
        if existing_user:
            raise ValueError("Username already taken")
        user.username = user_data["username"]

    # Update password if provided
    if user_data.get("password"):
        user.password = get_password_hash(user_data["password"])

    # Update wallet if provided
    if "wallet" in user_data:
        user_stats.wallet = user_data["wallet"]

    session.commit()
    session.refresh(user)
    session.refresh(user_stats)

    return {
        "id": user.id,
        "username": user.username,
        "wallet": user_stats.wallet
    }

def create_category(session: Session, name: str):
    # Check if category with same name already exists
    existing_category = session.exec(
        select(Categories).where(Categories.name == name)
    ).first()
    
    if existing_category:
        raise ValueError("Category with this name already exists")
    
    # Create new category
    db_category = Categories(name=name)
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category

def delete_category(session: Session, category_id: int):
    category = session.get(Categories, category_id)
    if not category:
        raise ValueError("category not found")
    
    products = session.exec(
        select(Products).where(Products.category_id == category_id)
        ).all()
    
    for product in products:
        session.delete(product)
        
    session.delete(category)
    session.commit()
    return {"message": "category deleted successfully"}

def create_purchase(session: Session, user_id: int, product_id: int, amount: int):
    """Create a new purchase record"""
    # Get product to verify it exists and get price info
    product = get_product(session, product_id)
    
    # Calculate prices
    product_price = product.price
    discount = product.korting
    discounted_price = product_price - (product_price * discount // 100)
    total_price = discounted_price * amount
    total_alcohol = ((product.alcohol/100)*product.amount) * amount
    total_calories = product.calorien * amount
    
    # Create purchase record
    purchase = Purchase(
        user_id=user_id,
        product_id=product_id,
        amount=amount,
        product_price=product_price,
        total_price=total_price,
        total_alcohol=total_alcohol,
        total_calories=total_calories,
        discount=discount,
        purchase_date=datetime.now()
    )
    
    session.add(purchase)
    session.commit()
    session.refresh(purchase)
    return purchase

def get_user_purchases(session: Session, user_id: int):
    """Get all purchases for a specific user, ordered by newest first"""
    statement = select(Purchase).where(Purchase.user_id == user_id).order_by(Purchase.purchase_date.desc())
    return session.exec(statement).all()

def get_stats(session: Session, user_id: int, date:date, period:int):
    # Get purchases for the current month
   
    if period == 0:  # Day
        start_date = datetime(date.year, date.month, date.day)
        end_date = start_date + timedelta(days=1)
    elif period == 1:  # Month
        start_date = datetime(date.year, date.month, 1)
        if date.month == 12:
            end_date = datetime(date.year + 1, 1, 1)
        else:
            end_date = datetime(date.year, date.month + 1, 1)
    else:  # Year
        start_date = datetime(date.year, 1, 1)
        end_date = datetime(date.year + 1, 1, 1)

    statement = (
        select( 
            func.sum(Purchase.total_price).label('total_spent'),
            func.sum(Purchase.total_calories).label('total_calories'),
            func.sum(Purchase.total_alcohol).label('total_alcohol'),
            func.count(Purchase.id).label('total_purchases'))
        .where(
            Purchase.user_id == user_id,
            Purchase.user_id == user_id,
            Purchase.purchase_date >= start_date,
            Purchase.purchase_date <= end_date
        ))
    return session.exec(statement).first()