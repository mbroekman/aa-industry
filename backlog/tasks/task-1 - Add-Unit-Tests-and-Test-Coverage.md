______________________________________________________________________

## id: TASK-1 title: Add Unit Tests and Test Coverage status: Done assignee: [] created_date: '2026-07-29 16:32' labels: [] dependencies: [] type: task ordinal: 5000

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

The project currently has minimal test coverage. We need to build a solid foundation of unit tests to prevent regressions, particularly for complex logic like pricing calculations, order management, and ESI synchronization.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 Set up pytest and pytest-django
- [ ] #2 Set up factory_boy
- [ ] #3 Add tests for core models
- [ ] #4 Add tests for complex utility functions
- [ ] #5 Add tests for Celery tasks
- [ ] #6 Integrate coverage reporting into CI checks
- [ ] #7 Coverage report shows at least 50% coverage
- [ ] #8 Tests pass locally and in CI pipeline

<!-- AC:END -->
