from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uvicorn

# ========== НАШИ МОДУЛИ ==========
from app.database.database import engine, Base, get_db
from app.config import settings
from app.utils.security import get_password_hash

# Импортируем все модели для создания таблиц
from app.models import (
    users, roles, freelancers, projects, proposals,
    payments, reviews, messages, skills, freelancer_skills
)

# Импортируем модели напрямую для начальных данных и создания таблиц
from app.models.roles import RoleModel
from app.models.users import UserModel
from app.models.projects import ProjectModel
from app.models.responces import ResponseModel
from app.models.freelancers import FreelancerModel
# Другие модели, если нужны

# Импортируем все CRUD роутеры
from app.api.endpoints import (
    users as users_router,
    freelancers as freelancers_router,
    projects as projects_router,
    proposals as proposals_router,
    payments as payments_router,
    reviews as reviews_router,
    messages as messages_router,
    skills as skills_router,
    freelancer_skills as freelancer_skills_router
)
from app.api import auth
# =================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер для управления жизненным циклом приложения
    """
    print("=" * 50)
    print("🚀 ЗАПУСК ФРИЛАНС-ПЛАТФОРМЫ")
    print("=" * 50)
    
    # Создаем таблицы в базе данных
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблицы базы данных созданы")
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        raise
    
    # Создаем начальные данные
    await create_initial_data()
    
    print("\n" + "=" * 50)
    print("🌐 СЕРВЕР ЗАПУЩЕН")
    print("=" * 50)
    print(f"📱 HTML интерфейс:    http://127.0.0.1:8001")
    print(f"📚 Документация API:  http://127.0.0.1:8001/docs")
    print(f"📖 Альтернативная:    http://127.0.0.1:8001/redoc")
    print(f"❤️  Проверка здоровья: http://127.0.0.1:8001/health")
    print("=" * 50)
    
    yield  # Здесь приложение работает
    
    print("\n" + "=" * 50)
    print("🛑 ЗАВЕРШЕНИЕ РАБОТЫ")
    print("=" * 50)
    
    await engine.dispose()  # Закрываем соединения с БД
    print("🔌 Соединения с базой данных закрыты")

async def create_initial_data():
    """
    Создает начальные данные в базе (роли, администратора)
    """
    from app.database.database import async_session_maker
    
    async with async_session_maker() as session:
        try:
            # 1. Создаем роли, если их нет
            result = await session.execute(select(RoleModel))
            existing_roles = result.scalars().all()
            
            if not existing_roles:
                print("📝 Создаем начальные роли...")
                
                # Базовые роли для платформы
                roles_to_create = [
                    RoleModel(name="admin", description="Администратор системы"),
                    RoleModel(name="client", description="Клиент (заказчик проектов)"),
                    RoleModel(name="freelancer", description="Фрилансер (исполнитель)")
                ]
                
                for role in roles_to_create:
                    session.add(role)
                
                await session.commit()
                print("   ✅ Создано 3 роли: admin, client, freelancer")
            
            # 2. Создаем администратора, если его нет
            result = await session.execute(
                select(UserModel).where(UserModel.email == "admin@example.com")
            )
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                print("👑 Создаем администратора по умолчанию...")
                
                # Находим роль admin
                result = await session.execute(
                    select(RoleModel).where(RoleModel.name == "admin")
                )
                admin_role = result.scalar_one_or_none()
                
                if admin_role:
                    # Создаем администратора
                    new_admin = UserModel(
                        name="Администратор Системы",
                        email="admin@example.com",
                        hashed_password=get_password_hash("admin123"),
                        role_id=admin_role.id
                    )
                    
                    session.add(new_admin)
                    await session.commit()
                    
                    print("   ✅ Администратор создан")
                    print("   📧 Email: admin@example.com")
                    print("   🔑 Пароль: admin123")
                    print("   ⚠️  Измените пароль после первого входа!")
            
            print("✅ Начальные данные успешно созданы")
            
        except Exception as e:
            print(f"⚠️  Ошибка при создании начальных данных: {e}")
            await session.rollback()

# ========== СОЗДАНИЕ ПРИЛОЖЕНИЯ ==========
app = FastAPI(
    title="Freelance Platform",
    description="Платформа для фрилансеров и клиентов с полным API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json"
)

# ========== НАСТРОЙКА CORS ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене замените на домены фронтенда
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# ========== СТАТИЧЕСКИЕ ФАЙЛЫ И ШАБЛОНЫ ==========
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ========== HTML СТРАНИЦЫ (ФРОНТЕНД) ==========

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Главная страница платформы"""
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "title": "Фриланс-Платформа | Главная"}
    )

@app.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request):
    """Страница с проектами (заданиями)"""
    return templates.TemplateResponse(
        "jobs.html", 
        {"request": request, "title": "Проекты | Фриланс-Платформа"}
    )

