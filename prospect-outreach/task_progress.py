"""
Task progress tracker: calculates how many setup steps a prospect has
completed and how many remain before they can earn their first dollar.

The 5 steps to first dollar:
1. Upload profile image
2. Choose coach type / niche
3. Create first module (program, eCourse, etc.)
4. Publish module (make it live)
5. Set up pricing / subscription

Each step maps to BigQuery event data already in the prospect profile.
"""

# Ordered steps to earning first dollar
STEPS = [
    {
        "key": "profile_image",
        "label": "Upload your profile image",
        "done_label": "Uploaded your profile image",
    },
    {
        "key": "coach_type",
        "label": "Choose your coaching niche",
        "done_label": "Chose your coaching niche",
    },
    {
        "key": "create_module",
        "label": "Create your first module",
        "done_label": "Created your first module",
    },
    {
        "key": "publish_module",
        "label": "Publish your module",
        "done_label": "Published your module",
    },
    {
        "key": "setup_pricing",
        "label": "Set up your subscription pricing",
        "done_label": "Set up subscription pricing",
    },
]


def get_task_progress(prospect):
    """
    Analyse a prospect's profile and return task progress info.

    Returns dict with:
        completed: list of completed step labels
        remaining: list of remaining step labels
        total: total number of steps
        done_count: number completed
        remaining_count: number remaining
        latest_done: the most recent completed step label (for messaging)
        next_step: the next step to complete
        progress_text: e.g. "3 of 5 steps done — only 2 to go!"
    """
    actions = prospect.get("actions_completed", [])
    coach_type = prospect.get("coach_type")
    has_image = prospect.get("has_profile_image", False)

    # Check each step
    step_status = {
        "profile_image": bool(has_image),
        "coach_type": bool(coach_type),
        "create_module": any(
            e in actions
            for e in ["create_module", "creates_program", "live_session_created"]
        ),
        "publish_module": any(
            e in actions for e in ["publish_module", "publishes_program"]
        ),
        "setup_pricing": any(
            e in actions
            for e in [
                "subscription_selected_talent",
                "self_serve_completed_add_payment_info",
            ]
        ),
    }

    completed = []
    remaining = []
    latest_done = None
    next_step = None

    for step in STEPS:
        if step_status[step["key"]]:
            completed.append(step["done_label"])
            latest_done = step["done_label"]
        else:
            remaining.append(step["label"])
            if next_step is None:
                next_step = step["label"]

    done_count = len(completed)
    remaining_count = len(remaining)
    total = len(STEPS)

    if remaining_count == 0:
        progress_text = "You've completed all 5 setup steps — you're ready to earn!"
    elif remaining_count == 1:
        progress_text = f"You're {done_count} of {total} steps done — just 1 more to go!"
    else:
        progress_text = (
            f"You're {done_count} of {total} steps done — only {remaining_count} to go!"
        )

    return {
        "completed": completed,
        "remaining": remaining,
        "total": total,
        "done_count": done_count,
        "remaining_count": remaining_count,
        "latest_done": latest_done,
        "next_step": next_step,
        "progress_text": progress_text,
    }
