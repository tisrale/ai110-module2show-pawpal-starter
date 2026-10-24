# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

My initial design has four classes: `Owner`, `Pet`, `Task`, and `Scheduler`. An Owner has many Pets, each Pet has many Tasks, and the Scheduler works from the Owner to build a daily plan. I kept the Scheduler connected only to the Owner, since it can reach every pet and task through it.

- What classes did you include, and what responsibilities did you assign to each?

- **Owner**: stores the owner's name, how many minutes they have available today, their preferences, and their list of pets. It can add a pet and collect all tasks across its pets.
- **Pet**: stores basic pet info (name, species, age) and the pet's care tasks. It can add and remove tasks.
- **Task**: represents one care activity, with a title, duration, priority, category, frequency, and whether it's completed. It can mark itself complete and turn its priority into a number for sorting.
- **Scheduler**: the planning logic. It sorts tasks by priority, fits them into the owner's available time starting from `day_start`, keeps track of which tasks were scheduled and which were skipped, and explains the plan.

**b. Design changes**

- Did your design change during implementation?

Yes. The design changed when I reviewed my first UML draft.

- If yes, describe at least one change and why you made it.

In my first draft, `Scheduler.build_plan()` returned a plain list and `explain_plan()` took no input. That meant `explain_plan()` had no way to know which tasks were scheduled or which were skipped for lack of time, and skipped tasks are an important part of explaining the plan. I added two attributes to the Scheduler, `scheduled` and `skipped`. `build_plan()` fills both, and `explain_plan()` reads them to explain what made it into the day and what didn't.

After writing the class skeleton, I asked AI to review it for missing relationships and logic bottlenecks. It pointed out that a `Task` didn't know which pet it belonged to. Since `Owner.get_all_tasks()` combines every pet's tasks into one list, the Scheduler lost track of whose task was whose, so the plan couldn't say "Mochi: Walk". I added a `pet_name` attribute to `Task`, and `Pet.add_task()` will set it automatically when a task is added.

For smarter scheduling I added an optional `time` ("HH:MM") and a `due_date` to `Task`. Without a time there was nothing to sort by clock or to check for overlaps, and without a due date a recurring task couldn't say when it's next needed. Completing a task through `Pet.complete_task()` now adds the next occurrence. The Scheduler gained `sort_by_time()`, `filter_tasks()`, `detect_conflicts()`, and a `timeline` that keeps fixed-time tasks at their time and fits flexible tasks into the gaps.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

**Main tradeoff: conflicts are reported, not fixed.** My scheduler checks whether fixed-time tasks overlap for their whole duration, not just whether they start at the same minute (a 30-minute walk at 08:30 clashes with medication at 08:45). When it finds a clash, it only adds a warning like `[different pets] Mochi: Morning walk at 08:30 overlaps Luna: Give medication at 08:45`. It doesn't move either task, and it doesn't crash; a badly typed time like "8am" also becomes a warning instead of an error.

This is reasonable because the owner picked those times for a reason. Medication may have to be given at a set hour, and a feeding may be tied to when the owner leaves for work, so the app shouldn't quietly change them. A warning leaves the decision to the owner. Tasks with no fixed time are a different case: nobody chose their time, so the scheduler moves them into free gaps automatically, and they never cause a conflict.

**Smaller tradeoff: readability over speed.** `detect_conflicts()` uses `itertools.combinations` to compare every pair of fixed-time tasks, which is O(n²). An earlier version sorted the tasks and stopped checking early, which is faster for large lists but harder to follow. A pet owner has maybe 5–20 tasks a day (at most about 190 pairs), so the speed difference doesn't matter, and code that's easy to read is easier to fix later. If the app ever had to schedule thousands of tasks, I'd bring back the early stop.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

I used Claude Code in VS Code at almost every step:
- **Design brainstorming:** it suggested attributes and methods for Owner, Pet, Task, and Scheduler, and turned them into a Mermaid class diagram.
- **Design review:** I asked it to review the UML and later the class skeleton for missing relationships and logic bottlenecks.
- **Implementation:** it filled in the method stubs and wrote `main.py` and the first two tests.
- **Debugging setup problems:** it helped when my virtual environment wasn't activating (PowerShell script policy) and when pytest couldn't import `pawpal_system` from the `tests` folder.

- What kinds of prompts or questions were most helpful?

Review questions were the most useful, for example "review my skeleton for missing relationships or potential logic bottlenecks." They made the AI look for problems instead of just agreeing with my design. Specific questions also worked well, like "how should the Scheduler retrieve all tasks from the Owner's pets?", because the answer was something I could check directly in the code.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

The AI's first UML draft had a gap: `build_plan()` returned a plain list and `explain_plan()` took no input, so the explanation couldn't mention skipped tasks. I didn't keep that version. The Scheduler got `scheduled` and `skipped` attributes instead. Later, the skeleton review suggested several changes, and I chose which to take. I accepted adding `pet_name` to `Task` so the plan shows whose task it is. I rejected removing `Owner.preferences`, even though the AI pointed out nothing uses it yet, because owner preferences are one of the constraints in the project scenario and I may use them later.

- How did you evaluate or verify what the AI suggested?

I didn't just trust that the code looked right. I ran `main.py` and checked the schedule by hand: high-priority tasks came first, the times added up, and the 45-minute low-priority task was skipped because only 25 minutes were left. I also tested a two-pet case where one task was already completed, a priority was written as "High" with a capital letter, and `build_plan()` was called twice, to confirm there were no duplicates. Running `pytest` showed both tests passing. Running it also caught a real problem the first time, the import error from the `tests` folder, which we fixed with `pytest.ini`. Finally, I checked that `diagrams/uml.mmd` still matched the code after each change.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
