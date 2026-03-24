from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Skill:
    name: str
    version: str
    description: str
    activation_conditions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    content: str = ""


def _parse_skill(path: Path) -> Skill | None:
    """Parse a SKILL.md file into a Skill dataclass, returning None on failure."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        logger.warning("Could not read skill file: %s", path)
        return None

    if not raw.startswith("---"):
        logger.warning("SKILL.md missing YAML frontmatter: %s", path)
        return None

    parts = raw.split("---", 2)
    if len(parts) < 3:
        logger.warning("SKILL.md has malformed frontmatter: %s", path)
        return None

    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        logger.warning("Invalid YAML in %s: %s", path, exc)
        return None

    if not isinstance(meta, dict) or "name" not in meta:
        logger.warning("Frontmatter missing required 'name' field: %s", path)
        return None

    return Skill(
        name=meta["name"],
        version=str(meta.get("version", "0.0")),
        description=str(meta.get("description", "")),
        activation_conditions=list(meta.get("activation_conditions", [])),
        tags=list(meta.get("tags", [])),
        content=raw,
    )


def load_all_skills() -> dict[str, Skill]:
    """Discover and load every ``*/SKILL.md`` under the skills directory."""
    skills: dict[str, Skill] = {}
    for md_path in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        skill = _parse_skill(md_path)
        if skill is not None:
            skills[skill.name] = skill
            logger.info("Loaded skill: %s v%s", skill.name, skill.version)
    logger.info("Total skills loaded: %d", len(skills))
    return skills


def get_skills_for_agent(agent_name: str, skills: dict[str, Skill]) -> list[str]:
    """Return the full markdown content of every skill activated for *agent_name*."""
    return [
        skill.content
        for skill in skills.values()
        if agent_name in skill.activation_conditions
    ]
