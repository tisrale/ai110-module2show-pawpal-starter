"""Tests for the PawPal+ logic layer in pawpal_system.py."""

from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_task_status():
    task = Task("Morning walk", 30, "high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Feeding", 10, "high"))

    assert len(pet.tasks) == 1


def make_owner_with_tasks():
    owner = Owner("Jordan", available_minutes=120)
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    mochi.add_task(Task("Walk", 30, "high", time="09:00"))
    luna.add_task(Task("Feeding", 10, "high", time="08:00"))
    luna.add_task(Task("Play", 20, "medium"))
    return owner, mochi, luna


def test_sort_by_time_puts_untimed_tasks_last():
    owner, _, _ = make_owner_with_tasks()
    scheduler = Scheduler(owner)

    titles = [task.title for task in scheduler.sort_by_time(owner.get_all_tasks())]

    assert titles == ["Feeding", "Walk", "Play"]


def test_filter_tasks_by_pet_and_status():
    owner, _, luna = make_owner_with_tasks()
    luna.tasks[0].mark_complete()
    scheduler = Scheduler(owner)

    pending = scheduler.filter_tasks(pet_name="luna", completed=False)

    assert [task.title for task in pending] == ["Play"]


def test_completing_daily_task_creates_next_day_task():
    pet = Pet("Luna", "cat")
    task = Task("Feeding", 10, "high", due_date=date(2026, 10, 24))
    pet.add_task(task)

    upcoming = pet.complete_task(task, completed_on=date(2026, 10, 24))

    assert task.completed is True
    assert upcoming.due_date == date(2026, 10, 25)
    assert upcoming.completed is False
    assert len(pet.tasks) == 2


def test_weekly_and_once_recurrence():
    weekly = Task("Bath", 45, "low", frequency="weekly", due_date=date(2026, 10, 24))
    once = Task("Vet visit", 60, "high", frequency="once")

    assert weekly.next_occurrence(completed_on=date(2026, 10, 24)).due_date == date(2026, 10, 31)
    assert once.next_occurrence() is None


def test_future_tasks_are_not_planned_today():
    owner, _, luna = make_owner_with_tasks()
    luna.complete_task(luna.tasks[0])  # next feeding is due tomorrow

    scheduler = Scheduler(owner)
    scheduler.build_plan()

    assert "Feeding" not in [task.title for task in scheduler.scheduled]


def test_detect_conflicts_flags_overlapping_times():
    owner = Owner("Jordan", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, "high", time="08:00"))
    pet.add_task(Task("Meds", 5, "high", time="08:15"))
    pet.add_task(Task("Brush", 10, "low", time="08:30"))  # starts right as the walk ends: no conflict

    scheduler = Scheduler(owner)
    scheduler.build_plan()

    assert len(scheduler.conflicts) == 1
    assert "Walk" in scheduler.conflicts[0] and "Meds" in scheduler.conflicts[0]


def test_flexible_tasks_fill_gaps_around_fixed_tasks():
    owner = Owner("Jordan", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, "high", time="08:10"))
    pet.add_task(Task("Play", 20, "medium"))  # can't fit 08:00-08:20, so goes after the walk

    scheduler = Scheduler(owner, day_start="08:00")
    scheduler.build_plan()

    slots = {task.title: start for start, _, task in scheduler.timeline}
    assert slots["Walk"] == 8 * 60 + 10
    assert slots["Play"] == 8 * 60 + 40
    assert scheduler.conflicts == []


def test_scheduler_mark_task_complete_adds_next_occurrence_to_right_pet():
    owner, mochi, luna = make_owner_with_tasks()
    walk = mochi.tasks[0]
    scheduler = Scheduler(owner)

    upcoming = scheduler.mark_task_complete(walk)

    assert walk.completed is True
    assert upcoming in mochi.tasks and upcoming not in luna.tasks
    assert upcoming.time == walk.time and upcoming.due_date == walk.due_date + timedelta(days=1)


def test_mark_task_complete_rejects_unknown_task():
    owner, _, _ = make_owner_with_tasks()

    with pytest.raises(ValueError):
        Scheduler(owner).mark_task_complete(Task("Stray", 5, "low"))


def test_late_daily_task_is_next_due_tomorrow_not_in_the_past():
    task = Task("Feeding", 10, "high", frequency="Daily", due_date=date(2026, 10, 20))

    upcoming = task.next_occurrence(completed_on=date(2026, 10, 24))

    assert upcoming.due_date == date(2026, 10, 25)  # today + 1, not Oct 21


