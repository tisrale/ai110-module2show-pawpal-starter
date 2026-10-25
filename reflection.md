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

1. **Available time:** the owner's minutes for the day are a hard limit. A task is only scheduled if it fits in the minutes left.
2. **Priority:** high, medium, or low decides which tasks get picked first. On a tie, shorter tasks go first so more of them fit.
3. **Fixed times:** a task with a set time (like meds at 08:45) stays at that time. Flexible tasks fill the gaps around it.
4. **Due date and status:** only pending tasks due today or earlier are planned, so finished tasks and tomorrow's recurring tasks stay out.

Owner preferences are stored on `Owner` but not used by the scheduler yet.

- How did you decide which constraints mattered most?

I thought about what goes wrong for a real pet if the plan is bad. Time comes first because a plan that doesn't fit in the day is useless. Priority comes next because when time runs out, the owner should lose a play session, not medication. Fixed times come third because some care has to happen at a set hour, so the scheduler must never move those tasks. Clashes between them only get a warning, and the owner decides. Preferences mattered least for a first version, because time, priority, and fixed times already cover the decisions that affect a pet's health.

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

**c. AI strategy**

- Which AI coding assistant features were most effective for building your scheduler?

1. **Working across the whole project at once.** When I added a feature like recurring tasks, Claude Code updated `pawpal_system.py`, the tests, `diagrams/uml.mmd`, and the README together, so they stayed in sync.
2. **Running the code, not just writing it.** It ran `pytest` and `main.py` after changes and showed me the output. For the Streamlit UI it ran the app headlessly and clicked through it (adding tasks, filtering, generating a schedule, marking a task done). That caught a real UI problem: the same conflict warning showed up twice after generating a schedule.
3. **Review prompts.** Asking it to review my UML or skeleton for missing relationships worked better than asking it to write code, because it looked for problems instead of agreeing with me.
4. **Memory between sessions.** It kept a short progress note, so a new session knew what was done and what was left (for example, "refresh the README sample output before submitting").

- Give one example of an AI suggestion you rejected or modified to keep your system design clean.

An earlier version of `detect_conflicts()` sorted the tasks and stopped checking early once a task started after the current one ended. It was faster, but the loop was hard to follow. I changed it to compare every pair with `itertools.combinations`, which is O(n²) but obviously correct, and a day has at most about 20 tasks (see 2b). I made the same kind of call when connecting the UI: all sorting, filtering, and conflict logic stays in `Scheduler`, and `app.py` only calls `sort_by_time()`, `filter_tasks()`, `detect_conflicts()`, and `mark_task_complete()`. That way the app and `main.py` can never disagree about how scheduling works, and every rule is covered by the tests.

- How did using separate chat sessions for different phases help you stay organized?

I used one session per phase: design, implementation, smarter scheduling, and then testing and verification ("Phase 5: Testing and Verification"). Each session had one goal, so the conversation stayed focused and the AI wasn't working from old, outdated versions of my code. I committed at the end of each phase, so git history became a set of checkpoints: design (`6fcb3ed`), core implementation (`d81ff14`), and smarter scheduling (`f76da2f`). Starting a new phase also forced me to recheck earlier work. In Phase 5, comparing the UML to the final code showed it was missing the relationships for completing and repeating a task.

- Summarize what you learned about being the "lead architect" when collaborating with powerful AI tools.

The AI is fast at writing code, but I have to decide what the system should be. It will build whatever I ask for, so I had to set the rules: conflicts are warnings rather than automatic fixes, owner-chosen times are never moved, and logic lives in the backend and not in the UI. I also learned that AI output needs checking even when it looks right. Documentation drifted from the code more than once: the README said a repeating task is next due "today + 1 day", but the code counts from whichever is later, the due date or the day it was finished. The habits that worked best were to ask for reviews, run the code and check the output by hand, keep the UML and README in sync with every change, and make the final call myself on tradeoffs the AI raises but can't decide, like whether to keep `Owner.preferences`.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

