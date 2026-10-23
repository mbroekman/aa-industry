"""
Live Industry Slot Detection Service without Corptools dependency.
Determines total, active, and available manufacturing, reactions, and science slots
for an Alliance Auth user across all their owned characters.
"""

# Standard Library
import logging
from typing import Any

# Django
from django.contrib.auth.models import User
from django.core.cache import cache

from ..models import CharacterIndustryJob
from .skill_service import get_character_skill_levels, get_user_industry_characters

logger = logging.getLogger(__name__)

# EVE Online Industry Skill Type IDs
# Manufacturing:
# - 3387: Mass Production (+1 slot/level)
# - 24624: Advanced Mass Production (+1 slot/level)
SKILL_MASS_PRODUCTION = 3387
SKILL_ADV_MASS_PRODUCTION = 24624

# Reactions:
# - 45749: Mass Reactions (+1 slot/level)
# - 45750: Advanced Mass Reactions (+1 slot/level)
SKILL_MASS_REACTIONS = 45749
SKILL_ADV_MASS_REACTIONS = 45750

# Science / Research / Copying / Invention:
# - 3406: Laboratory Operation (+1 slot/level)
# - 24625: Advanced Laboratory Operation (+1 slot/level)
SKILL_LAB_OPERATION = 3406
SKILL_ADV_LAB_OPERATION = 24625

CACHE_TTL_CHAR_SLOTS = 86400  # 24 hours
CACHE_TTL_FALLBACK = 300  # 5 minutes on transient failure or missing token


def get_character_industry_slots(character_id: int) -> dict[str, int]:
    """
    Retrieve max industry slots for a specific character based on live ESI skills.
    Results are cached for 24 hours in Django cache.

    Returns:
        dict: {
            "mfg_slots": int (1 to 11),
            "reaction_slots": int (1 to 11),
            "science_slots": int (1 to 11)
        }
    """
    cache_key = f"industry_reforged_char_slots_{character_id}"
    cached = cache.get(cache_key)
    if cached is not None and isinstance(cached, dict):
        return cached

    # Safe default: in EVE Online every character has at least 1 base slot per activity
    default_slots = {
        "mfg_slots": 1,
        "reaction_slots": 1,
        "science_slots": 1,
    }

    # Shared with skill_service.py's eligibility checks - one raw-ESI anti-304 fetch per
    # character serves both slot counting and skill-gated job eligibility.
    skills = get_character_skill_levels(character_id)
    if not skills:
        cache.set(cache_key, default_slots, timeout=CACHE_TTL_FALLBACK)
        return default_slots

    mfg = (
        1
        + skills.get(SKILL_MASS_PRODUCTION, 0)
        + skills.get(SKILL_ADV_MASS_PRODUCTION, 0)
    )
    reactions = (
        1
        + skills.get(SKILL_MASS_REACTIONS, 0)
        + skills.get(SKILL_ADV_MASS_REACTIONS, 0)
    )
    science = (
        1 + skills.get(SKILL_LAB_OPERATION, 0) + skills.get(SKILL_ADV_LAB_OPERATION, 0)
    )

    slots = {
        "mfg_slots": min(max(mfg, 1), 11),
        "reaction_slots": min(max(reactions, 1), 11),
        "science_slots": min(max(science, 1), 11),
    }
    cache.set(cache_key, slots, timeout=CACHE_TTL_CHAR_SLOTS)
    return slots


def get_user_available_slots(user: User, activity_id: int = 1) -> dict[str, Any]:
    """
    Calculates total, active, and available slots across all characters owned by the user
    without any dependency on corptools.

    Args:
        user: Django User instance
        activity_id: EVE industry activity ID (1=Manufacturing, 9/11=Reactions, 3/4/5/8=Science)

    Returns:
        dict: {
            "total_slots": int,
            "active_slots": int,
            "available_slots": int,
            "character_count": int,
            "mfg_total": int,
            "mfg_active": int,
            "mfg_available": int,
            "reaction_total": int,
            "reaction_active": int,
            "reaction_available": int,
            "characters": list of character slot dicts
        }
    """
    empty_result: dict[str, Any] = {
        "total_slots": 0,
        "active_slots": 0,
        "available_slots": 0,
        "character_count": 0,
        "mfg_total": 0,
        "mfg_active": 0,
        "mfg_available": 0,
        "reaction_total": 0,
        "reaction_active": 0,
        "reaction_available": 0,
        "characters": [],
    }

    if not user or not user.is_authenticated:
        return empty_result

    # Only characters in the same corp as the user's main - alts sitting in an
    # unrelated corp have no access to the corp's hangars/facilities and can't
    # actually execute a job here, regardless of skills or free slots.
    characters = get_user_industry_characters(user)
    char_ids = [c.character_id for c in characters]

    if not char_ids:
        return empty_result

    # Active jobs from local DB (status in active or ready)
    active_jobs = CharacterIndustryJob.objects.filter(
        character__character_id__in=char_ids,
        status__in=["active", "ready"],
    )

    mfg_active = active_jobs.filter(activity_id=1).count()
    reaction_active = active_jobs.filter(activity_id__in=[9, 11]).count()
    science_active = active_jobs.filter(activity_id__in=[3, 4, 5, 8]).count()

    mfg_total = 0
    reaction_total = 0
    science_total = 0
    char_summaries = []

    for c in characters:
        slots = get_character_industry_slots(c.character_id)
        mfg_total += slots["mfg_slots"]
        reaction_total += slots["reaction_slots"]
        science_total += slots["science_slots"]

        char_active_mfg = active_jobs.filter(
            character__character_id=c.character_id, activity_id=1
        ).count()
        char_active_rx = active_jobs.filter(
            character__character_id=c.character_id, activity_id__in=[9, 11]
        ).count()

        char_summaries.append(
            {
                "character_id": c.character_id,
                "character_name": c.character_name,
                "mfg_slots": slots["mfg_slots"],
                "reaction_slots": slots["reaction_slots"],
                "mfg_active": char_active_mfg,
                "reaction_active": char_active_rx,
                "mfg_available": max(0, slots["mfg_slots"] - char_active_mfg),
                "reaction_available": max(0, slots["reaction_slots"] - char_active_rx),
            }
        )

    mfg_available = max(0, mfg_total - mfg_active)
    reaction_available = max(0, reaction_total - reaction_active)
    science_available = max(0, science_total - science_active)

    if activity_id == 1:
        total = mfg_total
        active = mfg_active
        available = mfg_available
    elif activity_id in [9, 11]:
        total = reaction_total
        active = reaction_active
        available = reaction_available
    elif activity_id in [3, 4, 5, 8]:
        total = science_total
        active = science_active
        available = science_available
    else:
        total = mfg_total
        active = mfg_active
        available = mfg_available

    return {
        "total_slots": total,
        "active_slots": active,
        "available_slots": available,
        "character_count": len(char_ids),
        "mfg_total": mfg_total,
        "mfg_active": mfg_active,
        "mfg_available": mfg_available,
        "reaction_total": reaction_total,
        "reaction_active": reaction_active,
        "reaction_available": reaction_available,
        "science_total": science_total,
        "science_active": science_active,
        "science_available": science_available,
        "characters": char_summaries,
    }
