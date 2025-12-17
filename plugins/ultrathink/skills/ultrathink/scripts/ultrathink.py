#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "typer[all]>=0.20.0",
#     "pydantic>=2.12.0",
# ]
# ///
"""
UltraThink CLI - A tool for sequential thinking and problem solving

Usage:
    uv run ultrathink.py -t "Your thought here" -n 3
"""

from __future__ import annotations

import ast
import json
import re
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Annotated, Any, Literal

import typer
from pydantic import BaseModel, Field, ValidationError, field_validator

__version__ = "2.0.1"

# =============================================================================
# Models
# =============================================================================


class Assumption(BaseModel):
    """
    Model: Represents an assumption made during thinking process
    Tracks what is being taken for granted in reasoning
    """

    model_config = {"strict": True}

    id: Annotated[
        str,
        Field(
            pattern=r"^(A\d+|[\w-]+:A\d+)$",
            description=(
                "Unique identifier for this assumption "
                "(e.g., 'A1', 'A2' for local, 'session-id:A1' for cross-session)"
            ),
        ),
    ]
    text: Annotated[
        str,
        Field(min_length=1, description="The assumption being made"),
    ]
    confidence: Annotated[
        float,
        Field(
            ge=0.0,
            le=1.0,
            description="Confidence level (0.0-1.0) in this assumption being true",
        ),
    ] = 1.0
    critical: Annotated[
        bool,
        Field(
            description="If false, does the reasoning collapse? (default: True)",
        ),
    ] = True
    verifiable: Annotated[
        bool,
        Field(
            description=(
                "Can this assumption be verified through testing or research? "
                "(default: False)"
            ),
        ),
    ] = False
    evidence: Annotated[
        str | None,
        Field(
            None, description="Why you believe this assumption (reference, reasoning)"
        ),
    ] = None
    verification_status: Annotated[
        Literal["unverified", "verified_true", "verified_false"] | None,
        Field(None, description="Whether this assumption has been verified"),
    ] = None

    @property
    def is_verified(self) -> bool:
        """Check if this assumption has been verified (true or false)"""
        return self.verification_status in ("verified_true", "verified_false")

    @property
    def is_falsified(self) -> bool:
        """Check if this assumption has been proven false"""
        return self.verification_status == "verified_false"

    @property
    def is_risky(self) -> bool:
        """Check if this is a risky assumption (critical, low confidence, unverified)"""
        return (
            self.critical
            and self.confidence < 0.7
            and self.verification_status != "verified_true"
        )


def _validate_thought_not_empty(value: str) -> str:
    """Helper function to validate thought is non-empty"""
    if not value or not value.strip():
        raise ValueError("thought must be a non-empty string")
    return value


def _parse_json_list(value: Any, field_name: str) -> Any:
    """Parse JSON string to list, or return value as-is.

    Supports both standard JSON (double quotes) and Python-style literals
    (single quotes) to handle shell argument mangling.
    """
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value in {"", "null"}:
        return None
    if isinstance(value, str):
        # Try standard JSON first
        try:
            parsed = json.loads(value)
            if not isinstance(parsed, list):
                raise ValueError(
                    f"{field_name} must be a list or valid JSON string "
                    f"representing a list. Got type: {type(parsed).__name__}"
                )
            return parsed
        except json.JSONDecodeError:
            pass

        # Fallback: try Python literal syntax (handles single quotes)
        # This helps when shell command arguments mangle JSON quotes
        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            raise ValueError(
                f"{field_name} must be valid JSON or Python literal. "
                f"Received: {value[:50]}{'...' if len(value) > 50 else ''}"
            ) from None

        if not isinstance(parsed, list):
            raise ValueError(
                f"{field_name} must be a list or valid JSON/Python literal "
                f"representing a list. Got type: {type(parsed).__name__}"
            )
        return parsed
    raise ValueError(
        f"{field_name} must be a list or JSON string, got {type(value).__name__}"
    )


