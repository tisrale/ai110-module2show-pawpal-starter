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
