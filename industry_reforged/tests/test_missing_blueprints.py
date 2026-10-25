"""
Blueprint runs an order no longer needs (TASK-270): the order page's Missing Blueprints
analysis must treat blueprint runs already consumed by linked EVE jobs as built, not
as a shortage, even while the task itself isn't marked complete yet.
"""

# Third Party
import pytest

# AA Industry App
from industry_reforged.models import TaskJobLink
from industry_reforged.tests.factories import (
    CharacterIndustryJobFactory,
    CorporationIndustryJobFactory,
    EveTypeFactory,
    MemberOrderFactory,
    ProductionTaskFactory,
)
from industry_reforged.views.orders.quotes import _built_blueprint_runs

BP_ID = 990001


@pytest.fixture
def product():
    return EveTypeFactory(name="Capital Ship Maintenance Bay")


@pytest.fixture
def order():
    return MemberOrderFactory(status="ACCEPTED")


def _bp_map(product, yield_qty=1):
    return {BP_ID: [{"product_eve_type_id": product.id, "quantity": yield_qty}]}


def _link(task, job, runs):
    is_corp = job.__class__.__name__ == "CorporationIndustryJob"
    return TaskJobLink.objects.create(
        task=task,
        corporation_job=job if is_corp else None,
        character_job=None if is_corp else job,
        linked_runs=runs,
    )


@pytest.mark.django_db
class TestBuiltBlueprintRuns:
    def test_delivered_jobs_of_unfinished_task_count_as_built(self, order, product):
        """Devauth order #279: task still IN_PRODUCTION, 40 + 21 runs delivered."""
        task = ProductionTaskFactory(
            item_type=product,
            quantity=432,
            status="IN_PRODUCTION",
            created_from_order=order,
        )
        _link(task, CorporationIndustryJobFactory(status="delivered", runs=40), 40)
        _link(task, CharacterIndustryJobFactory(status="delivered", runs=21), 21)

        assert _built_blueprint_runs([order.id], _bp_map(product)) == {BP_ID: 61}

    @pytest.mark.parametrize("status", ["active", "paused", "ready"])
    def test_running_jobs_count_because_runs_are_already_consumed(
        self, order, product, status
    ):
        task = ProductionTaskFactory(
            item_type=product,
            quantity=50,
            status="IN_PRODUCTION",
            created_from_order=order,
        )
        _link(task, CorporationIndustryJobFactory(status=status, runs=20), 20)

        assert _built_blueprint_runs([order.id], _bp_map(product)) == {BP_ID: 20}

    @pytest.mark.parametrize("status", ["cancelled", "reverted"])
    def test_cancelled_jobs_do_not_count(self, order, product, status):
        task = ProductionTaskFactory(
            item_type=product,
            quantity=50,
            status="IN_PRODUCTION",
            created_from_order=order,
        )
        _link(task, CorporationIndustryJobFactory(status=status, runs=20), 20)

        assert _built_blueprint_runs([order.id], _bp_map(product)) == {BP_ID: 0}

    def test_completed_task_with_linked_job_is_not_double_counted(self, order, product):
        task = ProductionTaskFactory(
            item_type=product,
            quantity=10,
            status="COMPLETED",
            created_from_order=order,
        )
        _link(task, CorporationIndustryJobFactory(status="delivered", runs=10), 10)

        assert _built_blueprint_runs([order.id], _bp_map(product)) == {BP_ID: 10}

    def test_completed_quantity_converts_to_runs_via_yield(self, order, product):
        ProductionTaskFactory(
            item_type=product,
            quantity=25,
            status="COMPLETED",
            created_from_order=order,
        )

        built = _built_blueprint_runs([order.id], _bp_map(product, yield_qty=10))
        assert built == {BP_ID: 3}

    def test_completed_and_in_progress_tasks_add_up(self, order, product):
        ProductionTaskFactory(
            item_type=product,
            quantity=100,
            status="COMPLETED",
            created_from_order=order,
        )
        running = ProductionTaskFactory(
            item_type=product,
            quantity=332,
            status="IN_PRODUCTION",
            created_from_order=order,
        )
        _link(running, CorporationIndustryJobFactory(status="delivered", runs=50), 50)

        assert _built_blueprint_runs([order.id], _bp_map(product)) == {BP_ID: 150}

    def test_other_orders_jobs_are_ignored(self, order, product):
        other_task = ProductionTaskFactory(
            item_type=product,
            quantity=50,
            status="IN_PRODUCTION",
            created_from_order=MemberOrderFactory(status="ACCEPTED"),
        )
        _link(
            other_task, CorporationIndustryJobFactory(status="delivered", runs=50), 50
        )

        assert _built_blueprint_runs([order.id], _bp_map(product)) == {BP_ID: 0}