class Thought(BaseModel):
    """Model: Represents a single thought in sequential thinking process"""

    model_config = {"strict": True}

    thought: Annotated[
        str, Field(min_length=1, description="Your current thinking step")
    ]
    thought_number: Annotated[
        int,
        Field(
            ge=1, description="Current thought number (numeric value, e.g., 1, 2, 3)"
        ),
    ]
    total_thoughts: Annotated[
        int,
        Field(ge=1, description="Estimated total thoughts needed (numeric value)"),
    ]
    next_thought_needed: Annotated[
        bool, Field(description="Whether another thought step is needed")
    ]
    is_revision: Annotated[
        bool | None, Field(None, description="Whether this revises previous thinking")
    ] = None
    revises_thought: Annotated[
        int | None, Field(None, ge=1, description="Which thought is being reconsidered")
    ] = None
    branch_from_thought: Annotated[
        int | None, Field(None, ge=1, description="Branching point thought number")
    ] = None
    branch_id: Annotated[str | None, Field(None, description="Branch identifier")] = (
        None
    )
    needs_more_thoughts: Annotated[
        bool | None, Field(None, description="If more thoughts are needed")
    ] = None
    confidence: Annotated[
        float | None,
        Field(None, ge=0.0, le=1.0, description="Confidence level (0.0-1.0)"),
    ] = None
    uncertainty_notes: Annotated[
        str | None, Field(None, description="Explanation for uncertainty")
    ] = None
    outcome: Annotated[
        str | None, Field(None, description="What was achieved or expected")
    ] = None
    assumptions: Annotated[
        list[Assumption] | None,
        Field(None, description="Assumptions made in this thought"),
    ] = None
    depends_on_assumptions: Annotated[
        list[str] | None,
        Field(None, description="Assumption IDs this thought depends on"),
    ] = None
    invalidates_assumptions: Annotated[
        list[str] | None, Field(None, description="Assumption IDs proven false")
    ] = None

    @field_validator("thought")
    @classmethod
    def validate_thought_not_empty(cls, v: str) -> str:
        return _validate_thought_not_empty(v)

    @field_validator("assumptions", mode="before")
    @classmethod
    def validate_assumptions(cls, v: Any) -> Any:
        return _parse_json_list(v, "assumptions")

    @field_validator("depends_on_assumptions", mode="before")
    @classmethod
    def validate_depends_on_assumptions(cls, v: Any) -> Any:
        return _parse_json_list(v, "depends_on_assumptions")

    @field_validator("invalidates_assumptions", mode="before")
    @classmethod
    def validate_invalidates_assumptions(cls, v: Any) -> Any:
        return _parse_json_list(v, "invalidates_assumptions")

    @property
    def is_branch(self) -> bool:
        return bool(self.branch_from_thought and self.branch_id)

    @property
    def is_final(self) -> bool:
        return not self.next_thought_needed

    def auto_adjust_total(self) -> None:
        self.total_thoughts = max(self.thought_number, self.total_thoughts)

    def validate_references(self, existing_thought_numbers: set[int]) -> None:
        if (
            self.is_revision
            and self.revises_thought is not None
            and self.revises_thought not in existing_thought_numbers
        ):
            if not existing_thought_numbers:
                raise ValueError(
                    f"Cannot revise thought {self.revises_thought}: "
                    "no thoughts exist in this session yet. "
                    "To continue an existing session, pass the session_id parameter."
                )
            available = sorted(existing_thought_numbers)
            raise ValueError(
                f"Cannot revise thought {self.revises_thought}: "
                f"thought not found in this session. Available thoughts: {available}"
            )

        if (
            self.is_branch
            and self.branch_from_thought is not None
            and self.branch_from_thought not in existing_thought_numbers
        ):
            if not existing_thought_numbers:
                raise ValueError(
                    f"Cannot branch from thought {self.branch_from_thought}: "
                    "no thoughts exist in this session yet. "
                    "To continue an existing session, pass the session_id parameter."
                )
            available = sorted(existing_thought_numbers)
            raise ValueError(
                f"Cannot branch from thought {self.branch_from_thought}: "
                f"thought not found in this session. Available thoughts: {available}"
            )