def test_early_task_does_not_come_back_on_its_original_due_date():
    task = Task("Bath", 45, "low", frequency="weekly", due_date=date(2026, 10, 26))

    upcoming = task.next_occurrence(completed_on=date(2026, 10, 24))

    assert upcoming.due_date == date(2026, 11, 2)  # original due date + 7


def test_detect_conflicts_same_pet_at_same_time():
    owner = Owner("Jordan", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, "high", time="08:00"))
    pet.add_task(Task("Feeding", 10, "high", time="08:00"))

    scheduler = Scheduler(owner)
    scheduler.build_plan()

    assert len(scheduler.conflicts) == 1
    assert "[same pet]" in scheduler.conflicts[0]
    assert "at the same time as" in scheduler.conflicts[0]


def test_detect_conflicts_different_pets_at_same_time():
    owner, mochi, luna = make_owner_with_tasks()  # Mochi's walk is at 09:00
    luna.add_task(Task("Brushing", 15, "low", time="09:00"))

    scheduler = Scheduler(owner)
    scheduler.build_plan()

    assert len(scheduler.conflicts) == 1
    assert "[different pets]" in scheduler.conflicts[0]


def test_detect_conflicts_finds_every_pair_among_three():
    owner = Owner("Jordan", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    for title in ("Walk", "Feeding", "Meds"):
        pet.add_task(Task(title, 10, "high", time="08:00"))

    scheduler = Scheduler(owner)

    assert len(scheduler.detect_conflicts(pet.tasks)) == 3  # A-B, A-C, B-C


def test_invalid_time_gives_warning_instead_of_crashing():
    owner = Owner("Jordan", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, "high", time="8am"))
    pet.add_task(Task("Feeding", 10, "high", time="25:00"))

    scheduler = Scheduler(owner)
    scheduler.build_plan()  # must not raise

    assert len(scheduler.scheduled) == 2  # still planned, as "any time" tasks
    assert len(scheduler.conflicts) == 2
    assert all("[invalid time]" in warning for warning in scheduler.conflicts)
    assert "Warnings:" in scheduler.explain_plan()


def test_unpadded_time_still_detects_conflict():
    owner = Owner("Jordan", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, "high", time="8:30"))
    pet.add_task(Task("Meds", 5, "high", time="08:45"))
    pet.add_task(Task("Lunch", 10, "high", time="12:00"))

    assert len(Scheduler(owner).detect_conflicts(pet.tasks)) == 1


def test_unpadded_and_padded_same_time_count_as_same_time():
    owner = Owner("Jordan", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, "high", time="8:00"))
    pet.add_task(Task("Feeding", 10, "high", time="08:00"))

    conflicts = Scheduler(owner).detect_conflicts(pet.tasks)

    assert len(conflicts) == 1 and "at the same time as" in conflicts[0]


# --- Sorting correctness ---


def test_sort_by_time_returns_chronological_order():
    owner = Owner("Jordan", available_minutes=120)
    mochi = Pet("Mochi", "dog")
    luna = Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    # Added out of order, across two pets.
    mochi.add_task(Task("Dinner", 10, "high", time="18:00"))
    luna.add_task(Task("Meds", 5, "high", time="07:30"))
    mochi.add_task(Task("Walk", 30, "medium", time="12:15"))
    luna.add_task(Task("Feeding", 10, "high", time="07:45"))

    times = [task.time for task in Scheduler(owner).sort_by_time(owner.get_all_tasks())]

    assert times == ["07:30", "07:45", "12:15", "18:00"]


def test_sort_by_time_orders_unpadded_times_by_clock():
    tasks = [Task("Lunch", 10, "high", time="10:00"), Task("Walk", 30, "high", time="8:30")]

    titles = [task.title for task in Scheduler(Owner("Jordan", 60)).sort_by_time(tasks)]

    assert titles == ["Walk", "Lunch"]  # as text, "10:00" would come before "8:30"


def test_sort_tasks_puts_high_priority_first_and_shorter_first_on_ties():
    tasks = [
        Task("Play", 20, "low"),
        Task("Walk", 30, "high"),
        Task("Meds", 5, "high"),
        Task("Brush", 15, "medium"),
    ]

    titles = [task.title for task in Scheduler(Owner("Jordan", 60)).sort_tasks(tasks)]

    assert titles == ["Meds", "Walk", "Brush", "Play"]


def test_sort_tasks_keeps_original_order_on_full_tie():
    tasks = [Task(title, 10, "high") for title in ("A", "B", "C")]

    titles = [task.title for task in Scheduler(Owner("Jordan", 60)).sort_tasks(tasks)]

    assert titles == ["A", "B", "C"]


def test_unknown_priority_sorts_after_low():
    tasks = [Task("Mystery", 10, "urgent"), Task("Play", 10, "low")]

    titles = [task.title for task in Scheduler(Owner("Jordan", 60)).sort_tasks(tasks)]

    assert titles == ["Play", "Mystery"]


