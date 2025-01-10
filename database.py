from sqlmodel import SQLModel, create_engine, Session

# Database connection string (adjust for your XAMPP setup)
DATABASE_URL = "mysql+mysqlconnector://root:@127.0.0.1/BarApp"

# Create the engine
engine = create_engine(DATABASE_URL, echo=True)

# Create a session
def get_session():
    with Session(engine) as session:
        yield session

# Initialize database (run migrations)
def init_db():
    SQLModel.metadata.create_all(engine)