class ThoughtRequest(BaseModel):
    """Model: Request model for ultrathink tool"""

    model_config = {"strict": True}

    thought: Annotated[
        str, Field(min_length=1, description="Your current thinking step")
    ]
    total_thoughts: Annotated[
        int, Field(ge=1, description="Estimated total thoughts needed")
    ]
    next_thought_needed: Annotated[
        bool | None, Field(None, description="Whether another thought step is needed")
    ] = None
    thought_number: Annotated[
        int | None, Field(None, ge=1, description="Current thought number")
    ] = None
    session_id: Annotated[str | None, Field(None, description="Session identifier")] = (
        None
    )
    is_revision: Annotated[
        bool | None, Field(None, description="Whether this revises previous thinking")
    ] = None
    revises_thought: Annotated[
        int | None, Field(None, ge=1, description="Which thought is being reconsidered")
    ] = None
    branch_from_thought: Annotated[
        int | None, Field(None, ge=1, description="Branching point thought number")
    ] = None
    branch_id: Annotated[str | None, Field(None, description="Branch identifier")] = (
        None
    )
    needs_more_thoughts: Annotated[
        bool | None, Field(None, description="If more thoughts are needed")
    ] = None
    confidence: Annotated[
        float | None,
        Field(None, ge=0.0, le=1.0, description="Confidence level (0.0-1.0)"),
    ] = None
    uncertainty_notes: Annotated[
        str | None, Field(None, description="Explanation for uncertainty")
    ] = None
    outcome: Annotated[
        str | None, Field(None, description="What was achieved or expected")
    ] = None
    assumptions: Annotated[
        list[Assumption] | None,
        Field(None, description="Assumptions made in this thought"),
    ] = None
    depends_on_assumptions: Annotated[
        list[str] | None,
        Field(None, description="Assumption IDs this thought depends on"),
    ] = None
    invalidates_assumptions: Annotated[
        list[str] | None, Field(None, description="Assumption IDs proven false")
    ] = None

    @field_validator("thought")
    @classmethod
    def validate_thought_not_empty(cls, v: str) -> str:
        return _validate_thought_not_empty(v)

    @field_validator("assumptions", mode="before")
    @classmethod
    def validate_assumptions(cls, v: Any) -> Any:
        return _parse_json_list(v, "assumptions")

    @field_validator("depends_on_assumptions", mode="before")
    @classmethod
    def validate_depends_on_assumptions(cls, v: Any) -> Any:
        return _parse_json_list(v, "depends_on_assumptions")

    @field_validator("invalidates_assumptions", mode="before")
    @classmethod
    def validate_invalidates_assumptions(cls, v: Any) -> Any:
        return _parse_json_list(v, "invalidates_assumptions")


class ThoughtResponse(BaseModel):
    """Model: Response model for ultrathink tool"""

    model_config = {"strict": True}

    session_id: Annotated[str, Field(description="Session identifier for continuation")]
    thought_number: Annotated[
        int, Field(ge=1, description="Current thought number in sequence")
    ]
    total_thoughts: Annotated[
        int, Field(ge=1, description="Total number of thoughts planned")
    ]
    next_thought_needed: Annotated[
        bool, Field(description="Whether another thought step is needed")
    ]
    branches: Annotated[
        list[str], Field(description="List of active branch identifiers")
    ]
    thought_history_length: Annotated[
        int, Field(ge=0, description="Total number of thoughts processed")
    ]
    confidence: Annotated[
        float | None, Field(None, ge=0.0, le=1.0, description="Confidence level")
    ] = None
    uncertainty_notes: Annotated[
        str | None, Field(None, description="Explanation for uncertainty")
    ] = None
    outcome: Annotated[
        str | None, Field(None, description="What was achieved or expected")
    ] = None
    all_assumptions: Annotated[
        dict[str, Assumption], Field(description="All assumptions tracked")
    ] = {}
    risky_assumptions: Annotated[
        list[str], Field(description="IDs of risky assumptions")
    ] = []
    falsified_assumptions: Annotated[
        list[str], Field(description="IDs of falsified assumptions")
    ] = []
    unresolved_references: Annotated[
        list[str], Field(description="IDs of unresolved cross-session references")
    ] = []
    cross_session_warnings: Annotated[
        list[str], Field(description="Warnings from cross-session operations")
    ] = []