I have 37 pytest tests in `tests/test_pawpal.py`, covering both happy paths and edge cases:
- **Sorting:** tasks from different pets come back in clock order with "any time" tasks last, `8:30` sorts before `10:00`, and priority sorting puts high first with shorter tasks first on a tie.
- **Recurrence:** completing a daily task adds one for the next day (and it shows up in tomorrow's plan), weekly tasks come back in 7 days, `once` tasks don't repeat, dates roll over correctly at year end and on a leap day, and finishing a task late or early gives a sensible next due date.
- **Conflict detection:** two tasks at the same time are flagged, overlapping durations are flagged, a task that starts exactly when another ends is not, and a bad time like `8am` gives a warning instead of a crash.
- **Planning edge cases:** a pet with no tasks, an owner with no pets, 0 minutes available, tasks that exactly fill the time, a task longer than the whole budget, and calling `build_plan()` twice.

- Why were these tests important?

The scheduler's whole job is to make decisions for the owner: what to do, in what order, and when. If sorting or recurrence is wrong, the owner gets a wrong plan without any error message, so tests are the only way to know those decisions are right. The edge-case tests also proved their value right away: they found two real bugs. `sort_by_time()` compared times as text, so `8:30` sorted after `10:00`, and completing the same task twice created two copies of the next one. I fixed both, and I checked that the new tests fail on the old code and pass on the fixed code, so they really guard against those bugs coming back.

**b. Confidence**

- How confident are you that your scheduler works correctly?

4 out of 5. All 37 tests pass, every scheduling feature is tested, and the demo output in `main.py` matches what I worked out by hand. I'm not at 5 because the tests only cover the backend (I checked the Streamlit UI by clicking through it, not with automated tests), and there are two known limits I documented but didn't fix.

- What edge cases would you test next if you had more time?

- **Tasks past midnight:** a 30-minute task at 23:50 currently shows as `23:50-24:20`. I'd decide whether it should wrap to the next day and test that.
- **Two pets with the same name:** conflict warnings compare pet names, so two pets named "Max" are labeled "same pet". I'd test this after giving each pet a unique ID.
- **Flexible tasks pushed past the end of the day** when fixed tasks fill most of it.
- **UI tests** with Streamlit's `AppTest`: adding a task with an invalid time, filters, and marking a task done.
- **Whether priority-first is the best fit:** a case where one high-priority task leaves minutes unused that two medium tasks would have filled.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with how scheduling and conflict handling work together. Fixed-time tasks stay where the owner put them, flexible tasks fill the gaps without ever causing a clash, and real clashes become clear warnings instead of crashes or silent changes. I'm also happy with the test suite. Writing edge-case tests found two real bugs (times like `8:30` sorting after `10:00`, and a task completed twice creating two copies of the next one), which showed me that tests are worth more than just confirming what I already believe works.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

- **Use the owner's preferences**, for example a preferred walk time or "no tasks before 7am", since they're stored but unused.
- **Better task choice:** picking by priority first can leave minutes unused when a different mix of tasks would fill the day better. I'd try a smarter selection that still respects priority.
- **Give each pet a unique ID**, so two pets with the same name aren't treated as the same pet in conflict warnings.
- **Handle tasks past midnight**, which currently show as `24:20`.
- **Edit and delete tasks in the UI**, and keep data between app restarts, since everything currently lives only in `st.session_state`.
- **Show each conflict warning once** in the UI instead of in both the Tasks and Schedule sections.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

Design first, and keep the design honest. Having a UML diagram before writing code made it easy to see gaps early: the plan couldn't explain skipped tasks, and tasks didn't know their pet. But the design only stayed useful because I kept updating it as the code changed. With AI, I learned that it's a fast and capable builder, but I still have to be the one deciding what the system should do and checking that it does it. The best results came from asking it to review and test my work, not just write it, and then verifying the output myself by running the code.
