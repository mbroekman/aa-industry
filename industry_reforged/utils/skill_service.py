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
    dict means "couldn't verify" and is deliberately treated as "no skills trained", so
    skill-gated claims fail closed: a member can't claim a job they can't prove they can
    build. Items with no skill requirement are unaffected.
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
            # Third Party
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
        except Exception:
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
    except Exception as e:
        logger.warning(
            f"Failed to fetch live skills from ESI for character {character_id}: {e}"
        )
        cache.set(cache_key, {}, timeout=CACHE_TTL_FALLBACK)
        return {}


def get_user_industry_characters(user: User) -> list:
    """
    Characters the user owns that are actually in the operating corp (same corp as
    their main character) - alts sitting in an unrelated corp have no access to the
    corp's hangars/facilities, so they can't execute a job here regardless of skills
    or slots, and must not be counted for either.
    """
    if not user or not user.is_authenticated:
        return []

    main_character = getattr(getattr(user, "profile", None), "main_character", None)
    if not main_character:
        return []

    return [
        ownership.character
        for ownership in user.character_ownerships.select_related("character").all()
        if ownership.character
        and ownership.character.corporation_id == main_character.corporation_id
    ]


def get_unauthed_characters(user: User) -> list:
    """
    Characters in the operating corp (see get_user_industry_characters) that have no
    esi-skills.read_skills.v1 token - these silently contribute 0 skills / base 1/1/1
    slots to the user's totals rather than their real numbers. A cheap DB existence
    check only (no live ESI call), safe to use on the claim path.
    """
    return [
        character
        for character in get_user_industry_characters(user)
        if not Token.objects.filter(
            character_id=character.character_id,
            scopes__name="esi-skills.read_skills.v1",
        ).exists()
    ]


def get_user_skill_levels(user: User) -> dict[int, int]:
    """Max trained level per skill across the user's characters in the operating corp."""
    merged: dict[int, int] = {}
    for character in get_user_industry_characters(user):
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
    except Exception as exc:
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


def check_eligibility_with_levels(
    skill_levels: dict[int, int], item_type_id: int, activity_id: int
) -> tuple[bool, list[dict[str, Any]]]:
    """Same comparison as check_user_eligibility, but takes pre-fetched skill levels so
    a caller evaluating many items for the same user in one request (e.g. the Job Market
    dashboard rendering a whole BOM tree) can fetch get_user_skill_levels() once and reuse
    it, instead of refetching per task."""
    required = get_required_skills(item_type_id, activity_id)
    if not required:
        return True, []
    missing = _missing_for(skill_levels, required)
    return not missing, missing


def check_user_eligibility(
    user: User, item_type_id: int, activity_id: int
) -> tuple[bool, list[dict[str, Any]]]:
    """Can ANY character the user owns run this job? (Job Market visibility check.)"""
    return check_eligibility_with_levels(
        get_user_skill_levels(user), item_type_id, activity_id
    )


def check_character_eligibility(
    character_id: int, item_type_id: int, activity_id: int
) -> tuple[bool, list[dict[str, Any]]]:
    """Can this SPECIFIC character run this job? (Claim-time hard-stop.)"""
    required = get_required_skills(item_type_id, activity_id)
    if not required:
        return True, []
    missing = _missing_for(get_character_skill_levels(character_id), required)
    return not missing, missing


def check_claim_tree_eligibility(
    character_id: int, task
) -> list[tuple[Any, list[dict[str, Any]]]]:
    """
    Every task a claim of `task` would assign to this character that they can't build,
    as [(task, missing_skills)]; empty means the claim may proceed.

    Mirrors the claim views' claim_recursive walk: it descends through every BOM child
    regardless of status but only claims UNCLAIMED ones, so only those are checked.
    """
    skill_levels = get_character_skill_levels(character_id)
    failures = []
    visited = set()
    stack = [task]
    while stack:
        current = stack.pop()
        if current.id in visited:
            continue
        visited.add(current.id)
        if current.status == "UNCLAIMED":
            eligible, missing = check_eligibility_with_levels(
                skill_levels, current.item_type_id, current.activity_id
            )
            if not eligible:
                failures.append((current, missing))
        stack.extend(current.bom_children.all())
    return failures


def claim_tree_failure_text(failures: list[tuple[Any, list[dict[str, Any]]]]) -> str:
    """'Item A (Requires: X V); Item B (Requires: Y III)' for claim error messages."""
    return "; ".join(
        f"{t.item_type.name} ({missing_skills_text(missing)})"
        for t, missing in failures
    )


def missing_skills_text(missing: list[dict[str, Any]]) -> str:
    """Human-readable 'Requires: X V, Y III' string for tooltips/error messages."""
    if not missing:
        return ""
    parts = [
        f"{m['skill_name']} {_ROMAN_LEVELS.get(m['required_level'], m['required_level'])}"
        for m in missing
    ]
    return "Requires: " + ", ".join(parts)
