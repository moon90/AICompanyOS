"""Domain exceptions for company, organization, and department management."""


class CompanyDomainError(Exception):
    """Base domain exception for company operations."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class CompanyNotFoundError(CompanyDomainError):
    """Raised when a requested company entity cannot be located."""


class CompanyAccessDeniedError(CompanyDomainError):
    """Raised when an authenticated user does not have membership or required role in a company."""


class DepartmentNotFoundError(CompanyDomainError):
    """Raised when a requested department cannot be located within a company."""


class DepartmentAlreadyExistsError(CompanyDomainError):
    """Raised when attempting to create a department with a duplicate code or name in a company."""


class DuplicateMembershipError(CompanyDomainError):
    """Raised when attempting to add a user who already belongs to the company."""


class InvalidCompanyDataError(CompanyDomainError):
    """Raised when company or department input violates domain constraints."""
