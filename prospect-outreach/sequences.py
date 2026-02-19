"""
Sequence engine: defines message templates and orchestrates
the outreach flow based on activation events.

Email templates are loaded from /templates/*.html files (on-brand KLIQ design).
SMS templates remain inline since they're short text strings.
"""

import os
from jinja2 import Template, Environment, FileSystemLoader
from task_progress import get_task_progress

# ── Template directory ──
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


# ── SMS Templates ──

SMS_TEMPLATES = {
    "welcome": Template(
        "Hey {{ first_name }}, we see you started setting up your KLIQ app - great start! "
        "We're offering select creators a free build-out service to get you launch-ready. "
        "Interested? Check your email or book a call: calendly.com/joinkliq/kliq-pp-shortlist "
        "- KLIQ Success Team"
    ),
    "profile_uploaded": Template(
        "Hey {{ first_name }}, nice one - you've uploaded your profile on KLIQ! "
        "We're offering select creators a free done-for-you build-out to get you fully live. "
        "Interested? Check your email or book a call: calendly.com/joinkliq/kliq-pp-shortlist "
        "- KLIQ Success Team"
    ),
    "profile_uploaded_cta": Template(
        "Hey {{ first_name }}, we see you're making progress on your KLIQ app. "
        "We can build the rest out for you - free for select creators. "
        "Book a call: calendly.com/joinkliq/kliq-pp-shortlist "
        "- KLIQ Success Team"
    ),
    "no_activity_7d": Template(
        "Hey {{ first_name }}, we noticed you started your KLIQ app but haven't finished setup. "
        "We're offering select creators a free build-out service - is this of interest? "
        "Check your email or book a call: calendly.com/joinkliq/kliq-pp-shortlist "
        "- KLIQ Success Team"
    ),
    "first_module": Template(
        "Hey {{ first_name }}, great work creating your first module on KLIQ! "
        "We can build the rest out for you - free for select creators. "
        "Interested? Book a call: calendly.com/joinkliq/kliq-pp-shortlist "
        "- KLIQ Success Team"
    ),
    # ── Facebook Campaign SMS ──
    "fb_reengagement": Template(
        "Hey {{ first_name }}, it's KLIQ! You showed interest in our Partner Program - "
        "we've just launched KLIQ Concierge: a dedicated VA for your coaching biz, "
        "15hrs/week for just $500/mo. Cancel anytime. "
        "Find out more: https://calendly.com/joinkliq/kliq-demo-call-15mins-clone "
        "- KLIQ Team"
    ),
    "fb_new_lead": Template(
        "Hi {{ first_name }}, thanks for applying to the KLIQ Partner Program! "
        "Your profile stood out - we'd love to chat about how the sponsorship works. "
        "Book a quick call: https://calendly.com/joinkliq/kliq-pp-shortlist "
        "- KLIQ Team"
    ),
}


# ── Email config: maps template key → (subject template, html file, CTA) ──

EMAIL_CONFIG = {
    "welcome": {
        "subject": "Welcome to KLIQ, {{ first_name }}! �",
        "template_file": "welcome.html",
        "cta_url": "https://admin.joinkliq.io",
        "cta_text": "Go to Your Dashboard",
    },
    "cheat_sheet": {
        "subject": "{{ first_name }}, your personalised growth cheat sheet 📈",
        "template_file": "cheat_sheet.html",
        "cta_url": "https://calendly.com/joinkliq/kliq-pp-shortlist",
        "cta_text": "Book a Free Setup Call",
    },
    "no_activity_7d": {
        "subject": "{{ first_name }}, need a hand getting started?",
        "template_file": "no_activity.html",
        "cta_url": "https://calendly.com/joinkliq/kliq-pp-shortlist",
        "cta_text": "Book a Free Setup Call",
    },
    # ── Facebook Campaign Emails ──
    "fb_reengagement": {
        "subject": "{{ first_name }}, something new from KLIQ you'll want to see",
        "template_file": "fb_reengagement.html",
        "cta_url": "https://calendly.com/joinkliq/kliq-demo-call-15mins-clone",
        "cta_text": "Book a Call — KLIQ Concierge",
    },
    "fb_new_lead": {
        "subject": "{{ first_name }}, you've been shortlisted for the KLIQ Partner Program",
        "template_file": "fb_new_lead.html",
        "cta_url": "https://calendly.com/joinkliq/kliq-pp-shortlist",
        "cta_text": "Book Your Call",
    },
}


def _build_context(prospect):
    """Build the template rendering context from a prospect dict."""
    name = prospect.get("name", "Coach")
    first_name = prospect.get("first_name") or prospect.get("greeting_name")
    if not first_name:
        first_name = name.split()[0] if name else "Coach"

    # Task progress
    progress = get_task_progress(prospect)

    return {
        "first_name": first_name,
        "name": name,
        "coach_type": prospect.get("coach_type", "coaching"),
        "app_name": prospect.get("app_name", "your app"),
        "subject": "",
        # Task progress fields
        "completed": progress["completed"],
        "remaining": progress["remaining"],
        "done_count": progress["done_count"],
        "remaining_count": progress["remaining_count"],
        "total": progress["total"],
        "latest_done": progress["latest_done"],
        "next_step": progress["next_step"],
        "progress_text": progress["progress_text"],
    }


def render_sms(template_key, prospect):
    """Render an SMS template with prospect data."""
    tpl = SMS_TEMPLATES.get(template_key)
    if not tpl:
        raise ValueError(f"Unknown SMS template: {template_key}")

    ctx = _build_context(prospect)
    return tpl.render(**ctx)


def render_email(template_key, prospect):
    """Render an on-brand email from HTML template files. Returns (subject, html_body)."""
    config = EMAIL_CONFIG.get(template_key)
    if not config:
        raise ValueError(f"Unknown email template: {template_key}")

    ctx = _build_context(prospect)

    # Render subject
    subject = Template(config["subject"]).render(**ctx)
    ctx["subject"] = subject

    # Add CTA
    ctx["cta_url"] = config.get("cta_url", "")
    ctx["cta_text"] = config.get("cta_text", "")

    # Render HTML body from file template
    tpl = _env.get_template(config["template_file"])
    body = tpl.render(**ctx)

    return subject, body
