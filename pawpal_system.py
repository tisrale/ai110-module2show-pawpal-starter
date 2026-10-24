"""PawPal+ logic layer: backend classes for owners, pets, tasks, and scheduling."""

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from itertools import combinations

PRIORITY_SCORES = {"low": 1, "medium": 2, "high": 3}
RECURRENCE_DAYS = {"daily": 1, "weekly": 7}


def to_minutes(hhmm: str) -> int:
    """Turn an "HH:MM" string into minutes after midnight (raises ValueError if malformed)."""
    parsed = datetime.strptime(hhmm.strip(), "%H:%M")
    return parsed.hour * 60 + parsed.minute


def has_valid_time(task: "Task") -> bool:
    """Return True if the task has a fixed time that parses as "HH:MM" (never raises)."""
    if not task.time:
        return False
    try:
        to_minutes(task.time)
    except ValueError:
        return False
    return True


def to_hhmm(minutes: int) -> str:
    """Turn minutes after midnight back into an "HH:MM" string."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@dataclass
class Task:
    """One pet care activity, such as a walk, feeding, or medication."""

    title: str
    duration_minutes: int
    priority: str  # "low", "medium", or "high"
    category: str = "general"
    frequency: str = "daily"  # "daily", "weekly", or "once"
    completed: bool = False
    pet_name: str = ""  # set by Pet.add_task() so the plan can show whose task it is
    time: str = ""  # fixed start time "HH:MM"; empty means any time works
    due_date: date = field(default_factory=date.today)

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def priority_score(self) -> int:
        """Return the priority as a number so tasks can be sorted (unknown priorities score 0)."""
        return PRIORITY_SCORES.get(self.priority.strip().lower(), 0)

    def next_occurrence(self, completed_on: date | None = None) -> "Task | None":
        """Return a fresh copy of this task for its next due date, or None if it doesn't repeat.

        The next date is max(due_date, completed_on) + 1 day (daily) or + 7 days (weekly),
        using timedelta so month and year ends roll over correctly:
          - done on time or late -> counts from the completion day, so it isn't due in the past
          - done early           -> counts from the original due date, so it doesn't come back
                                    on a day it was already done

        Args:
            completed_on: The day the task was finished. Defaults to today.

        Returns:
            A new, not-completed Task with the same title, time, and priority, or None if
            the frequency isn't "daily" or "weekly" (for example "once").
        """
        days = RECURRENCE_DAYS.get(self.frequency.strip().lower())
        if days is None:
            return None
        base = max(self.due_date, completed_on or date.today())
        return replace(self, completed=False, due_date=base + timedelta(days=days))


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

    def complete_task(self, task: Task, completed_on: date | None = None) -> "Task | None":
        """Mark a task done and, if it repeats, add its next occurrence to this pet.

        Args:
            task: One of this pet's tasks.
            completed_on: The day it was finished. Defaults to today.

        Returns:
            The newly added next-occurrence Task, or None if the task doesn't repeat.
        """
        task.mark_complete()
        upcoming = task.next_occurrence(completed_on)
        if upcoming is not None:
            self.add_task(upcoming)
        return upcoming


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

    def __init__(self, owner: Owner, day_start: str = "08:00", plan_date: date | None = None):
        """Set up a scheduler for an owner, with the day starting at day_start (HH:MM)."""
        self.owner = owner
        self.day_start = day_start
        self.plan_date = plan_date or date.today()
        self.scheduled: list[Task] = []
        self.skipped: list[Task] = []
        self.timeline: list[tuple[int, int, Task]] = []  # (start, end) in minutes after midnight
        self.conflicts: list[str] = []

    def build_plan(self) -> list[Task]:
        """Choose tasks that fit in the owner's available time, then give each a time slot.

        Steps:
          1. Keep tasks that are not completed and are due on or before plan_date.
          2. Go through them by priority (sort_tasks). Add a task if it fits in the
             minutes left; otherwise skip it and keep going, since a shorter one may fit.
          3. Give each chosen task a start time (_assign_times) and check for
             clashes (detect_conflicts).

        Fills self.scheduled, self.skipped, self.timeline, and self.conflicts, clearing
        them first so calling it twice doesn't duplicate anything.

        Returns:
            The scheduled tasks, in priority order.
        """
        # Start fresh so calling build_plan() twice doesn't duplicate tasks.
        self.scheduled = []
        self.skipped = []

        pending = [
            task
            for task in self.filter_tasks(completed=False)
            if task.due_date <= self.plan_date
        ]
        remaining = self.owner.available_minutes
        for task in self.sort_tasks(pending):
            if task.duration_minutes <= remaining:
                self.scheduled.append(task)
                remaining -= task.duration_minutes
            else:
                # Skip it but keep going: a shorter task later may still fit.
                self.skipped.append(task)

        self.timeline = self._assign_times(self.scheduled)
        self.conflicts = self.detect_conflicts(self.scheduled)
        return self.scheduled

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered from highest to lowest priority, shorter tasks first on ties."""
        return sorted(tasks, key=lambda task: (-task.priority_score(), task.duration_minutes))

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks in clock order; tasks with no fixed time go last.

        The sort key is the tuple (has no time, time). Python compares tuples item by
        item, so False (has a time) sorts before True (no time), and within each group
        the "HH:MM" strings sort as text. That matches clock order only when times are
        zero-padded ("08:30", not "8:30").

        Args:
            tasks: The tasks to sort. The list itself isn't changed.

        Returns:
            A new sorted list.
        """
        return sorted(tasks, key=lambda task: (task.time == "", task.time))

    def filter_tasks(self, pet_name: str | None = None, completed: bool | None = None) -> list[Task]:
        """Return the owner's tasks, optionally only one pet's and/or only done/not-done ones.

        Each filter left as None is not applied, so filter_tasks() returns every task.

        Args:
            pet_name: Keep only this pet's tasks (case and extra spaces are ignored).
            completed: True for finished tasks, False for pending ones.

        Returns:
            A new list of the matching tasks.
        """
        tasks = self.owner.get_all_tasks()
        if pet_name is not None:
            tasks = [task for task in tasks if task.pet_name.lower() == pet_name.strip().lower()]
        if completed is not None:
            tasks = [task for task in tasks if task.completed == completed]
        return tasks

    def mark_task_complete(self, task: Task, completed_on: date | None = None) -> Task | None:
        """Complete a task for whichever pet owns it; daily/weekly tasks get their next occurrence.

        Use this when you have a task but not its Pet (for example, from the app's task list).

        Args:
            task: A task belonging to one of the owner's pets.
            completed_on: The day it was finished. Defaults to today.

        Returns:
            The next-occurrence Task added to the same pet, or None if it doesn't repeat.

        Raises:
            ValueError: If no pet of this owner has the task.
        """
        for pet in self.owner.pets:
            # Compare by identity: two tasks with the same fields are still different tasks.
            if any(existing is task for existing in pet.tasks):
                return pet.complete_task(task, completed_on)
        raise ValueError(f"Task '{task.title}' doesn't belong to any of {self.owner.name}'s pets.")

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Return a warning for every pair of fixed-time tasks whose time slots overlap.

        Lightweight on purpose: it only reports problems and never raises, so a bad
        time or a clash can't stop the plan from being built. It never moves a task.

        How it works: turn each fixed-time task into a (start, end) slot in minutes,
        sorted by start, then compare every pair. Two slots overlap when the later one
        starts before the earlier one ends; a task starting exactly when another ends
        is fine. Every pair is checked (O(n^2)), which is plenty fast for a day of tasks.

        Args:
            tasks: The tasks to check, usually the scheduled ones.

        Returns:
            Warning strings, empty if there are no problems. Each starts with a label:
            "[same pet]", "[different pets]", or "[invalid time]" for a time that isn't
            "HH:MM" (that task is treated as any time instead).
        """
        warnings = [
            f"[invalid time] {task.pet_name}: {task.title} has time '{task.time}' "
            f"(expected HH:MM), so it was treated as any time"
            for task in tasks
            if task.time and not has_valid_time(task)
        ]
        # Check every pair once. A day has few tasks, so this is fast enough and easy to follow.
        for earlier, later in combinations(self._fixed_slots(tasks), 2):
            earlier_start, earlier_end, first = earlier
            later_start, _, second = later
            # Slots are sorted by start, so they overlap if the later one starts before the earlier ends.
            if later_start < earlier_end:
                # Same pet: the pet can't do both. Different pets: the owner can't be in two places.
                kind = "same pet" if first.pet_name == second.pet_name else "different pets"
                clash = "at the same time as" if earlier_start == later_start else "overlaps"
                warnings.append(
                    f"[{kind}] {first.pet_name}: {first.title} at {first.time} {clash} "
                    f"{second.pet_name}: {second.title} at {second.time}"
                )
        return warnings

    def _fixed_slots(self, tasks: list[Task]) -> list[tuple[int, int, Task]]:
        """Return (start, end, task) in minutes for each task with a valid fixed time, sorted by start.

        Tasks with no time or an invalid time are left out. Shared by detect_conflicts()
        and _assign_times() so each time is parsed in one place.
        """
        slots = []
        for task in tasks:
            if has_valid_time(task):
                start = to_minutes(task.time)
                slots.append((start, start + task.duration_minutes, task))
        # Sort by minutes, not text, so an unpadded time like "8:30" still lands in the right place.
        return sorted(slots, key=lambda slot: slot[0])

    def _assign_times(self, tasks: list[Task]) -> list[tuple[int, int, Task]]:
        """Keep fixed-time tasks at their time and fit flexible tasks into the gaps from day_start.

        Flexible tasks are placed in priority order. Each one starts where the previous
        one ended (the first at day_start); if it would overlap a fixed-time task, it
        moves to just after that task. So flexible tasks never cause a conflict, but
        overlaps between fixed-time tasks are kept as the owner set them.

        Args:
            tasks: The scheduled tasks, in priority order.

        Returns:
            (start, end, task) slots in minutes after midnight, sorted by start.
        """
        fixed = self._fixed_slots(tasks)
        timeline = list(fixed)

        current = to_minutes(self.day_start)
        for task in tasks:  # already in priority order
            if has_valid_time(task):
                continue
            start = current
            for busy_start, busy_end, _ in fixed:
                if start < busy_end and start + task.duration_minutes > busy_start:
                    start = busy_end  # would overlap, so move past this fixed task
            timeline.append((start, start + task.duration_minutes, task))
            current = start + task.duration_minutes

        return sorted(timeline, key=lambda slot: slot[0])

    def explain_plan(self) -> str:
        """Describe which tasks were scheduled or skipped, and why."""
        if not self.scheduled and not self.skipped:
            return "No tasks to plan. Add some tasks and build the plan first."

        used = sum(task.duration_minutes for task in self.scheduled)
        lines = [
            f"Daily plan for {self.owner.name} on {self.plan_date:%Y-%m-%d} "
            f"({used} of {self.owner.available_minutes} minutes used):"
        ]

        for start, end, task in self.timeline:
            fixed = " (fixed time)" if has_valid_time(task) else ""
            lines.append(
                f"  {to_hhmm(start)}-{to_hhmm(end)}  {task.pet_name}: {task.title} "
                f"({task.duration_minutes} min) [priority: {task.priority}]{fixed}"
            )

        if self.skipped:
            lines.append("Skipped (not enough time left):")
            for task in self.skipped:
                lines.append(
                    f"  {task.pet_name}: {task.title} "
                    f"({task.duration_minutes} min) [priority: {task.priority}]"
                )

        if self.conflicts:
            lines.append("Warnings:")
            for warning in self.conflicts:
                lines.append(f"  {warning}")

        lines.append(
            "Tasks are chosen highest priority first; on a tie, shorter tasks go first "
            "so more of them fit. Fixed-time tasks keep their time, and the others fill "
            "the free gaps starting at " + self.day_start + "."
        )
        return "\n".join(lines)
