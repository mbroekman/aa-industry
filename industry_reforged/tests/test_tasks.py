# Third Party
import pytest

# AA Industry App
from industry_reforged.tasks.pi import update_character_pi


@pytest.mark.django_db
class TestTasks:
    def test_dummy_task_import(self):
        assert update_character_pi is not None
