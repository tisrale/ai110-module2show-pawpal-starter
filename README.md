# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🧩 Implementation Summary

The logic layer lives in `pawpal_system.py` and has four classes:

- **`Task`**: one care activity (title, duration, priority, category, frequency, completion status). It can mark itself complete and turn its priority into a number for sorting.
- **`Pet`**: a pet's details and its list of tasks. Adding a task also stamps the task with the pet's name.
- **`Owner`**: the owner's name, available minutes for the day, and their pets. `get_all_tasks()` returns every pet's tasks in one list.
- **`Scheduler`**: the planner. It reads tasks from `Owner.get_all_tasks()`, so it works across all pets.

**How a plan is built:** `Scheduler.build_plan()` drops completed tasks, sorts the rest by priority (shorter tasks first on ties), and adds tasks in that order while they fit in the owner's available minutes. A task that doesn't fit is skipped, and the scheduler keeps checking the shorter tasks after it. `explain_plan()` then lists each scheduled task with its start and end time, starting from `day_start`, followed by the skipped tasks.

`main.py` runs a demo with two pets, and `tests/test_pawpal.py` holds the pytest tests.

## 🖥️ Sample Output

Output of `python main.py` (one owner with 90 minutes available, two pets, five tasks):

```
=== Today's Schedule ===
Daily plan for Jordan (65 of 90 minutes used):
  08:00-08:05  Luna: Give medication (5 min) [priority: high]
  08:05-08:15  Luna: Feeding (10 min) [priority: high]
  08:15-08:45  Mochi: Morning walk (30 min) [priority: high]
  08:45-09:05  Luna: Play time (20 min) [priority: medium]
Skipped (not enough time left):
  Mochi: Bath (45 min) [priority: low]
Tasks are chosen highest priority first; on a tie, shorter tasks go first so more of them fit.
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

Beyond picking tasks by priority, the scheduler can sort by time of day, filter tasks, repeat daily and weekly tasks, and warn about clashes. Tasks have two fields for this: an optional `time` (`"HH:MM"`, empty means "any time") and a `due_date`.

| Feature | Method(s) |
|---------|-----------|
| Sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_tasks()` |
| Filtering | `Scheduler.filter_tasks()`, `Scheduler.build_plan()` |
| Conflict detection | `Scheduler.detect_conflicts()`, `Scheduler._assign_times()` |
| Recurring tasks | `Scheduler.mark_task_complete()`, `Pet.complete_task()`, `Task.next_occurrence()` |

### Sorting

- **`Scheduler.sort_by_time(tasks)`** returns tasks in clock order, with "any time" tasks last. It uses `sorted()` with the lambda key `(task.time == "", task.time)`: the first item puts timed tasks before untimed ones, and the second sorts the `"HH:MM"` strings, which works as text because they're zero-padded.
- **`Scheduler.sort_tasks(tasks)`** orders tasks for planning: highest priority first, and shorter tasks first on a tie so more of them fit.

### Filtering

- **`Scheduler.filter_tasks(pet_name=None, completed=None)`** returns the owner's tasks narrowed by pet, by status, or both. A filter left as `None` isn't applied, and pet names ignore upper/lower case.
  ```python
  scheduler.filter_tasks(pet_name="Luna")                   # all of Luna's tasks
  scheduler.filter_tasks(completed=False)                   # pending tasks, every pet
  scheduler.filter_tasks(pet_name="Mochi", completed=False) # Mochi's pending tasks
  ```
- **`Scheduler.build_plan()`** only plans tasks that aren't completed and are due on or before the plan date. If a task doesn't fit in the time left, it's skipped and the scheduler keeps going, because a shorter task later may still fit.

### Conflict detection

- **`Scheduler.detect_conflicts(tasks)`** turns each fixed-time task into a start–end slot in minutes and compares every pair (`itertools.combinations`). Two tasks clash when one starts before the other ends, so it catches overlapping durations, not just identical start times. A task that starts exactly when another ends is fine.
- It's lightweight: it **returns warning messages instead of raising errors**, and it never moves a task. `build_plan()` stores the warnings in `scheduler.conflicts`, and `explain_plan()` prints them under "Warnings:". Each warning has a label:
  ```
  [same pet] Mochi: Walk at 08:00 at the same time as Mochi: Feeding at 08:00
  [different pets] Mochi: Morning walk at 08:30 overlaps Luna: Give medication at 08:45
  [invalid time] Mochi: Walk has time '8am' (expected HH:MM), so it was treated as any time
  ```
- **`Scheduler._assign_times(tasks)`** keeps fixed-time tasks at their time and places "any time" tasks into the free gaps starting at `day_start`, so the scheduler itself never creates a conflict.

### Recurring tasks

- **`Scheduler.mark_task_complete(task)`** finds which pet owns the task and completes it through **`Pet.complete_task()`**. That marks the task done and adds the copy that **`Task.next_occurrence()`** creates.
- The next due date uses `timedelta`: **today + 1 day** for `"daily"` and **today + 7 days** for `"weekly"`. A task finished late is next due tomorrow, not on a date that's already past. A task finished early counts from its original due date instead, so it doesn't come back on a day it was already done. `"once"` tasks don't repeat.
- The new copy is due in the future, so it doesn't show up in today's plan.

**Tradeoffs:** see section 2b of [reflection.md](reflection.md).

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
