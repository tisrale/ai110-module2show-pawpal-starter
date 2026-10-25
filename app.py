import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler, to_hhmm, to_minutes

PRIORITY_BADGES = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low"}
CONFLICT_LABELS = {
    "same pet": "Pet double-booked",
    "different pets": "You're double-booked",
    "invalid time": "Invalid time",
}


def priority_badge(priority: str) -> str:
    """Return the priority with a colored dot, like "🔴 High"."""
    return PRIORITY_BADGES.get(priority.strip().lower(), priority)


def show_warning(warning: str) -> None:
    """Show a Scheduler warning like "[same pet] ..." as a readable st.warning box."""
    tag, _, detail = warning.partition("] ")
    label = CONFLICT_LABELS.get(tag.lstrip("["), "Warning")
    st.warning(f"**{label}:** {detail or warning}", icon="⚠️")

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")
available_minutes = st.number_input(
    "Minutes available today", min_value=0, max_value=1440, value=60
)

# Streamlit reruns this whole script on every click, so keep the Owner in
# session_state and only create it the first time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, available_minutes=int(available_minutes))
owner = st.session_state.owner
owner.name = owner_name
owner.available_minutes = int(available_minutes)

st.subheader("Add a Pet")
with st.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet name")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    age = st.number_input("Age (years)", min_value=0, max_value=40, value=1)
    if st.form_submit_button("Add pet"):
        if pet_name.strip():
            owner.add_pet(Pet(name=pet_name.strip(), species=species, age=int(age)))
            st.success(f"Added {pet_name.strip()}.")
        else:
            st.error("Please enter a pet name.")

if owner.pets:
    st.table(
        [{"Pet": pet.name, "Species": pet.species.capitalize(), "Age": pet.age} for pet in owner.pets],
        hide_index=True,
    )
else:
    st.info("No pets yet. Add one above.")