# --- Recurrence logic ---


def test_completed_daily_task_appears_in_tomorrows_plan():
    owner = Owner("Jordan", available_minutes=60)
    pet = Pet("Luna", "cat")
    owner.add_pet(pet)
    today = date(2026, 10, 24)
    feeding = Task("Feeding", 10, "high", due_date=today)
    pet.add_task(feeding)

    Scheduler(owner, plan_date=today).mark_task_complete(feeding, completed_on=today)
    tomorrow = Scheduler(owner, plan_date=today + timedelta(days=1))
    tomorrow.build_plan()

    assert [task.title for task in tomorrow.scheduled] == ["Feeding"]
    assert tomorrow.scheduled[0] is not feeding  # the new copy, not the finished one


def test_daily_task_rolls_over_to_next_year():
    task = Task("Feeding", 10, "high", due_date=date(2026, 12, 31))

    assert task.next_occurrence(completed_on=date(2026, 12, 31)).due_date == date(2027, 1, 1)


def test_weekly_task_crosses_leap_day():
    task = Task("Bath", 45, "low", frequency="weekly", due_date=date(2028, 2, 25))

    assert task.next_occurrence(completed_on=date(2028, 2, 25)).due_date == date(2028, 3, 3)


def test_completing_a_task_twice_adds_only_one_next_occurrence():
    pet = Pet("Luna", "cat")
    task = Task("Feeding", 10, "high")
    pet.add_task(task)

    pet.complete_task(task)
    second = pet.complete_task(task)

    assert second is None
    assert len(pet.tasks) == 2  # the original and one next occurrence


# --- Conflict detection ---


def test_no_conflicts_when_times_are_different():
    owner, _, _ = make_owner_with_tasks()  # Feeding 08:00, Walk 09:00, Play any time

    scheduler = Scheduler(owner)
    scheduler.build_plan()

    assert scheduler.conflicts == []


def test_conflicting_tasks_are_still_scheduled():
    owner = Owner("Jordan", available_minutes=120)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 30, "high", time="08:00"))
    pet.add_task(Task("Feeding", 10, "high", time="08:00"))

    scheduler = Scheduler(owner)
    scheduler.build_plan()

    assert len(scheduler.scheduled) == 2  # warns, but never drops or moves a task
    assert "Warnings:" in scheduler.explain_plan()


# --- Planning edge cases ---


def test_pet_with_no_tasks_gives_empty_plan():
    owner = Owner("Jordan", available_minutes=60)
    owner.add_pet(Pet("Mochi", "dog"))

    scheduler = Scheduler(owner)

    assert scheduler.build_plan() == []
    assert scheduler.conflicts == []
    assert "No tasks to plan" in scheduler.explain_plan()


def test_owner_with_no_pets_gives_empty_plan():
    scheduler = Scheduler(Owner("Jordan", available_minutes=60))

    assert scheduler.build_plan() == []
    assert scheduler.filter_tasks() == []


def test_zero_minutes_available_skips_every_task():
    owner, _, _ = make_owner_with_tasks()
    owner.available_minutes = 0

    scheduler = Scheduler(owner)
    scheduler.build_plan()

    assert scheduler.scheduled == []
    assert len(scheduler.skipped) == 3


def test_tasks_that_exactly_fill_the_time_are_all_scheduled():
    owner = Owner("Jordan", available_minutes=30)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", 20, "high"))
    pet.add_task(Task("Brush", 10, "low"))

    scheduler = Scheduler(owner)
    scheduler.build_plan()

    assert [task.title for task in scheduler.scheduled] == ["Walk", "Brush"]
    assert scheduler.skipped == []


def test_task_longer_than_budget_is_skipped_but_smaller_one_still_fits():
    owner = Owner("Jordan", available_minutes=30)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Long hike", 45, "high"))
    pet.add_task(Task("Brush", 10, "low"))

    scheduler = Scheduler(owner)
    scheduler.build_plan()

    assert [task.title for task in scheduler.scheduled] == ["Brush"]
    assert [task.title for task in scheduler.skipped] == ["Long hike"]


def test_build_plan_twice_does_not_duplicate_tasks():
    owner, _, _ = make_owner_with_tasks()
    scheduler = Scheduler(owner)

    scheduler.build_plan()
    scheduler.build_plan()

    assert len(scheduler.scheduled) == 3
    assert len(scheduler.timeline) == 3


def test_filter_by_unknown_pet_returns_empty_list():
    owner, _, _ = make_owner_with_tasks()

    assert Scheduler(owner).filter_tasks(pet_name="Ghost") == []
