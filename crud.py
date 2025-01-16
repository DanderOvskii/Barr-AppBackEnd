from sqlmodel import Session, select
from models import Products,Categories,CategoryWithProducts


def get_products(session: Session, categoryId: int = None):
    statement = (
        select(Products)
        .join(Categories, Products.category_id == Categories.id)
    )
    
    if categoryId is not None:
        statement = statement.where(Products.category_id == categoryId)
    
    return session.exec(statement).all()

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
        category_id=product.category_id,
        calorien=product.calorien,
        alcohol=product.alcohol
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
