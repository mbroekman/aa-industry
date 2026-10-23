"""
Skill-gated job eligibility service.

Determines whether a character/user actually has the EVE Online skills required to run a
given manufacturing/reaction job, independent of slot availability. Most blueprints (T1/T2
ships, modules, ammo, drones) have no hard skill gate at all - only capitals, T3 strategic
cruiser hulls/subsystems, and advanced reaction formulas carry a genuine "cannot start the
job without this skill at this level" requirement. That requirement data is sourced from
django-eveuniverse's EveIndustryActivitySkill (EVE SDE - already populated, no new ESI sync
needed). Character skill levels are fetched live via the same raw-ESI anti-304 pattern
slot_service.py already uses for its 6 slot-count skills - this module owns that fetch and
returns the *full* skill dict, so slot_service and this module share one ESI call per
character instead of each doing their own.
"""

# Standard Library
import logging
from typing import Any

# Django
from django.contrib.auth.models import User
from django.core.cache import cache

# Alliance Auth
from esi.exceptions import HTTPNotModified
from esi.models import Token

from ..tasks.utils import esi

logger = logging.getLogger(__name__)

CACHE_TTL_CHAR_SKILLS = 86400  # 24 hours
CACHE_TTL_FALLBACK = 300  # 5 minutes on transient failure or missing token
CACHE_TTL_REQUIRED_SKILLS = 86400  # 24 hours - EVE SDE skill requirements barely change

# Roman numerals for human-readable skill level display (EVE skills never exceed level 5)
_ROMAN_LEVELS = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}


def get_character_skill_levels(character_id: int) -> dict[int, int]:
    """
    Full map of {skill_type_id: trained_level} for a character, fetched live via ESI.

    Cached 24h on success, 5 min on missing token/transient failure (empty dict). An empty
    dict means "couldn't verify" - callers should treat that as "don't block" (fail open),
    the same philosophy slot_service already applies by falling back to a safe default
    slot count rather than blocking production when ESI is flaky.
    """
    cache_key = f"industry_reforged_char_skills_{character_id}"
    cached = cache.get(cache_key)
    if cached is not None and isinstance(cached, dict):
        return cached

    token = Token.objects.filter(
        character_id=character_id, scopes__name="esi-skills.read_skills.v1"
    ).first()

    if not token:
        cache.set(cache_key, {}, timeout=CACHE_TTL_FALLBACK)
        return {}

    try:
        skills: dict[int, int] = {}
        # Direct ESI skills fetch with the OAuth bearer token to bypass django-esi's
        # bravado 304 cache issues (same technique as slot_service.py).
        try:
            import requests

            access_token = token.valid_access_token()
            headers = {
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "AA-Industry Skill Service",
            }
            url = f"https://esi.evetech.net/latest/characters/{character_id}/skills/"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                for s in resp.json().get("skills", []):
                    skills[s.get("skill_id", 0)] = s.get("active_skill_level", 0)
        except Exception:  # noqa: BLE001
            skills = {}

        if not skills:
            res = esi.client.Skills.GetCharactersCharacterIdSkills(
                character_id=character_id,
                token=token,
            ).results()
            for s in getattr(res, "skills", []):
                skills[getattr(s, "skill_id", 0)] = getattr(s, "active_skill_level", 0)

        cache.set(cache_key, skills, timeout=CACHE_TTL_CHAR_SKILLS)
        return skills

    except HTTPNotModified:
        return {}
    except Exception as e:  # noqa: BLE001
        logger.warning(
            f"Failed to fetch live skills from ESI for character {character_id}: {e}"
        )
        cache.set(cache_key, {}, timeout=CACHE_TTL_FALLBACK)
        return {}


def get_user_skill_levels(user: User) -> dict[int, int]:
    """Max trained level per skill across every character the user owns."""
    if not user or not user.is_authenticated:
        return {}

    merged: dict[int, int] = {}
    for ownership in user.character_ownerships.select_related("character").all():
        character = getattr(ownership, "character", None)
        if not character:
            continue
        for skill_id, level in get_character_skill_levels(
            character.character_id
        ).items():
            merged[skill_id] = max(merged.get(skill_id, 0), level)
    return merged


def get_required_skills(item_type_id: int, activity_id: int) -> list[dict[str, Any]]:
    """
    Hard skill requirements (not slot-count modifiers) to run a job for this item/activity.

    Sourced from django-eveuniverse's EveIndustryActivitySkill (EVE SDE). Cached 24h since
    SDE data barely changes. Returns an empty list for the vast majority of items, which
    genuinely have no hard skill gate - that's expected, not a missing-data signal.

    Returns: [{"skill_type_id": int, "skill_name": str, "level": int}, ...]
    """
    cache_key = f"aa_industry_required_skills_{item_type_id}_{activity_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Third Party
    from eveuniverse.models import EveIndustryActivityProduct, EveIndustryActivitySkill

    result: list[dict[str, Any]] = []
    try:
        bp_prod = EveIndustryActivityProduct.objects.filter(
            product_eve_type_id=item_type_id,
            activity_id=activity_id,
            eve_type__published=True,
        ).first()
        if bp_prod:
            for skill in EveIndustryActivitySkill.objects.filter(
                eve_type_id=bp_prod.eve_type_id,
                activity_id=activity_id,
            ).select_related("skill_eve_type"):
                result.append(
                    {
                        "skill_type_id": skill.skill_eve_type_id,
                        "skill_name": skill.skill_eve_type.name,
                        "level": skill.level,
                    }
                )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Error fetching required skills for type %s (act %s): %s",
            item_type_id,
            activity_id,
            exc,
        )

    cache.set(cache_key, result, timeout=CACHE_TTL_REQUIRED_SKILLS)
    return result


def _missing_for(
    skill_levels: dict[int, int], required: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    return [
        {
            "skill_name": req["skill_name"],
            "required_level": req["level"],
            "owned_level": skill_levels.get(req["skill_type_id"], 0),
        }
        for req in required
        if skill_levels.get(req["skill_type_id"], 0) < req["level"]
    ]


def check_user_eligibility(
    user: User, item_type_id: int, activity_id: int
) -> tuple[bool, list[dict[str, Any]]]:
    """Can ANY character the user owns run this job? (Job Market visibility check.)"""
    required = get_required_skills(item_type_id, activity_id)
    if not required:
        return True, []
    missing = _missing_for(get_user_skill_levels(user), required)
    return not missing, missing


def check_character_eligibility(
    character_id: int, item_type_id: int, activity_id: int
) -> tuple[bool, list[dict[str, Any]]]:
    """Can this SPECIFIC character run this job? (Claim-time hard-stop.)"""
    required = get_required_skills(item_type_id, activity_id)
    if not required:
        return True, []
    missing = _missing_for(get_character_skill_levels(character_id), required)
    return not missing, missing


def missing_skills_text(missing: list[dict[str, Any]]) -> str:
    """Human-readable 'Requires: X V, Y III' string for tooltips/error messages."""
    if not missing:
        return ""
    parts = [
        f"{m['skill_name']} {_ROMAN_LEVELS.get(m['required_level'], m['required_level'])}"
        for m in missing
    ]
    return "Requires: " + ", ".join(parts)
