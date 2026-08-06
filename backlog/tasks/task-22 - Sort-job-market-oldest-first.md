# Task 22: Sort Job Market Oldest First

## Status

DONE

## Description

De "Unclaimed Tasks" tabel op het Industrialist Dashboard (Job Market) moet altijd worden gesorteerd op basis van hoe lang geleden de bestelling is geplaatst (de oudste jobs bovenaan).

## Acceptance Criteria

- [x] Job market queryset (`unclaimed_tasks_qs`) sorteert oplopend op de aanmaakdatum van de order (`created_from_order__created_at`).
- [x] Wijziging getest en gecommit in `views/industrialist.py`.

## Notes

Gewijzigd in `views/industrialist.py` regel 66. `-created_from_order__created_at` veranderd naar `created_from_order__created_at`.
