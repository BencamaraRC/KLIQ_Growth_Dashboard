# KLIQ Prospect Outreach System

Automated, personalized outreach sequences for new KLIQ coach sign-ups.

## How It Works

1. **Data Pipeline** — Polls BigQuery for new sign-ups and their activation events
2. **Sequence Engine** — Triggers SMS + email based on activation milestones
3. **Cheat Sheet Generator** — Creates personalized PDFs branded with coach's profile image + niche-specific data
4. **Delivery** — Sends via Twilio (SMS) and SendGrid (email)

## Sequence Flow

```
Sign-up detected
  → Welcome email (immediate)

Profile image uploaded
  → SMS: "Hey {name}, noticed you've uploaded your profile image!
          Also noticed you're in the {coach_type} niche.
          I've emailed over a cheat sheet on how to get your first 100 paying subscribers."
  → Email: Personalized cheat sheet PDF attached
  → SMS: "To finalise your setup, we have a white-glove service. Time for a call this week?"

Module created (3 days later)
  → Email: "Great progress {name}! Here's what top {coach_type} coaches do next..."

No activity (7 days)
  → SMS: Re-engagement nudge
  → Email: "Need help getting started?"
```

## Data Sources (BigQuery)

| Event | What it gives us |
|-------|-----------------|
| `self_serve_completed` | Name, email, UUID |
| `self_serve_completed_create_account` | Email, login type |
| `self_serve_completed_creator_type` | Selected worlds/niches |
| `coach_type_updated` | Coach type (Fitness/Business/Executive/etc), country |
| `profile_image_added_your_store` | Profile image uploaded trigger |
| `applications` table | App name, email, created_at |
| Activation events | Module created, livestream, program, etc. |

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # Fill in API keys
python run.py         # Run the sequence engine
```

## Environment Variables

- `TWILIO_ACCOUNT_SID` — Twilio account SID
- `TWILIO_AUTH_TOKEN` — Twilio auth token
- `TWILIO_PHONE_NUMBER` — Twilio sender phone number
- `SENDGRID_API_KEY` — SendGrid API key
- `SENDGRID_FROM_EMAIL` — Sender email address
- `GOOGLE_APPLICATION_CREDENTIALS` — Path to GCP service account JSON