st.subheader("Add a Task")
if not owner.pets:
    st.caption("Add a pet first, then you can give it tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        pet_index = st.selectbox(
            "For which pet?",
            range(len(owner.pets)),
            format_func=lambda i: owner.pets[i].name,
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        col4, col5 = st.columns(2)
        with col4:
            task_time = st.text_input("Fixed time (HH:MM, optional)", placeholder="e.g. 08:30")
        with col5:
            frequency = st.selectbox("Repeats", ["daily", "weekly", "once"])
        if st.form_submit_button("Add task"):
            if not task_title.strip():
                st.error("Please enter a task title.")
            else:
                try:
                    # Store "8:30" as "08:30" so times look the same in every table.
                    fixed_time = to_hhmm(to_minutes(task_time)) if task_time.strip() else ""
                except ValueError:
                    st.error(f"'{task_time}' isn't a valid time. Use HH:MM, like 08:30.")
                else:
                    pet = owner.pets[pet_index]
                    pet.add_task(
                        Task(
                            title=task_title.strip(),
                            duration_minutes=int(duration),
                            priority=priority,
                            frequency=frequency,
                            time=fixed_time,
                        )
                    )
                    st.success(f"Added '{task_title.strip()}' for {pet.name}.")

scheduler = Scheduler(owner)

st.subheader("Tasks")
if not owner.get_all_tasks():
    st.info("No tasks yet. Add one above.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_filter = st.selectbox("Pet", ["All pets"] + [pet.name for pet in owner.pets])
    with col2:
        status_filter = st.selectbox("Status", ["Pending", "Done", "All"])
    with col3:
        sort_choice = st.selectbox("Sort by", ["Time", "Priority"])

    shown = scheduler.filter_tasks(
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"Pending": False, "Done": True, "All": None}[status_filter],
    )
    shown = scheduler.sort_by_time(shown) if sort_choice == "Time" else scheduler.sort_tasks(shown)

    total = len(owner.get_all_tasks())
    if shown:
        st.caption(f"Showing {len(shown)} of {total} tasks, sorted by {sort_choice.lower()}.")
        st.table(
            [
                {
                    "Time": task.time or "Any time",
                    "Pet": task.pet_name,
                    "Task": task.title,
                    "Minutes": task.duration_minutes,
                    "Priority": priority_badge(task.priority),
                    "Repeats": task.frequency.capitalize(),
                    "Due": f"{task.due_date:%b %d}",
                    "Status": "✅ Done" if task.completed else "⏳ Pending",
                }
                for task in shown
            ],
            hide_index=True,
        )
    else:
        st.info(f"No tasks match these filters (out of {total} total).", icon="🔍")

    # Warn about clashes as soon as tasks are added, not only when a schedule is built.
    pending_warnings = scheduler.detect_conflicts(scheduler.filter_tasks(completed=False))
    for warning in pending_warnings:
        show_warning(warning)
    if not pending_warnings and any(task.time for task in scheduler.filter_tasks(completed=False)):
        st.success("No time conflicts between pending tasks.", icon="✅")

    pending = scheduler.sort_by_time(scheduler.filter_tasks(completed=False))
    if pending:
        with st.form("complete_task_form"):
            task_index = st.selectbox(
                "Mark a task done",
                range(len(pending)),
                format_func=lambda i: f"{pending[i].pet_name}: {pending[i].title}"
                f" (due {pending[i].due_date:%Y-%m-%d})",
            )
            if st.form_submit_button("Mark done"):
                task = pending[task_index]
                upcoming = scheduler.mark_task_complete(task)
                if upcoming is not None:
                    st.session_state.flash = (
                        f"Done: {task.title}. Next one added for {upcoming.due_date:%Y-%m-%d}."
                    )
                else:
                    st.session_state.flash = f"Done: {task.title}."
                st.rerun()  # redraw the table above with the updated tasks

    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"), icon="🎉")

st.divider()

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if not scheduler.filter_tasks(completed=False):
        st.warning("Add at least one pending task before generating a schedule.")
    else:
        scheduler.build_plan()
        used = sum(task.duration_minutes for task in scheduler.scheduled)

        col1, col2, col3 = st.columns(3)
        col1.metric("Scheduled", len(scheduler.scheduled))
        col2.metric("Minutes used", f"{used} / {owner.available_minutes}")
        col3.metric("Skipped", len(scheduler.skipped))

        if scheduler.conflicts:
            st.error(
                f"{len(scheduler.conflicts)} conflict(s) found. Consider moving one of these tasks.",
                icon="🚨",
            )
            for warning in scheduler.conflicts:
                show_warning(warning)
        else:
            st.success("No conflicts. Every task has its own time slot.", icon="✅")

        st.markdown(f"#### Today's timeline ({scheduler.plan_date:%A, %b %d})")
        if scheduler.timeline:
            st.table(
                [
                    {
                        "Time": f"{to_hhmm(start)} – {to_hhmm(end)}",
                        "Pet": task.pet_name,
                        "Task": task.title,
                        "Minutes": task.duration_minutes,
                        "Priority": priority_badge(task.priority),
                        "Type": "📌 Fixed" if task.time else "🔄 Flexible",
                    }
                    for start, end, task in scheduler.timeline
                ],
                hide_index=True,
            )
            st.caption("📌 Fixed tasks keep the time you set. 🔄 Flexible tasks fill the free gaps.")
        else:
            st.info("Nothing fits in the time available today.", icon="⏰")

        if scheduler.skipped:
            st.warning(
                f"{len(scheduler.skipped)} task(s) skipped because there wasn't enough time left. "
                "Add more minutes or lower another task's priority.",
                icon="⏭️",
            )
            st.table(
                [
                    {
                        "Pet": task.pet_name,
                        "Task": task.title,
                        "Minutes": task.duration_minutes,
                        "Priority": priority_badge(task.priority),
                    }
                    for task in scheduler.skipped
                ],
                hide_index=True,
            )

        with st.expander("Why this plan?"):
            st.code(scheduler.explain_plan(), language=None)
