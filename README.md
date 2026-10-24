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

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