# =============================================================================
# Session
# =============================================================================


def _parse_assumption_id(assumption_id: str) -> tuple[str | None, str]:
    """Parse scoped assumption ID into (session_id, local_id)"""
    if ":" in assumption_id:
        parts = assumption_id.split(":", 1)
        return parts[0], parts[1]
    return None, assumption_id


class ThinkingSession:
    """Model: Manages the sequential thinking session"""

    def __init__(self) -> None:
        self._thoughts: list[Thought] = []
        self._branches: dict[str, list[Thought]] = {}
        self._assumptions: dict[str, Assumption] = {}
        self._unresolved_refs: list[str] = []
        self._cross_session_warnings: list[str] = []

    @property
    def thought_count(self) -> int:
        return len(self._thoughts)

    @property
    def branch_ids(self) -> list[str]:
        return list(self._branches.keys())

    @property
    def all_assumptions(self) -> dict[str, Assumption]:
        return self._assumptions.copy()

    @property
    def risky_assumptions(self) -> list[str]:
        return [aid for aid, a in self._assumptions.items() if a.is_risky]

    @property
    def falsified_assumptions(self) -> list[str]:
        return [aid for aid, a in self._assumptions.items() if a.is_falsified]

    @property
    def unresolved_references(self) -> list[str]:
        return self._unresolved_refs.copy()

    @property
    def cross_session_warnings(self) -> list[str]:
        return self._cross_session_warnings.copy()

    def add_thought(  # noqa: PLR0912
        self, thought: Thought, validated_cross_session_refs: list[str] | None = None
    ) -> None:
        thought.auto_adjust_total()
        existing_numbers = {t.thought_number for t in self._thoughts}
        thought.validate_references(existing_numbers)

        if thought.depends_on_assumptions:
            for assumption_id in thought.depends_on_assumptions:
                session_id, _ = _parse_assumption_id(assumption_id)
                if session_id is None:
                    if assumption_id not in self._assumptions:
                        available = sorted(self._assumptions.keys())
                        avail_str = str(available) if available else "none"
                        raise ValueError(
                            f"Cannot depend on assumption {assumption_id}: "
                            f"assumption not found. Available: {avail_str}"
                        )
                elif (
                    validated_cross_session_refs
                    and assumption_id in validated_cross_session_refs
                ):
                    continue
                elif assumption_id not in self._unresolved_refs:
                    self._unresolved_refs.append(assumption_id)

        if thought.assumptions:
            for assumption in thought.assumptions:
                if assumption.id in self._assumptions:
                    existing = self._assumptions[assumption.id]
                    if existing.text != assumption.text:
                        raise ValueError(
                            f"Cannot update assumption {assumption.id}: text mismatch. "
                            f"Existing: '{existing.text}', New: '{assumption.text}'. "
                            f"Core assumption fields (text, critical) are immutable."
                        )
                    if existing.critical != assumption.critical:
                        raise ValueError(
                            f"Cannot update assumption {assumption.id}: "
                            f"critical flag mismatch. Existing: {existing.critical}, "
                            f"New: {assumption.critical}. "
                            "Core fields (text, critical) are immutable."
                        )
                    existing.confidence = assumption.confidence
                    existing.verifiable = assumption.verifiable
                    existing.evidence = assumption.evidence
                    existing.verification_status = assumption.verification_status
                else:
                    self._assumptions[assumption.id] = assumption

        if thought.invalidates_assumptions:
            for assumption_id in thought.invalidates_assumptions:
                session_id, _ = _parse_assumption_id(assumption_id)
                if session_id is None:
                    if assumption_id not in self._assumptions:
                        available = sorted(self._assumptions.keys())
                        avail_str = str(available) if available else "none"
                        raise ValueError(
                            f"Cannot invalidate assumption {assumption_id}: "
                            f"assumption not found. Available: {avail_str}"
                        )
                    self._assumptions[
                        assumption_id
                    ].verification_status = "verified_false"
                else:
                    warning = (
                        f"Cannot invalidate cross-session assumption "
                        f"{assumption_id}: cross-session invalidation not supported"
                    )
                    self._cross_session_warnings.append(warning)

        self._thoughts.append(thought)

        if thought.is_branch and thought.branch_id is not None:
            if thought.branch_id not in self._branches:
                self._branches[thought.branch_id] = []
            self._branches[thought.branch_id].append(thought)


