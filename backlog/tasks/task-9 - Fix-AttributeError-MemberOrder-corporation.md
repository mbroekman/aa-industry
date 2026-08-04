______________________________________________________________________

## id: TASK-9 title: 'Fix AttributeError: MemberOrder object has no attribute corporation' status: Done assignee: [] created_date: '2026-08-03 16:35' labels: [] dependencies: [] type: bug ordinal: 10000

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

Bij het voltooien van een order ontstond een `AttributeError` op regel 38 in `notifications.py` omdat de code `order.corporation` aanriep. Een `MemberOrder` object bevat echter alleen een relatie naar `character`, en niet direct naar `corporation`.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Webhook notificaties werken zonder AttributeError door de juiste eigenschappen aan te spreken.

<!-- AC:END -->

## Implementation Notes

De webhook config filter is aangepast om te zoeken via de corporation_id van de aan de order gekoppelde character:

```python
webhook_config = CorporationWebhookConfig.objects.filter(
    corporation__corporation_id=order.character.corporation_id
).first()
```
