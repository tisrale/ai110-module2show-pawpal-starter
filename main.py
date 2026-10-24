"""Demo script: build and print today's PawPal+ schedule in the terminal."""

from pawpal_system import Owner, Pet, Task, Scheduler


def main() -> None:
    owner = Owner("Jordan", available_minutes=90)

    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added out of time order on purpose, to show sort_by_time().
    mochi.add_task(Task("Morning walk", 30, "high", category="walk", time="08:30"))
    mochi.add_task(Task("Bath", 45, "low", category="grooming", frequency="weekly"))
    luna.add_task(Task("Feeding", 10, "high", category="feeding", time="08:00"))
    mochi.add_task(Task("Breakfast", 10, "high", category="feeding", time="08:00"))  # same time as Luna's feeding
    luna.add_task(Task("Give medication", 5, "high", category="meds", time="08:45"))  # overlaps the walk
    luna.add_task(Task("Play time", 20, "medium", category="enrichment"))

    scheduler = Scheduler(owner, day_start="08:00")
    scheduler.build_plan()

    print("=== Today's Schedule ===")
    print(scheduler.explain_plan())

    print("\n=== All tasks in the order they were added ===")
    print_tasks(owner.get_all_tasks())

    print("\n=== All tasks sorted by time ===")
    print_tasks(scheduler.sort_by_time(owner.get_all_tasks()))

    print("\n=== Recurring task: complete Luna's feeding ===")
    feeding = luna.tasks[0]
    upcoming = scheduler.mark_task_complete(feeding)
    print(f"  Done: {feeding.title} ({feeding.due_date}), next one due {upcoming.due_date}")

    print("\n=== Filter: Mochi's tasks ===")
    print_tasks(scheduler.filter_tasks(pet_name="Mochi"))

    print("\n=== Filter: completed tasks ===")
    print_tasks(scheduler.filter_tasks(completed=True))

    print("\n=== Filter + sort: Luna's pending tasks by time ===")
    print_tasks(scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Luna", completed=False)))


def print_tasks(tasks: list[Task]) -> None:
    """Print one line per task: time, pet, title, status, and due date."""
    if not tasks:
        print("  (none)")
    for task in tasks:
        status = "done" if task.completed else "pending"
        print(
            f"  {task.time or 'any time':>8}  {task.pet_name}: {task.title} "
            f"[{status}, due {task.due_date}]"
        )


if __name__ == "__main__":
    main()
