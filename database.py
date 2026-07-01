from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Hozircha oddiy SQLite bazasidan foydalanamiz, chunki u barcha muhitlarda (Renderda ham) qo'shimcha sozlamalarsiz ishlaydi. 
# Keyinchalik haqiqiy loyiha ishga tushganda buni PostgreSQL ga bitta qatorda o'zgartirib qo'yishimiz mumkin.
SQLALCHEMY_DATABASE_URL = "sqlite:///./perfection_school.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
