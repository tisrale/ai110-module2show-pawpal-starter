"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

PRIORITY_SCORES = {"low": 1, "medium": 2, "high": 3}


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
        self.completed = True

    def priority_score(self) -> int:
        """Return the priority as a number so tasks can be sorted (unknown priorities score 0)."""
        return PRIORITY_SCORES.get(self.priority.strip().lower(), 0)


@dataclass
class Pet:
    """A pet and the care tasks it needs."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet and set the task's pet_name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet."""
        if task in self.tasks:
            self.tasks.remove(task)


@dataclass
class Owner:
    """A pet owner, their available time, and their pets."""

    name: str
    available_minutes: int
    preferences: dict = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Return the tasks of all this owner's pets in one list."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """Builds and explains a daily care plan for an owner."""

    def __init__(self, owner: Owner, day_start: str = "08:00"):
        """Set up a scheduler for an owner, with the day starting at day_start (HH:MM)."""
        self.owner = owner
        self.day_start = day_start
        self.scheduled: list[Task] = []
        self.skipped: list[Task] = []

    def build_plan(self) -> list[Task]:
        """Choose and order tasks that fit in the owner's available time."""
        # Start fresh so calling build_plan() twice doesn't duplicate tasks.
        self.scheduled = []
        self.skipped = []

        pending = [task for task in self.owner.get_all_tasks() if not task.completed]
        remaining = self.owner.available_minutes
        for task in self.sort_tasks(pending):
            if task.duration_minutes <= remaining:
                self.scheduled.append(task)
                remaining -= task.duration_minutes
            else:
                # Skip it but keep going: a shorter task later may still fit.
                self.skipped.append(task)
        return self.scheduled

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered from highest to lowest priority, shorter tasks first on ties."""
        return sorted(tasks, key=lambda task: (-task.priority_score(), task.duration_minutes))

    def explain_plan(self) -> str:
        """Describe which tasks were scheduled or skipped, and why."""
        if not self.scheduled and not self.skipped:
            return "No tasks to plan. Add some tasks and build the plan first."

        used = sum(task.duration_minutes for task in self.scheduled)
        lines = [
            f"Daily plan for {self.owner.name} "
            f"({used} of {self.owner.available_minutes} minutes used):"
        ]

        current = datetime.strptime(self.day_start, "%H:%M")
        for task in self.scheduled:
            end = current + timedelta(minutes=task.duration_minutes)
            lines.append(
                f"  {current:%H:%M}-{end:%H:%M}  {task.pet_name}: {task.title} "
                f"({task.duration_minutes} min) [priority: {task.priority}]"
            )
            current = end

        if self.skipped:
            lines.append("Skipped (not enough time left):")
            for task in self.skipped:
                lines.append(
                    f"  {task.pet_name}: {task.title} "
                    f"({task.duration_minutes} min) [priority: {task.priority}]"
                )

        lines.append(
            "Tasks are chosen highest priority first; on a tie, shorter tasks go first "
            "so more of them fit."
        )
        return "\n".join(lines)
