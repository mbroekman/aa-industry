# Django
from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def eve_isk(value):
    """
    Formats a number as EVE ISK with a tooltip showing the abbreviation (K, M, B, T).
    Example: 14000000000 -> <span title="14.00B ISK">14,000,000,000 ISK</span>
    """
    try:
        val = float(value)
    except (ValueError, TypeError):
        return value

    if val >= 1_000_000_000_000:
        abbrev = f"{val / 1_000_000_000_000:.2f}T ISK"
    elif val >= 1_000_000_000:
        abbrev = f"{val / 1_000_000_000:.2f}B ISK"
    elif val >= 1_000_000:
        abbrev = f"{val / 1_000_000:.2f}M ISK"
    elif val >= 1_000:
        abbrev = f"{val / 1_000:.2f}K ISK"
    else:
        abbrev = f"{val:.2f} ISK"

    # Format number with commas
    formatted_val = f"{intcomma(round(val, 2))} ISK"

    # Return HTML span with bootstrap tooltip
    return mark_safe(
        f'<span data-bs-toggle="tooltip" data-bs-placement="top" title="{abbrev}" style="text-decoration: underline dotted; cursor: help;">{formatted_val}</span>'
    )


@register.filter
def eve_isk_short(value):
    """
    Formats a number as EVE ISK showing the abbreviation directly, with a tooltip showing the full number.
    Example: 14000000000 -> <span title="14,000,000,000 ISK">14.00B ISK</span>
    """
    try:
        val = float(value)
    except (ValueError, TypeError):
        return value

    if val >= 1_000_000_000_000:
        abbrev = f"{val / 1_000_000_000_000:.2f}T ISK"
    elif val >= 1_000_000_000:
        abbrev = f"{val / 1_000_000_000:.2f}B ISK"
    elif val >= 1_000_000:
        abbrev = f"{val / 1_000_000:.2f}M ISK"
    elif val >= 1_000:
        abbrev = f"{val / 1_000:.2f}K ISK"
    else:
        abbrev = f"{val:.2f} ISK"

    # Format number with commas
    full_val = f"{intcomma(round(val, 2))} ISK"

    return mark_safe(
        f'<span data-bs-toggle="tooltip" data-bs-placement="top" title="{full_val}" style="text-decoration: underline dotted; cursor: help;">{abbrev}</span>'
    )
