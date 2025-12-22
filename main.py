from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy import Column, Integer, String
from contextlib import asynccontextmanager
import uvicorn

# Создаем асинхронный движок для SQLite
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)

# Создаем фабрику сессий
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Базовый класс для моделей
class Base(DeclarativeBase):
    pass

# Модель пользователя
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)

# Создаем таблицы при старте
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаем таблицы при запуске
    await create_tables()
    print("✅ Таблицы созданы")
    yield
    # Закрываем соединения при завершении
    await engine.dispose()
    print("🔌 Соединения закрыты")

app = FastAPI(lifespan=lifespan)

# Зависимость для получения сессии БД
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/")
async def root():
    return {"message": "Фриланс-платформа работает на Python 3.13!"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "python_version": "3.13.9"}

@app.post("/test-db")
async def test_db(db: AsyncSession = Depends(get_db)):
    # Простой тест базы данных
    from sqlalchemy import text
    result = await db.execute(text("SELECT 1"))
    value = result.scalar()
    return {"database_test": value == 1}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)