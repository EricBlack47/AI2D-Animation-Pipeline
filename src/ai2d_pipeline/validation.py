"""Validation primitives shared by pipeline stages."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    code: str
    severity: Severity
    message: str
    file: str | None = None
    expected: str | None = None
    actual: str | None = None
    remediation: str | None = None


def as_dict(issue: ValidationIssue) -> dict:
    return {
        "code": issue.code,
        "severity": issue.severity.value,
        "message": issue.message,
        "file": issue.file,
        "expected": issue.expected,
        "actual": issue.actual,
        "remediation": issue.remediation,
    }


def has_error(issues: List[ValidationIssue]) -> bool:
    return any(issue.severity == Severity.ERROR for issue in issues)


def merge_reports(*reports: List[ValidationIssue]) -> List[ValidationIssue]:
    merged: List[ValidationIssue] = []
    for item in reports:
        merged.extend(item)
    return merged
