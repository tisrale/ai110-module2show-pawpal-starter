"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from dataclasses import dataclass, field


@dataclass
class Task:
    """One pet care activity, such as a walk, feeding, or medication."""

    title: str
    duration_minutes: int
    priority: str  # "low", "medium", or "high"
    category: str = "general"
    frequency: str = "daily"  # "daily" or "weekly"
    completed: bool = False
    pet_name: str = ""  # set by Pet.add_task() so the plan can show whose task it is

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass

    def priority_score(self) -> int:
        """Return the priority as a number so tasks can be sorted."""
        pass


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet and set the task's pet_name."""
        pass

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet."""
        pass


@dataclass
class Owner:
    """A pet owner, their available time, and their pets."""

    name: str
    available_minutes: int
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def get_all_tasks(self) -> list[Task]:
        """Return the tasks of all this owner's pets in one list."""
        pass


class Scheduler:
    """Builds and explains a daily care plan for an owner."""

    def __init__(self, owner: Owner, day_start: str = "08:00"):
        self.owner = owner
        self.day_start = day_start
        self.scheduled: list[Task] = []
        self.skipped: list[Task] = []

    def build_plan(self) -> list[Task]:
        """Choose and order tasks that fit in the owner's available time."""
        pass

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered from highest to lowest priority."""
        pass

    def explain_plan(self) -> str:
        """Describe which tasks were scheduled or skipped, and why."""
        pass