# =============================================================================
# Session Storage
# =============================================================================


def _get_sessions_dir() -> Path:
    """Get the sessions directory path, create if not exists"""
    sessions_dir = Path(tempfile.gettempdir()) / "ultrathink" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


_SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def _validate_session_id(session_id: str) -> None:
    """Validate session ID to prevent path traversal attacks"""
    if not session_id:
        raise ValueError("Session ID cannot be empty")
    if len(session_id) > 128:
        raise ValueError("Session ID too long (max 128 characters)")
    if not _SESSION_ID_PATTERN.match(session_id):
        raise ValueError(
            f"Invalid session ID '{session_id}': must contain only "
            "alphanumeric characters, hyphens, and underscores"
        )


def _session_file_path(session_id: str) -> Path:
    _validate_session_id(session_id)
    return _get_sessions_dir() / f"{session_id}.json"


def save_session(session_id: str, session: ThinkingSession) -> None:
    data = {
        "thoughts": [
            {
                "thought": t.thought,
                "thought_number": t.thought_number,
                "total_thoughts": t.total_thoughts,
                "next_thought_needed": t.next_thought_needed,
                "is_revision": t.is_revision,
                "revises_thought": t.revises_thought,
                "branch_from_thought": t.branch_from_thought,
                "branch_id": t.branch_id,
                "needs_more_thoughts": t.needs_more_thoughts,
                "confidence": t.confidence,
                "uncertainty_notes": t.uncertainty_notes,
                "outcome": t.outcome,
                "assumptions": [a.model_dump() for a in t.assumptions]
                if t.assumptions
                else None,
                "depends_on_assumptions": t.depends_on_assumptions,
                "invalidates_assumptions": t.invalidates_assumptions,
            }
            for t in session._thoughts
        ],
        "assumptions": {aid: a.model_dump() for aid, a in session._assumptions.items()},
        "branches": {
            bid: [t.thought_number for t in thoughts]
            for bid, thoughts in session._branches.items()
        },
        "unresolved_refs": session._unresolved_refs,
        "cross_session_warnings": session._cross_session_warnings,
    }
    with _session_file_path(session_id).open("w") as f:
        json.dump(data, f, indent=2)


def load_session(session_id: str) -> ThinkingSession | None:
    file_path = _session_file_path(session_id)
    if not file_path.exists():
        return None

    try:
        with file_path.open() as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        # Corrupted or unreadable session file - treat as non-existent
        return None

    try:
        session = ThinkingSession()

        for aid, assumption_data in data.get("assumptions", {}).items():
            session._assumptions[aid] = Assumption(**assumption_data)

        for thought_data in data.get("thoughts", []):
            if thought_data.get("assumptions"):
                thought_data["assumptions"] = [
                    Assumption(**a) for a in thought_data["assumptions"]
                ]
            thought = Thought(**thought_data)
            session._thoughts.append(thought)
            if thought.is_branch and thought.branch_id:
                if thought.branch_id not in session._branches:
                    session._branches[thought.branch_id] = []
                session._branches[thought.branch_id].append(thought)

        session._unresolved_refs = data.get("unresolved_refs", [])
        session._cross_session_warnings = data.get("cross_session_warnings", [])

        return session
    except (KeyError, TypeError, ValidationError, AttributeError):
        # Invalid session data structure - treat as non-existent
        return None


# =============================================================================
# Service
# =============================================================================