@app.get("/post-project", response_class=HTMLResponse)
async def post_project_page(request: Request):
    """Страница размещения нового проекта"""
    return templates.TemplateResponse(
        "post_project.html", 
        {"request": request, "title": "Разместить проект"}
    )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Страница входа в систему"""
    return templates.TemplateResponse(
        "login.html", 
        {"request": request, "title": "Вход в систему"}
    )

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Личный кабинет пользователя"""
    return templates.TemplateResponse(
        "dashboard.html", 
        {"request": request, "title": "Личный кабинет"}
    )

# ========== API РОУТЕРЫ (БЭКЕНД) ==========

# Пользователи (Users)
app.include_router(
    users_router.router,
    prefix="/api/users",
    tags=["👥 Пользователи"]
)

# Фрилансеры (Freelancers)
app.include_router(
    freelancers_router.router,
    prefix="/api/freelancers",
    tags=["👨‍💻 Фрилансеры"]
)

# Проекты (Projects)
app.include_router(
    projects_router.router,
    prefix="/api/projects",
    tags=["📋 Проекты"]
)

# Предложения (Proposals)
app.include_router(
    proposals_router.router,
    prefix="/api/proposals",
    tags=["💼 Предложения"]
)

# Платежи (Payments)
app.include_router(
    payments_router.router,
    prefix="/api/payments",
    tags=["💰 Платежи"]
)

# Отзывы (Reviews)
app.include_router(
    reviews_router.router,
    prefix="/api/reviews",
    tags=["⭐ Отзывы"]
)

# Сообщения (Messages)
app.include_router(
    messages_router.router,
    prefix="/api/messages",
    tags=["✉️ Сообщения"]
)

# Навыки (Skills)
app.include_router(
    skills_router.router,
    prefix="/api/skills",
    tags=["🔧 Навыки"]
)

# Связи фрилансер-навыки (FreelancerSkills)
app.include_router(
    freelancer_skills_router.router,
    prefix="/api/freelancer-skills",
    tags=["🔗 Навыки фрилансеров"]
)

# Аутентификация (Auth)
app.include_router(
    auth.router,
    prefix="/api",
    tags=["🔐 Аутентификация"]
)

# ========== СИСТЕМНЫЕ ЭНДПОИНТЫ ==========

@app.get("/health", tags=["⚙️ Система"])
async def health_check():
    """Проверка здоровья системы"""
    return {
        "status": "healthy",
        "service": "freelance-platform",
        "version": "2.0.0",
        "api": "active",
        "database": "connected"
    }

@app.get("/api/info", tags=["⚙️ Система"])
async def api_info():
    """Информация об API"""
    return {
        "name": "Freelance Platform API",
        "version": "2.0.0",
        "description": "Полный API для управления фриланс-платформой",
        "documentation": "/docs",
        "endpoints": [
            {"name": "Пользователи", "path": "/api/users", "methods": ["GET", "POST", "PUT", "DELETE"]},
            {"name": "Фрилансеры", "path": "/api/freelancers", "methods": ["GET", "POST", "PUT", "DELETE"]},
            {"name": "Проекты", "path": "/api/projects", "methods": ["GET", "POST", "PUT", "DELETE"]},
            {"name": "Предложения", "path": "/api/proposals", "methods": ["GET", "POST", "PUT", "DELETE"]},
            {"name": "Платежи", "path": "/api/payments", "methods": ["GET", "POST", "PUT", "DELETE"]},
            {"name": "Отзывы", "path": "/api/reviews", "methods": ["GET", "POST", "PUT", "DELETE"]},
            {"name": "Сообщения", "path": "/api/messages", "methods": ["GET", "POST", "PUT", "DELETE"]},
            {"name": "Навыки", "path": "/api/skills", "methods": ["GET", "POST", "PUT", "DELETE"]},
            {"name": "Связи фрилансер-навыки", "path": "/api/freelancer-skills", "methods": ["GET", "POST", "DELETE"]}
        ]
    }

@app.get("/test-db", tags=["⚙️ Система"])
async def test_db(db: AsyncSession = Depends(get_db)):
    """Тест подключения к базе данных"""
    from sqlalchemy import text
    
    try:
        result = await db.execute(text("SELECT 1"))
        value = result.scalar()
        
        return {
            "database": "connected",
            "test": "successful",
            "result": value == 1
        }
    except Exception as e:
        return {
            "database": "error",
            "error": str(e),
            "result": False
        }

# ========== ЗАПУСК СЕРВЕРА ==========

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8001,
        reload=True,          # Автоматическая перезагрузка при изменении кода
        log_level="info",     # Уровень логирования
        access_log=True       # Логирование запросов
    )