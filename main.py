"""Demo script: build and print today's PawPal+ schedule in the terminal."""

from pawpal_system import Owner, Pet, Task, Scheduler


def main() -> None:
    owner = Owner("Jordan", available_minutes=90)

    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", 30, "high", category="walk"))
    mochi.add_task(Task("Bath", 45, "low", category="grooming", frequency="weekly"))
    luna.add_task(Task("Feeding", 10, "high", category="feeding"))
    luna.add_task(Task("Give medication", 5, "high", category="meds"))
    luna.add_task(Task("Play time", 20, "medium", category="enrichment"))

    scheduler = Scheduler(owner, day_start="08:00")
    scheduler.build_plan()

    print("=== Today's Schedule ===")
    print(scheduler.explain_plan())


if __name__ == "__main__":
    main()