class UltraThinkService:
    """Service: Orchestrates the sequential thinking process"""

    def __init__(self) -> None:
        self._sessions: dict[str, ThinkingSession] = {}

    def _get_or_create_session(
        self, session_id: str | None
    ) -> tuple[str, ThinkingSession]:
        if session_id is None:
            new_id = str(uuid.uuid4())
            session = ThinkingSession()
            self._sessions[new_id] = session
            return new_id, session

        if session_id in self._sessions:
            return session_id, self._sessions[session_id]

        loaded_session = load_session(session_id)
        if loaded_session is not None:
            self._sessions[session_id] = loaded_session
            return session_id, loaded_session

        new_session = ThinkingSession()
        self._sessions[session_id] = new_session
        return session_id, new_session

    def _resolve_cross_session_assumption(
        self, scoped_id: str, _current_session_id: str
    ) -> tuple[str | None, bool]:
        target_session_id, local_id = _parse_assumption_id(scoped_id)

        if target_session_id is None:
            return scoped_id, True

        if target_session_id not in self._sessions:
            target_session = load_session(target_session_id)
            if target_session is not None:
                self._sessions[target_session_id] = target_session
            else:
                return None, False

        target_session = self._sessions[target_session_id]
        if local_id not in target_session.all_assumptions:
            return None, False

        return local_id, True

    def process_thought(self, request: ThoughtRequest) -> ThoughtResponse:
        session_id, session = self._get_or_create_session(request.session_id)

        if request.thought_number is None:
            thought_number = session.thought_count + 1
        else:
            thought_number = request.thought_number

        if request.next_thought_needed is None:
            next_thought_needed = thought_number < request.total_thoughts
        else:
            next_thought_needed = request.next_thought_needed

        validated_cross_session_refs: list[str] = []
        if request.depends_on_assumptions:
            for assumption_id in request.depends_on_assumptions:
                if ":" in assumption_id:
                    _, was_resolved = self._resolve_cross_session_assumption(
                        assumption_id, session_id
                    )
                    if was_resolved:
                        validated_cross_session_refs.append(assumption_id)

        thought_data = request.model_dump(exclude={"session_id"})
        thought_data["thought_number"] = thought_number
        thought_data["next_thought_needed"] = next_thought_needed
        thought = Thought(**thought_data)

        session.add_thought(thought, validated_cross_session_refs)
        save_session(session_id, session)

        return ThoughtResponse(
            session_id=session_id,
            thought_number=thought.thought_number,
            total_thoughts=thought.total_thoughts,
            next_thought_needed=thought.next_thought_needed,
            branches=session.branch_ids,
            thought_history_length=session.thought_count,
            confidence=thought.confidence,
            uncertainty_notes=thought.uncertainty_notes,
            outcome=thought.outcome,
            all_assumptions=session.all_assumptions,
            risky_assumptions=session.risky_assumptions,
            falsified_assumptions=session.falsified_assumptions,
            unresolved_references=session.unresolved_references,
            cross_session_warnings=session.cross_session_warnings,
        )


# =============================================================================
# CLI
# =============================================================================

app = typer.Typer(
    name="ultrathink",
    help="CLI for dynamic problem-solving through sequential thoughts.",
    add_completion=False,
    no_args_is_help=True,
)

_service = UltraThinkService()


def version_callback(value: bool) -> None:
    if value:
        print(json.dumps({"version": __version__}))
        raise typer.Exit()


