"""Application service for company, organization, and department management."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.company.exceptions import (
    CompanyAccessDeniedError,
    CompanyNotFoundError,
    DepartmentAlreadyExistsError,
    DepartmentNotFoundError,
    InvalidCompanyDataError,
)
from infrastructure.database.models import Company, CompanyMember, Department, User


class CompanyService:
    """Service orchestrating company lifecycle, organizational structures, and membership."""

    DEFAULT_DEPARTMENTS = [
        {
            "name": "CTO",
            "code": "cto",
            "lead_role": "Chief Technology Officer",
            "description": "Technology strategy, engineering architecture, and technical execution.",
        },
        {
            "name": "CMO",
            "code": "cmo",
            "lead_role": "Chief Marketing Officer",
            "description": "Marketing strategy, brand narrative, and customer acquisition.",
        },
        {
            "name": "Sales",
            "code": "sales",
            "lead_role": "Head of Sales",
            "description": "Revenue generation, pipeline management, and client relationships.",
        },
        {
            "name": "Finance",
            "code": "finance",
            "lead_role": "Head of Finance",
            "description": "Capital allocation, financial planning, and budgeting.",
        },
        {
            "name": "Operations",
            "code": "operations",
            "lead_role": "Head of Operations",
            "description": "Organizational execution, procedures, and cross-functional operations.",
        },
    ]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_active_membership(self, user_id: str, company_id: str) -> CompanyMember | None:
        """Helper to retrieve an active membership for a user in a specific company."""
        stmt = select(CompanyMember).where(
            CompanyMember.user_id == user_id,
            CompanyMember.company_id == company_id,
            CompanyMember.status == "active",
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_company(
        self,
        user_id: str,
        name: str,
        description: str | None = None,
        mission: str | None = None,
        industry: str | None = None,
    ) -> tuple[Company, CompanyMember]:
        """Create a new company, establish the creator as owner, and seed standard departments."""
        clean_name = name.strip()
        if not clean_name:
            raise InvalidCompanyDataError("Company name cannot be empty.")

        company = Company(
            name=clean_name,
            description=description.strip() if description else None,
            mission=mission.strip() if mission else None,
            industry=industry.strip() if industry else None,
            status="active",
        )
        self.session.add(company)
        await self.session.flush()

        # Add creator as owner
        membership = CompanyMember(
            company_id=company.id,
            user_id=user_id,
            role="owner",
            status="active",
        )
        self.session.add(membership)

        # Seed initial departments per docs/Phases.md § 7
        for dept in self.DEFAULT_DEPARTMENTS:
            department = Department(
                company_id=company.id,
                name=dept["name"],
                code=dept["code"],
                lead_role=dept["lead_role"],
                description=dept["description"],
                status="active",
            )
            self.session.add(department)

        await self.session.commit()
        await self.session.refresh(company)
        await self.session.refresh(membership)
        return company, membership

    async def get_user_companies(self, user_id: str) -> list[tuple[Company, CompanyMember]]:
        """Return all companies the authenticated user belongs to with their active membership."""
        stmt = (
            select(Company, CompanyMember)
            .join(CompanyMember, Company.id == CompanyMember.company_id)
            .where(
                CompanyMember.user_id == user_id,
                CompanyMember.status == "active",
                Company.status != "archived",
            )
            .order_by(Company.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def get_company(self, user_id: str, company_id: str) -> tuple[Company, CompanyMember]:
        """Retrieve company details while strictly validating user membership."""
        stmt = (
            select(Company, CompanyMember)
            .join(CompanyMember, Company.id == CompanyMember.company_id)
            .where(
                Company.id == company_id,
                CompanyMember.user_id == user_id,
                CompanyMember.status == "active",
            )
        )
        result = await self.session.execute(stmt)
        row = result.first()
        if not row:
            # Check if company exists to provide explicit error
            comp_stmt = select(Company).where(Company.id == company_id)
            comp_res = await self.session.execute(comp_stmt)
            if comp_res.scalars().first() is None:
                raise CompanyNotFoundError(f"Company '{company_id}' was not found.")
            raise CompanyAccessDeniedError("You do not have active membership in this company.")
        return row[0], row[1]

    async def update_company(
        self,
        user_id: str,
        company_id: str,
        name: str | None = None,
        description: str | None = None,
        mission: str | None = None,
        industry: str | None = None,
        status: str | None = None,
    ) -> Company:
        """Update company attributes after verifying caller has owner or admin role."""
        company, member = await self.get_company(user_id, company_id)
        if member.role not in ("owner", "admin"):
            raise CompanyAccessDeniedError(
                "Only company owners and administrators may modify company settings."
            )

        if name is not None:
            clean_name = name.strip()
            if not clean_name:
                raise InvalidCompanyDataError("Company name cannot be empty.")
            company.name = clean_name

        if description is not None:
            company.description = description.strip() if description else None

        if mission is not None:
            company.mission = mission.strip() if mission else None

        if industry is not None:
            company.industry = industry.strip() if industry else None

        if status is not None:
            if status not in ("active", "pending", "archived"):
                raise InvalidCompanyDataError(f"Invalid company status: '{status}'.")
            company.status = status

        await self.session.commit()
        await self.session.refresh(company)
        return company

    async def get_departments(self, user_id: str, company_id: str) -> list[Department]:
        """Retrieve all departments for a company after validating caller membership."""
        await self.get_company(user_id, company_id)
        stmt = (
            select(Department)
            .where(Department.company_id == company_id)
            .order_by(Department.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_department(
        self,
        user_id: str,
        company_id: str,
        name: str,
        code: str,
        description: str | None = None,
        lead_role: str | None = None,
    ) -> Department:
        """Create a new department within a company after validating administrative privileges."""
        _, member = await self.get_company(user_id, company_id)
        if member.role not in ("owner", "admin"):
            raise CompanyAccessDeniedError(
                "Only company owners and administrators may create departments."
            )

        clean_name = name.strip()
        clean_code = code.strip().lower()
        if not clean_name:
            raise InvalidCompanyDataError("Department name cannot be empty.")
        if not clean_code:
            raise InvalidCompanyDataError("Department code cannot be empty.")

        # Check for existing code or name in company
        existing_stmt = select(Department).where(
            Department.company_id == company_id,
            (Department.code == clean_code) | (Department.name == clean_name),
        )
        existing = await self.session.execute(existing_stmt)
        if existing.scalars().first() is not None:
            raise DepartmentAlreadyExistsError(
                f"Department with code '{clean_code}' or name '{clean_name}' already exists in this company."
            )

        department = Department(
            company_id=company_id,
            name=clean_name,
            code=clean_code,
            description=description.strip() if description else None,
            lead_role=lead_role.strip() if lead_role else None,
            status="active",
        )
        self.session.add(department)
        await self.session.commit()
        await self.session.refresh(department)
        return department

    async def update_department(
        self,
        user_id: str,
        company_id: str,
        department_id: str,
        name: str | None = None,
        description: str | None = None,
        lead_role: str | None = None,
        status: str | None = None,
    ) -> Department:
        """Update department configuration after validating administrative privileges."""
        _, member = await self.get_company(user_id, company_id)
        if member.role not in ("owner", "admin"):
            raise CompanyAccessDeniedError(
                "Only company owners and administrators may modify departments."
            )

        stmt = select(Department).where(
            Department.id == department_id,
            Department.company_id == company_id,
        )
        result = await self.session.execute(stmt)
        department = result.scalars().first()
        if not department:
            raise DepartmentNotFoundError(
                f"Department '{department_id}' was not found in this company."
            )

        if name is not None:
            clean_name = name.strip()
            if not clean_name:
                raise InvalidCompanyDataError("Department name cannot be empty.")
            department.name = clean_name

        if description is not None:
            department.description = description.strip() if description else None

        if lead_role is not None:
            department.lead_role = lead_role.strip() if lead_role else None

        if status is not None:
            if status not in ("active", "planned", "inactive"):
                raise InvalidCompanyDataError(f"Invalid department status: '{status}'.")
            department.status = status

        await self.session.commit()
        await self.session.refresh(department)
        return department

    async def get_company_members(
        self, user_id: str, company_id: str
    ) -> list[tuple[CompanyMember, User]]:
        """Retrieve members of a company with their user details."""
        await self.get_company(user_id, company_id)
        stmt = (
            select(CompanyMember, User)
            .join(User, CompanyMember.user_id == User.id)
            .where(CompanyMember.company_id == company_id)
            .order_by(CompanyMember.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]
