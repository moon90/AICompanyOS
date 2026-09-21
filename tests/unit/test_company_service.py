from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from application.services.company_service import CompanyService
from domain.company.exceptions import (
    CompanyAccessDeniedError,
    CompanyNotFoundError,
    DepartmentAlreadyExistsError,
    DepartmentNotFoundError,
    InvalidCompanyDataError,
)
from infrastructure.database.base import Base
from infrastructure.database.models import User


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create in-memory SQLite database session for testing CompanyService."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Create test users
        user1 = User(
            id="user-owner-1", name="Owner One", email="owner1@company.os", password_hash="hash1"
        )
        user2 = User(
            id="user-other-2", name="Other User", email="other2@company.os", password_hash="hash2"
        )
        session.add_all([user1, user2])
        await session.commit()
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_company_success(db_session: AsyncSession) -> None:
    """Verify company creation provisions creator as owner and seeds 5 initial departments."""
    service = CompanyService(session=db_session)
    company, member = await service.create_company(
        user_id="user-owner-1",
        name="Nova Technologies",
        description="Autonomous AI enterprise",
        mission="Empower humans with AI teams",
        industry="Software",
    )

    assert company.id is not None
    assert company.name == "Nova Technologies"
    assert company.status == "active"
    assert member.user_id == "user-owner-1"
    assert member.role == "owner"
    assert member.status == "active"

    # Verify initial departments per docs/Phases.md § 7
    departments = await service.get_departments(user_id="user-owner-1", company_id=company.id)
    assert len(departments) == 5
    codes = {d.code for d in departments}
    assert codes == {"cto", "cmo", "sales", "finance", "operations"}


@pytest.mark.asyncio
async def test_create_company_empty_name_fails(db_session: AsyncSession) -> None:
    """Verify empty company name raises InvalidCompanyDataError."""
    service = CompanyService(session=db_session)
    with pytest.raises(InvalidCompanyDataError):
        await service.create_company(user_id="user-owner-1", name="   ")


@pytest.mark.asyncio
async def test_company_isolation_access_denied(db_session: AsyncSession) -> None:
    """Verify a user cannot retrieve a company they do not belong to."""
    service = CompanyService(session=db_session)
    company, _ = await service.create_company(
        user_id="user-owner-1",
        name="Owner Only Corp",
    )

    # user-other-2 tries to access Owner Only Corp
    with pytest.raises(CompanyAccessDeniedError):
        await service.get_company(user_id="user-other-2", company_id=company.id)

    # user-other-2 tries to view departments
    with pytest.raises(CompanyAccessDeniedError):
        await service.get_departments(user_id="user-other-2", company_id=company.id)


@pytest.mark.asyncio
async def test_get_nonexistent_company_raises_not_found(db_session: AsyncSession) -> None:
    """Verify querying non-existent company ID raises CompanyNotFoundError."""
    service = CompanyService(session=db_session)
    with pytest.raises(CompanyNotFoundError):
        await service.get_company(user_id="user-owner-1", company_id="non-existent-id")


@pytest.mark.asyncio
async def test_update_company_by_owner(db_session: AsyncSession) -> None:
    """Verify company owner can modify company properties."""
    service = CompanyService(session=db_session)
    company, _ = await service.create_company(
        user_id="user-owner-1",
        name="Initial Corp",
    )

    updated = await service.update_company(
        user_id="user-owner-1",
        company_id=company.id,
        name="Updated Corp",
        mission="New Mission Statement",
    )
    assert updated.name == "Updated Corp"
    assert updated.mission == "New Mission Statement"


@pytest.mark.asyncio
async def test_create_custom_department_and_prevent_duplicates(db_session: AsyncSession) -> None:
    """Verify creating custom departments and blocking duplicate department codes in company."""
    service = CompanyService(session=db_session)
    company, _ = await service.create_company(
        user_id="user-owner-1",
        name="Department Test Corp",
    )

    # Create new department
    legal_dept = await service.create_department(
        user_id="user-owner-1",
        company_id=company.id,
        name="Legal & Compliance",
        code="legal",
        lead_role="General Counsel",
        description="Legal and regulatory compliance",
    )
    assert legal_dept.code == "legal"

    # Attempt to create duplicate code
    with pytest.raises(DepartmentAlreadyExistsError):
        await service.create_department(
            user_id="user-owner-1",
            company_id=company.id,
            name="Another Legal",
            code="legal",
        )


@pytest.mark.asyncio
async def test_update_department(db_session: AsyncSession) -> None:
    """Verify updating department role and status."""
    service = CompanyService(session=db_session)
    company, _ = await service.create_company(
        user_id="user-owner-1",
        name="Dept Update Corp",
    )
    depts = await service.get_departments(user_id="user-owner-1", company_id=company.id)
    cto_dept = next(d for d in depts if d.code == "cto")

    updated = await service.update_department(
        user_id="user-owner-1",
        company_id=company.id,
        department_id=cto_dept.id,
        lead_role="VP of Engineering",
        status="active",
    )
    assert updated.lead_role == "VP of Engineering"

    # Attempt update non-existent department
    with pytest.raises(DepartmentNotFoundError):
        await service.update_department(
            user_id="user-owner-1",
            company_id=company.id,
            department_id="fake-dept-id",
            lead_role="Lead",
        )