def format_response_json(response: ThoughtResponse) -> str:
    return response.model_dump_json(indent=2)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    thought: Annotated[
        str | None,
        typer.Option(
            "--thought",
            "-t",
            help="Your current thinking step (required).",
            show_default=False,
        ),
    ] = None,
    total: Annotated[
        int | None,
        typer.Option(
            "--total",
            "-n",
            help="Total thoughts estimated/needed (required).",
            show_default=False,
            min=1,
        ),
    ] = None,
    session_id: Annotated[
        str | None,
        typer.Option(
            "--session-id",
            "-s",
            help="Session ID for continuity (omit to create new session).",
        ),
    ] = None,
    thought_number: Annotated[
        int | None,
        typer.Option(
            "--thought-number",
            help="Override auto-numbering (auto-assigned if omitted).",
            min=1,
        ),
    ] = None,
    confidence: Annotated[
        float | None,
        typer.Option(
            "--confidence", "-c", help="Confidence level (0.0-1.0).", min=0.0, max=1.0
        ),
    ] = None,
    is_revision: Annotated[
        bool | None,
        typer.Option(
            "--is-revision/--no-revision", help="Mark this thought as a revision."
        ),
    ] = None,
    revises_thought: Annotated[
        int | None,
        typer.Option(
            "--revises",
            help="Thought number being revised (use with --is-revision).",
            min=1,
        ),
    ] = None,
    branch_from_thought: Annotated[
        int | None,
        typer.Option("--branch-from", help="Thought number to branch from.", min=1),
    ] = None,
    branch_id: Annotated[
        str | None,
        typer.Option(
            "--branch-id", help="Identifier for the branch (use with --branch-from)."
        ),
    ] = None,
    uncertainty_notes: Annotated[
        str | None,
        typer.Option("--uncertainty-notes", help="Explanation for doubts or concerns."),
    ] = None,
    outcome: Annotated[
        str | None,
        typer.Option("--outcome", help="What was achieved or expected."),
    ] = None,
    assumptions: Annotated[
        str | None,
        typer.Option("--assumptions", help="JSON array of assumption objects."),
    ] = None,
    depends_on: Annotated[
        str | None,
        typer.Option(
            "--depends-on", help="JSON array of assumption IDs this thought depends on."
        ),
    ] = None,
    invalidates: Annotated[
        str | None,
        typer.Option(
            "--invalidates", help="JSON array of assumption IDs proven false."
        ),
    ] = None,
    needs_more: Annotated[
        bool | None,
        typer.Option(
            "--needs-more/--no-needs-more",
            help="Flag if more thoughts are needed beyond estimate.",
        ),
    ] = None,
    next_needed: Annotated[
        bool | None,
        typer.Option(
            "--next-needed/--no-next-needed",
            help="Override auto-assignment of next_thought_needed.",
        ),
    ] = None,
    _version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """
    Process a thinking step in a sequential problem-solving session.

    Output is always JSON.

    \b
    Examples:
        # Start a new thinking session
        uv run ultrathink.py --thought "Analyze this..." --total 5

        # Continue an existing session
        uv run ultrathink.py -t "Building on analysis..." -n 5 -s <sid>

        # Add a thought with confidence
        uv run ultrathink.py -t "Answer is X" -n 3 -c 0.8 -s <sid>

        # Create a revision
        uv run ultrathink.py -t "Revising..." -n 3 --is-revision --revises 2

        # Create a branch
        uv run ultrathink.py -t "Alternative..." -n 3 --branch-from 1 --branch-id alt

        # Add assumptions
        uv run ultrathink.py -t "Assuming..." -n 3 \
            --assumptions '[{"id":"A1","text":"X is true","critical":true}]'
    """
    if thought is None or total is None:
        if ctx.invoked_subcommand is None:
            print(ctx.get_help())
            raise typer.Exit()
        return

    try:
        request = ThoughtRequest(
            thought=thought,
            total_thoughts=total,
            session_id=session_id,
            thought_number=thought_number,
            confidence=confidence,
            is_revision=is_revision,
            revises_thought=revises_thought,
            branch_from_thought=branch_from_thought,
            branch_id=branch_id,
            uncertainty_notes=uncertainty_notes,
            outcome=outcome,
            assumptions=assumptions,  # type: ignore[arg-type]
            depends_on_assumptions=depends_on,  # type: ignore[arg-type]
            invalidates_assumptions=invalidates,  # type: ignore[arg-type]
            needs_more_thoughts=needs_more,
            next_thought_needed=next_needed,
        )

        response = _service.process_thought(request)
        print(format_response_json(response))

    except ValidationError as e:
        errors = [{"loc": list(err["loc"]), "msg": err["msg"]} for err in e.errors()]
        print(
            json.dumps({"error": "validation_error", "details": errors}, indent=2),
            file=sys.stderr,
        )
        raise typer.Exit(code=1) from None
    except ValueError as e:
        print(
            json.dumps({"error": "value_error", "message": str(e)}, indent=2),
            file=sys.stderr,
        )
        raise typer.Exit(code=1) from None
    except Exception as e:
        print(
            json.dumps({"error": "unexpected_error", "message": str(e)}, indent=2),
            file=sys.stderr,
        )
        raise typer.Exit(code=1) from None


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
