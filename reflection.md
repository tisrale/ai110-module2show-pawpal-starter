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

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

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
