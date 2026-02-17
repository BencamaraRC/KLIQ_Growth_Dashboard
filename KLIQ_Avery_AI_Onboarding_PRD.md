# PRD: AVERY AI — Conversational Onboarding Assistant
## Two-Way AI-Guided Coach Setup for KLIQ

---

# 1. EXECUTIVE SUMMARY

## The Idea

Replace the current static onboarding (1 niche question → empty dashboard) with a **two-way AI conversation** that guides coaches through setting up their store. Avery already exists as a chatbot widget in the bottom-right corner of the admin panel. We transform it from a passive support bot into an **active onboarding partner** that:

1. **Asks questions** to understand the coach's business
2. **Takes actions** on the coach's behalf (creates content, configures store, sets pricing)
3. **Explains what it's doing** and why
4. **Learns the coach's voice** from their social content
5. **Celebrates progress** and keeps momentum

## Why Conversational > Static Checklist

| Approach | Pros | Cons |
|----------|------|------|
| **Static checklist** (Scorecard PRD) | Simple, clear, predictable | One-size-fits-all, no personalisation, coach still does all the work |
| **Guided wizard** (5-Min Storefront PRD) | Step-by-step, visual | Linear, can't adapt, coach still does all the work |
| **Conversational AI** (This PRD) | Personalised, adaptive, does work FOR the coach, feels like having a helper | More complex to build, AI can make mistakes |
| **Hybrid: Conversation + Scorecard** (RECOMMENDED) | Best of both — AI does the work, scorecard shows progress | Needs both systems integrated |

**Recommendation:** Build the conversational AI as the PRIMARY onboarding experience, with the Activation Scorecard as a VISUAL PROGRESS TRACKER that updates as Avery completes tasks. The conversation IS the onboarding.

---

# 2. THE CONVERSATION FLOW

## 2.1 — Full Conversation Script

The conversation adapts based on coach responses, but follows this general arc:

### Phase 1: Welcome & Discovery (60 seconds)

```
┌─────────────────────────────────────────────────────────┐
│                                          Avery AI 🤖    │
│                                                         │
│  AVERY: Hey! 👋 I'm Avery, your setup assistant.       │
│  I'm going to help you build your coaching store        │
│  in the next few minutes.                               │
│                                                         │
│  First — what should I call you?                        │
│                                                         │
│  COACH: Sarah                                           │
│                                                         │
│  AVERY: Great, Sarah! What kind of coaching do          │
│  you do?                                                │
│                                                         │
│  [Fitness & Training]  [Wellness & Mindfulness]         │
│  [Business & Executive]  [Lifestyle & Creator]          │
│  [Type your own...]                                     │
│                                                         │
│  COACH: [Fitness & Training]                            │
│                                                         │
│  AVERY: Nice! And what's your specialty within          │
│  fitness? For example: HIIT, strength training,         │
│  yoga, running, nutrition...                            │
│                                                         │
│  COACH: HIIT and strength training                      │
│                                                         │
│  AVERY: Love it. HIIT and strength — that's one         │
│  of the most popular niches on KLIQ. Coaches in         │
│  your space typically earn £500-1,800/month.            │
│                                                         │
│  Let me set up your store. This will take about         │
│  3 minutes and I'll do most of the work. 💪             │
│                                                         │
│  ████░░░░░░ 20% — Let's go!                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**What Avery learns:**
- Coach's preferred name
- Niche (replaces the current modal question)
- Specialty/sub-niche (NEW — more granular than current)
- Sets expectations ("3 minutes", "I'll do most of the work")

**What Avery does in the background:**
- Updates coach profile with name, niche, specialty
- Selects appropriate template based on niche
- Prepares niche-specific pricing benchmarks

### Phase 2: Social Connect & Content Import (90 seconds)

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  AVERY: Do you post on Instagram, TikTok, or           │
│  YouTube? I can pull your best content and turn         │
│  it into blog posts for your store automatically.       │
│                                                         │
│  [Connect Instagram]  [Connect TikTok]                  │
│  [Connect YouTube]    [Skip — I'll start fresh]         │
│                                                         │
│  COACH: [Connect Instagram]                             │
│                                                         │
│  (OAuth popup → connects → returns)                     │
│                                                         │
│  AVERY: Connected! ✅ I can see your Instagram          │
│  — you've got some great content, Sarah.                │
│                                                         │
│  I found 47 posts. Your top performers:                 │
│  📸 "5 morning stretches..." — 2,300 likes              │
│  📸 "The protein myth..." — 1,800 likes                 │
│  📸 "My go-to HIIT workout..." — 1,500 likes            │
│                                                         │
│  I'm turning these into blog articles for your          │
│  store now... ⏳                                        │
│                                                         │
│  ████████░░ 40% — Content importing                     │
│                                                         │
│  ...                                                    │
│                                                         │
│  Done! ✅ I've created 3 blog posts:                    │
│                                                         │
│  📝 "5 Morning Stretches That Changed My Routine"       │
│  📝 "The Protein Myth: What I Tell All My Clients"      │
│  📝 "My Go-To HIIT Workout for Busy Professionals"      │
│                                                         │
│  Want to preview them?                                  │
│                                                         │
│  [Preview blogs]  [Looks good, continue!]               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**If coach clicks "Preview blogs":**
```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  AVERY: Here's the first one:                           │
│                                                         │
│  ┌──────────────────────────────────────────────┐       │
│  │ 5 Morning Stretches That Changed My Routine  │       │
│  │                                              │       │
│  │ As a fitness coach, I get asked about         │       │
│  │ morning routines more than anything else.     │       │
│  │ Here are the 5 stretches I do every single    │       │
│  │ morning — and why they work...                │       │
│  │                                              │       │
│  │ [Read full article →]                        │       │
│  └──────────────────────────────────────────────┘       │
│                                                         │
│  I wrote this in your voice based on your Instagram     │
│  post. Want me to change anything?                      │
│                                                         │
│  [Publish all 3 ✅]  [Edit this one]  [Regenerate]     │
│                                                         │
│  COACH: [Publish all 3 ✅]                              │
│                                                         │
│  AVERY: Published! 🎉 Your store now has 3 blog         │
│  posts. That puts you ahead of 95% of new coaches.     │
│                                                         │
│  ██████████░░ 60% — Content done!                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**If coach clicks "Skip — I'll start fresh":**
```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  AVERY: No problem! I can write blog posts for          │
│  you based on popular topics in HIIT & strength.        │
│                                                         │
│  Here are 3 topics your audience would love:            │
│                                                         │
│  📝 "The Beginner's Guide to HIIT Training"             │
│  📝 "5 Strength Exercises You Can Do at Home"           │
│  📝 "Why Rest Days Are Non-Negotiable"                  │
│                                                         │
│  Want me to write these for you? I'll use a             │
│  professional but friendly tone.                        │
│                                                         │
│  [Write them! ✅]  [Suggest different topics]           │
│                                                         │
│  COACH: [Write them! ✅]                                │
│                                                         │
│  AVERY: Writing... ⏳                                   │
│                                                         │
│  Done! ✅ 3 blog posts published to your store.         │
│  You can edit them anytime from Your Store.             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Phase 3: Profile & Store Setup (60 seconds)

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  AVERY: Now let's make your store look amazing.         │
│  Can you upload a profile photo? This is what           │
│  your subscribers will see.                             │
│                                                         │
│  [Upload photo 📷]  [Take selfie 🤳]                   │
│  [Use my Instagram photo]                               │
│                                                         │
│  COACH: [Use my Instagram photo]                        │
│                                                         │
│  AVERY: Great choice! ✅ I've set your Instagram        │
│  profile photo as your store photo.                     │
│                                                         │
│  I also wrote a bio for your store based on your        │
│  Instagram profile:                                     │
│                                                         │
│  ┌──────────────────────────────────────────────┐       │
│  │ "Sarah is a certified HIIT and strength      │       │
│  │  coach helping busy professionals get fit     │       │
│  │  without spending hours in the gym. With 5+   │       │
│  │  years of experience and a community of       │       │
│  │  10,000+ followers, she brings high-energy    │       │
│  │  workouts and practical nutrition advice       │       │
│  │  straight to your phone."                     │       │
│  └──────────────────────────────────────────────┘       │
│                                                         │
│  How does that sound?                                   │
│                                                         │
│  [Use this bio ✅]  [Edit it]  [Write my own]          │
│                                                         │
│  COACH: Can you make it more casual?                    │
│                                                         │
│  AVERY: Sure! Here's a more casual version:             │
│                                                         │
│  ┌──────────────────────────────────────────────┐       │
│  │ "Hey! I'm Sarah — HIIT lover, strength       │       │
│  │  nerd, and your new favourite coach. I help   │       │
│  │  busy people get strong without living at     │       │
│  │  the gym. Expect sweaty workouts, real talk   │       │
│  │  on nutrition, and zero BS. Let's go! 💪"     │       │
│  └──────────────────────────────────────────────┘       │
│                                                         │
│  COACH: Perfect!                                        │
│                                                         │
│  AVERY: Bio updated! ✅                                 │
│                                                         │
│  ████████████░░ 70% — Looking great!                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Key moment:** The coach said "Can you make it more casual?" — this is a **free-form conversation**. Avery understands natural language and adapts. This is what makes it two-way, not just button clicks.

### Phase 4: Pricing (30 seconds)

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  AVERY: Almost there! Let's set your subscription       │
│  price.                                                 │
│                                                         │
│  Based on other HIIT & strength coaches on KLIQ:        │
│  • Average price: £14.99/month                          │
│  • Top earners charge: £25-35/month                     │
│  • Most popular price point: £9.99/month                │
│                                                         │
│  What would you like to charge?                         │
│                                                         │
│  [£9.99/mo]  [£14.99/mo]  [£19.99/mo]                 │
│  [Custom amount...]                                     │
│                                                         │
│  COACH: I was thinking £12.99                           │
│                                                         │
│  AVERY: £12.99/month — solid choice! That's right       │
│  in the sweet spot for your niche.                      │
│                                                         │
│  If you get 50 subscribers at that price, you'd         │
│  earn £649.50/month. Top coaches in your niche          │
│  hit 50 subs within 3-6 months. 📈                     │
│                                                         │
│  Price set! ✅                                          │
│                                                         │
│  ██████████████░░ 80% — Nearly done!                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Phase 5: Store Launch & Share (60 seconds)

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  AVERY: 🎉 Sarah, your store is LIVE!                  │
│                                                         │
│  ┌──────────────────────────────────────────────┐       │
│  │  [STORE PREVIEW]                              │       │
│  │                                              │       │
│  │  🖼️ Sarah's photo                            │       │
│  │  "Hey! I'm Sarah — HIIT lover..."            │       │
│  │  Subscribe — £12.99/mo                        │       │
│  │                                              │       │
│  │  📝 5 Morning Stretches That Changed...       │       │
│  │  📝 The Protein Myth: What I Tell...          │       │
│  │  📝 My Go-To HIIT Workout for...             │       │
│  │                                              │       │
│  │  🔗 sarahjones.joinkliq.io                   │       │
│  └──────────────────────────────────────────────┘       │
│                                                         │
│  Your URL: sarahjones.joinkliq.io                       │
│                                                         │
│  Now the most important step — share it with            │
│  your audience! Coaches who share on Day 1 get          │
│  their first subscriber 5x faster.                      │
│                                                         │
│  I've written a post for you:                           │
│                                                         │
│  ┌──────────────────────────────────────────────┐       │
│  │ "I just launched my coaching platform! 🎉     │       │
│  │  Get exclusive HIIT workouts, strength tips,  │       │
│  │  and live sessions — all in one place.        │       │
│  │  Check it out 👇                              │       │
│  │  sarahjones.joinkliq.io"                      │       │
│  └──────────────────────────────────────────────┘       │
│                                                         │
│  [Share to Instagram Story]  [Copy to clipboard]        │
│  [Share on WhatsApp]  [Download QR code]                │
│                                                         │
│  COACH: [Copy to clipboard]                             │
│                                                         │
│  AVERY: Copied! ✅ Go paste that everywhere. 🚀        │
│                                                         │
│  ████████████████░░ 90%                                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Phase 6: Next Steps & Ongoing Relationship (30 seconds)

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  AVERY: You're almost at 100%! One last thing           │
│  that top coaches do in their first week:               │
│                                                         │
│  📅 Schedule your first live session.                   │
│  Live sessions are the #2 driver of subscriber          │
│  retention — your audience LOVES live content.          │
│                                                         │
│  Want me to help you set one up?                        │
│                                                         │
│  [Yes, let's schedule one]  [I'll do it later]          │
│                                                         │
│  COACH: [I'll do it later]                              │
│                                                         │
│  AVERY: No worries! I'll remind you tomorrow. 😊       │
│                                                         │
│  Here's what you've accomplished today:                 │
│                                                         │
│  ✅ Store created with your branding                    │
│  ✅ 3 blog posts published                              │
│  ✅ Profile photo & bio set                             │
│  ✅ Pricing configured (£12.99/mo)                      │
│  ✅ Store URL shared                                    │
│  ⬜ Schedule first live session (tomorrow?)              │
│                                                         │
│  ████████████████░░ 90% — Amazing start!                │
│                                                         │
│  I'm always here if you need help. Just click           │
│  my icon anytime. I can:                                │
│  • Write more blog posts                               │
│  • Help you plan live sessions                          │
│  • Answer questions about KLIQ                          │
│  • Give you tips to grow your audience                  │
│                                                         │
│  Talk soon, Sarah! 💪                                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

# 3. ONGOING CONVERSATIONS (Post-Onboarding)

Avery doesn't disappear after onboarding. It becomes an ongoing assistant:

## 3.1 — Daily Check-Ins (First 7 Days)

### Day 2 Morning
```
AVERY: Morning Sarah! 👋 Quick update:
• Your store had 12 visitors yesterday
• 3 people read your blog "5 Morning Stretches"
• 0 subscribers yet — but that's normal for Day 1!

Tip: Coaches who go live in their first week get 
subscribers 3x faster. Want to schedule a session?

[Schedule a live session]  [Not yet]
```

### Day 3
```
AVERY: Hey Sarah! Your store is getting traffic — 
28 total visitors now. 📈

I noticed you haven't connected Stripe yet. You'll 
need it to accept payments when subscribers sign up.

Want me to walk you through it? Takes 2 minutes.

[Set up Stripe]  [Remind me tomorrow]
```

### Day 5
```
AVERY: Sarah, I've got 2 new blog drafts ready 
from your latest Instagram posts:

📝 "Why I Swear By Compound Movements"
📝 "My Honest Review of Creatine After 6 Months"

[Review & publish]  [Skip this week]
```

### Day 7
```
AVERY: It's been one week! 🎉 Here's your recap:

📊 YOUR FIRST WEEK
• 67 store visitors
• 3 blog posts published (+ 2 drafts ready)
• 1 subscriber! 🎉 (if applicable)
• Store shared 3 times

You're in the top 27% of new coaches. Keep going!

This week I'd recommend:
1. Go live for the first time (even 15 mins)
2. Publish those 2 blog drafts
3. Share your store link again

[Let's plan this week]  [I'm good for now]
```

## 3.2 — Reactive Conversations (Coach Asks Avery)

Avery can answer questions and take actions at any time:

```
COACH: How do I change my subscription price?

AVERY: Easy! Your current price is £12.99/month.
What would you like to change it to?

[£9.99]  [£14.99]  [£19.99]  [Custom...]

COACH: £14.99

AVERY: Done! ✅ Price updated to £14.99/month.
Existing subscribers will keep their current price.
New subscribers will see £14.99.
```

```
COACH: Can you write a blog about meal prep?

AVERY: Sure! Any specific angle? For example:
• Meal prep for busy professionals
• Budget-friendly meal prep
• High-protein meal prep for strength training
• Meal prep for beginners

COACH: High protein for strength training

AVERY: Writing now... ⏳

Done! Here's what I've got:

📝 "High-Protein Meal Prep: A Strength Trainer's 
    Weekly Guide"

[Preview]  [Publish ✅]  [Regenerate]
```

```
COACH: How am I doing compared to other coaches?

AVERY: Here's where you stand, Sarah:

📊 YOUR STATS (Month 1)
• Subscribers: 8 (avg for month 1: 3)
• Monthly revenue: £103.92
• Blog posts: 7 (avg: 1)
• Store visitors: 234

You're outperforming 78% of coaches at this stage! 🔥

To hit the next level (25 subscribers), I'd suggest:
1. Go live twice a week (your live sessions convert 
   3x better than blogs)
2. Share a blog post on Instagram Stories every 
   Tuesday and Thursday
3. Ask your current subscribers to refer friends

Want me to help with any of these?
```

## 3.3 — Proactive Nudges (Avery Initiates)

| Trigger | Avery Message |
|---------|--------------|
| No login for 3 days | "Hey Sarah! Haven't seen you in a few days. Your store had 15 visitors while you were away. Want to check in?" |
| Subscriber milestone (10, 25, 50, 100) | "🎉 You just hit 25 subscribers! That's £324.75/month. You're now eligible for KLIQ Growth Services → [Learn more]" |
| Blog draft ready (weekly) | "2 new blog drafts from your latest posts → [Review]" |
| Live session reminder | "Your live session is in 1 hour! 12 people have RSVP'd. [Go to studio]" |
| Revenue milestone | "💰 You just earned your first £100! At this rate, you'll hit £500/month by [date]." |
| Churn risk detected (no login 7+ days) | "Sarah, your subscribers are asking when your next live session is. Want me to help you schedule one? [Schedule] [Snooze 3 days]" |
| Social post performing well | "Your Instagram post from today is getting great engagement (500+ likes). Want me to turn it into a blog post? [Yes!]" |

---

# 4. TECHNICAL ARCHITECTURE

## 4.1 — System Design

```
┌──────────────────────────────────────────────────────────────┐
│                        AVERY AI SYSTEM                        │
│                                                              │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────────┐   │
│  │  CHAT UI     │    │  CONVERSATION │    │  ACTION        │   │
│  │  (Frontend)  │───▶│  ENGINE       │───▶│  EXECUTOR      │   │
│  │             │◀───│  (Backend)    │◀───│  (Backend)     │   │
│  └─────────────┘    └──────┬───────┘    └────────┬───────┘   │
│                            │                     │           │
│                     ┌──────▼───────┐    ┌────────▼───────┐   │
│                     │  LLM API     │    │  KLIQ INTERNAL │   │
│                     │  (OpenAI)    │    │  APIs           │   │
│                     │              │    │                │   │
│                     │  - GPT-4o    │    │  - Profile API │   │
│                     │  - Function  │    │  - Blog API    │   │
│                     │    Calling   │    │  - Store API   │   │
│                     │  - Streaming │    │  - Pricing API │   │
│                     └──────────────┘    │  - Social API  │   │
│                                         │  - Live API    │   │
│                                         │  - Analytics   │   │
│                                         └────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │                  CONTEXT STORE                        │    │
│  │                                                      │    │
│  │  - Coach profile (name, niche, specialty)            │    │
│  │  - Onboarding state (current phase, completed items) │    │
│  │  - Conversation history (last 50 messages)           │    │
│  │  - Coach preferences (tone, formality, topics)       │    │
│  │  - Store state (content count, subscriber count)     │    │
│  │  - Social connections (platforms, content cache)     │    │
│  │  - Analytics (visitors, subscribers, revenue)        │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## 4.2 — OpenAI Function Calling (Tools)

Avery uses OpenAI's function calling to execute actions on the KLIQ platform. The LLM decides WHEN to call each function based on the conversation context.

### Defined Functions (Tools)

```json
{
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "update_coach_profile",
        "description": "Update the coach's profile information including name, bio, niche, specialty, and profile photo",
        "parameters": {
          "type": "object",
          "properties": {
            "display_name": {"type": "string", "description": "Coach's display name"},
            "bio": {"type": "string", "description": "Coach's bio text for their storefront"},
            "niche": {"type": "string", "enum": ["fitness", "wellness", "business", "executive", "lifestyle", "creator"]},
            "specialty": {"type": "string", "description": "Coach's specific specialty within their niche"},
            "profile_photo_source": {"type": "string", "enum": ["instagram", "tiktok", "upload"], "description": "Where to pull profile photo from"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "connect_social_account",
        "description": "Initiate OAuth flow to connect a social media account",
        "parameters": {
          "type": "object",
          "properties": {
            "platform": {"type": "string", "enum": ["instagram", "tiktok", "youtube"]}
          },
          "required": ["platform"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "generate_blog_posts",
        "description": "Generate blog posts using AI, either from social media content or from niche-specific topics",
        "parameters": {
          "type": "object",
          "properties": {
            "source": {"type": "string", "enum": ["social_import", "niche_template", "custom_topic"]},
            "count": {"type": "integer", "description": "Number of blog posts to generate (1-5)"},
            "topic": {"type": "string", "description": "Custom topic if source is custom_topic"},
            "tone": {"type": "string", "enum": ["professional", "casual", "energetic", "calm"], "description": "Writing tone preference"},
            "auto_publish": {"type": "boolean", "description": "Whether to publish immediately or save as draft"}
          },
          "required": ["source", "count"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "set_subscription_price",
        "description": "Set the monthly subscription price for the coach's store",
        "parameters": {
          "type": "object",
          "properties": {
            "price": {"type": "number", "description": "Monthly price in the coach's currency"},
            "currency": {"type": "string", "enum": ["GBP", "USD", "EUR"], "default": "GBP"}
          },
          "required": ["price"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "apply_store_template",
        "description": "Apply a visual template/theme to the coach's storefront",
        "parameters": {
          "type": "object",
          "properties": {
            "template_id": {"type": "string", "description": "Template identifier"},
            "niche": {"type": "string", "description": "Niche to auto-select best template"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "get_store_analytics",
        "description": "Get current analytics for the coach's store",
        "parameters": {
          "type": "object",
          "properties": {
            "period": {"type": "string", "enum": ["today", "this_week", "this_month", "all_time"]},
            "metrics": {
              "type": "array",
              "items": {"type": "string", "enum": ["visitors", "subscribers", "revenue", "blog_views", "live_attendees"]}
            }
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "get_niche_benchmarks",
        "description": "Get pricing and performance benchmarks for coaches in a specific niche",
        "parameters": {
          "type": "object",
          "properties": {
            "niche": {"type": "string"},
            "specialty": {"type": "string"}
          },
          "required": ["niche"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "schedule_live_session",
        "description": "Create and schedule a live streaming session",
        "parameters": {
          "type": "object",
          "properties": {
            "title": {"type": "string"},
            "date": {"type": "string", "format": "date"},
            "time": {"type": "string", "description": "Time in HH:MM format"},
            "duration_minutes": {"type": "integer", "default": 30},
            "description": {"type": "string"}
          },
          "required": ["title", "date", "time"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "generate_share_content",
        "description": "Generate a social media post for the coach to share their store",
        "parameters": {
          "type": "object",
          "properties": {
            "platform": {"type": "string", "enum": ["instagram_story", "instagram_post", "twitter", "whatsapp", "generic"]},
            "tone": {"type": "string", "enum": ["excited", "professional", "casual"]}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "update_scorecard",
        "description": "Mark a scorecard item as complete and update progress percentage",
        "parameters": {
          "type": "object",
          "properties": {
            "item": {"type": "string", "enum": ["profile_photo", "socials_connected", "blogs_published", "store_shared", "live_scheduled"]},
            "completed": {"type": "boolean"}
          },
          "required": ["item", "completed"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "setup_stripe",
        "description": "Initiate Stripe Connect onboarding flow for the coach",
        "parameters": {
          "type": "object",
          "properties": {
            "return_url": {"type": "string", "description": "URL to return to after Stripe setup"}
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "get_social_top_posts",
        "description": "Get the top-performing posts from a connected social account",
        "parameters": {
          "type": "object",
          "properties": {
            "platform": {"type": "string", "enum": ["instagram", "tiktok", "youtube"]},
            "count": {"type": "integer", "default": 5},
            "sort_by": {"type": "string", "enum": ["engagement", "recent", "views"]}
          },
          "required": ["platform"]
        }
      }
    }
  ]
}
```

## 4.3 — System Prompt

```
SYSTEM PROMPT FOR AVERY:

You are Avery, the AI onboarding assistant for KLIQ — a platform where 
coaches build their own branded coaching apps and stores.

YOUR PERSONALITY:
- Friendly, encouraging, and energetic (but not annoying)
- You speak like a helpful colleague, not a corporate bot
- Use emojis sparingly (1-2 per message, not every sentence)
- Keep messages SHORT — 2-4 sentences max per turn
- Always give the coach a clear next action or choice
- Celebrate wins genuinely but briefly

YOUR ROLE:
- Guide new coaches through setting up their store
- Do as much work FOR them as possible (write blogs, set up profile, etc.)
- Explain WHY each step matters using real data
- Adapt to the coach's pace and preferences
- Answer any questions about KLIQ

YOUR KNOWLEDGE:
- You know KLIQ's features: blogs, live streaming, 1:1 coaching, 
  subscriptions, digital products, courses, community feed, AMA
- You know niche benchmarks from real KLIQ data (pricing, subscriber 
  counts, revenue ranges)
- You know that blogs are the #1 retention driver (6.8x multiplier)
- You know that coaches who share their store URL on Day 1 get 
  subscribers 5x faster
- You know that live sessions drive 28pp retention lift

CONVERSATION RULES:
1. NEVER write more than 4 sentences before asking a question or 
   offering a choice
2. ALWAYS offer button options AND allow free-text responses
3. When the coach gives a free-text response, understand their intent 
   and act on it
4. If the coach asks to change something you wrote (bio, blog, etc.), 
   do it immediately — don't ask "are you sure?"
5. Show progress bar updates after each completed action
6. If the coach seems confused, simplify — don't add more information
7. If the coach wants to skip something, let them — but note you'll 
   remind them later
8. NEVER mention technical details (APIs, databases, etc.)
9. NEVER say "I'm just an AI" or apologise for being AI
10. If you don't know something, say "Let me check on that" and 
    escalate to human support

ONBOARDING PHASES (follow this order, but adapt):
1. Welcome & Discovery (name, niche, specialty)
2. Social Connect & Content Import (Instagram/TikTok/YouTube → blogs)
3. Profile Setup (photo, bio)
4. Pricing (with niche benchmarks)
5. Store Launch & Share
6. Next Steps (live session, ongoing tips)

CONTEXT AVAILABLE:
- Coach profile: {coach_profile}
- Onboarding state: {onboarding_state}
- Store state: {store_state}
- Social connections: {social_connections}
- Analytics: {analytics}
- Conversation history: {conversation_history}
```

## 4.4 — Conversation State Machine

```
                    ┌─────────────┐
                    │   START     │
                    │  (signup)   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  DISCOVERY  │ ← Name, niche, specialty
                    │             │   Free-text allowed
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
              ┌─────│   SOCIAL    │ ← Connect or skip
              │     │  CONNECT    │
              │     └──────┬──────┘
              │            │
         (skip)    ┌──────▼──────┐
              │     │  CONTENT    │ ← AI generates blogs
              │     │  IMPORT     │   from social OR niche
              │     └──────┬──────┘
              │            │
              └────▶┌──────▼──────┐
                    │  PROFILE    │ ← Photo, bio (AI-written)
                    │  SETUP      │   Free-text edits allowed
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  PRICING    │ ← Benchmarks shown
                    │             │   Free-text amount allowed
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  LAUNCH     │ ← Store goes live
                    │  & SHARE    │   Share options
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  NEXT STEPS │ ← Live session, Stripe
                    │             │   Ongoing relationship
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  ONGOING    │ ← Daily check-ins
                    │  ASSISTANT  │   Reactive Q&A
                    │             │   Proactive nudges
                    └─────────────┘

At ANY point, the coach can:
- Ask a question (Avery answers, then returns to flow)
- Request a change (Avery executes, then continues)
- Say "skip" (Avery notes it, moves on)
- Close the chat (Avery picks up where they left off next time)
```

## 4.5 — Database Schema

```sql
-- Conversation history
CREATE TABLE avery_conversations (
    id SERIAL PRIMARY KEY,
    coach_id INTEGER NOT NULL REFERENCES users(id),
    application_id INTEGER NOT NULL REFERENCES applications(id),
    
    -- Message
    role VARCHAR(20) NOT NULL, -- 'coach', 'avery', 'system'
    content TEXT NOT NULL,
    
    -- UI elements sent with message
    buttons JSONB, -- [{label, action, value}]
    preview JSONB, -- {type: 'blog'|'bio'|'store', content: ...}
    progress_pct INTEGER, -- progress bar value shown
    
    -- Function calls (if Avery took an action)
    function_name VARCHAR(100),
    function_args JSONB,
    function_result JSONB,
    
    -- Metadata
    phase VARCHAR(50), -- current onboarding phase
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_coach_conv (coach_id, created_at)
);

-- Coach preferences learned from conversation
CREATE TABLE avery_coach_context (
    id SERIAL PRIMARY KEY,
    coach_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Learned preferences
    preferred_name VARCHAR(100),
    tone_preference VARCHAR(20), -- casual, professional, energetic
    niche VARCHAR(50),
    specialty VARCHAR(100),
    
    -- Onboarding state
    current_phase VARCHAR(50) DEFAULT 'discovery',
    onboarding_complete BOOLEAN DEFAULT FALSE,
    onboarding_completed_at TIMESTAMP,
    
    -- Engagement
    total_messages_sent INTEGER DEFAULT 0,
    total_messages_received INTEGER DEFAULT 0,
    last_interaction_at TIMESTAMP,
    
    -- Nudge state
    last_nudge_sent_at TIMESTAMP,
    nudge_snooze_until TIMESTAMP,
    nudges_sent INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(coach_id)
);

-- Scheduled nudges
CREATE TABLE avery_scheduled_nudges (
    id SERIAL PRIMARY KEY,
    coach_id INTEGER NOT NULL,
    
    nudge_type VARCHAR(50) NOT NULL, -- 'day2_checkin', 'day3_stripe', etc.
    scheduled_for TIMESTAMP NOT NULL,
    
    -- Content
    message_template TEXT NOT NULL,
    buttons JSONB,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- pending, sent, cancelled, snoozed
    sent_at TIMESTAMP,
    coach_responded BOOLEAN DEFAULT FALSE,
    coach_responded_at TIMESTAMP,
    
    INDEX idx_scheduled (status, scheduled_for)
);
```

## 4.6 — API Endpoints

```
POST /api/avery/message
  Body: { coach_id, message, buttons_clicked: [{action, value}] }
  Returns: { 
    reply: "Avery's response text",
    buttons: [{label, action, value}],
    preview: {type, content},
    progress_pct: 60,
    actions_taken: [{function, result}]
  }

GET /api/avery/conversation/:coachId
  Returns: Last 50 messages for conversation continuity

GET /api/avery/context/:coachId
  Returns: Coach context (preferences, phase, state)

POST /api/avery/nudge/snooze
  Body: { coach_id, nudge_id, snooze_hours }

GET /api/avery/suggestions/:coachId
  Returns: Proactive suggestions based on coach state
```

## 4.7 — Message Flow (Backend)

```python
async def handle_avery_message(coach_id: int, user_message: str, buttons_clicked: list):
    
    # 1. Load context
    context = await get_coach_context(coach_id)
    history = await get_conversation_history(coach_id, limit=20)
    store_state = await get_store_state(context.application_id)
    analytics = await get_store_analytics(context.application_id)
    scorecard = await get_scorecard(context.application_id)
    
    # 2. Build messages for OpenAI
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.format(
            coach_profile=context.to_dict(),
            onboarding_state=scorecard.to_dict(),
            store_state=store_state.to_dict(),
            social_connections=context.social_connections,
            analytics=analytics.to_dict(),
            conversation_history=""  # included via message history
        )}
    ]
    
    # Add conversation history
    for msg in history:
        messages.append({
            "role": "user" if msg.role == "coach" else "assistant",
            "content": msg.content
        })
    
    # Add current message
    messages.append({"role": "user", "content": user_message})
    
    # 3. Call OpenAI with function calling
    response = await openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=AVERY_TOOLS,
        tool_choice="auto",
        stream=True  # Stream for real-time typing effect
    )
    
    # 4. Process response
    actions_taken = []
    
    # Handle function calls
    if response.tool_calls:
        for tool_call in response.tool_calls:
            result = await execute_function(
                coach_id=coach_id,
                function_name=tool_call.function.name,
                arguments=json.loads(tool_call.function.arguments)
            )
            actions_taken.append({
                "function": tool_call.function.name,
                "result": result
            })
            
            # Update scorecard based on action
            await update_scorecard_from_action(
                coach_id, 
                tool_call.function.name
            )
    
    # 5. Extract UI elements from response
    reply_text = response.content
    buttons = extract_buttons(reply_text)  # Parse [Button Text] patterns
    preview = extract_preview(reply_text)  # Parse preview blocks
    progress = calculate_progress(scorecard)
    
    # 6. Save to database
    await save_message(coach_id, "coach", user_message)
    await save_message(coach_id, "avery", reply_text, 
                       buttons=buttons, 
                       progress_pct=progress,
                       function_calls=actions_taken)
    
    # 7. Update context
    await update_coach_context(coach_id, 
                               last_interaction=now(),
                               total_messages_received=+1,
                               total_messages_sent=+1)
    
    return {
        "reply": reply_text,
        "buttons": buttons,
        "preview": preview,
        "progress_pct": progress,
        "actions_taken": actions_taken
    }


async def execute_function(coach_id, function_name, arguments):
    """Execute a KLIQ platform action on behalf of the coach"""
    
    FUNCTION_MAP = {
        "update_coach_profile": kliq_api.update_profile,
        "connect_social_account": kliq_api.initiate_oauth,
        "generate_blog_posts": kliq_api.generate_and_publish_blogs,
        "set_subscription_price": kliq_api.update_pricing,
        "apply_store_template": kliq_api.apply_template,
        "get_store_analytics": kliq_api.get_analytics,
        "get_niche_benchmarks": kliq_api.get_benchmarks,
        "schedule_live_session": kliq_api.create_live_session,
        "generate_share_content": kliq_api.generate_share_post,
        "update_scorecard": kliq_api.update_scorecard,
        "setup_stripe": kliq_api.initiate_stripe_connect,
        "get_social_top_posts": kliq_api.get_top_social_posts,
    }
    
    handler = FUNCTION_MAP.get(function_name)
    if handler:
        return await handler(coach_id=coach_id, **arguments)
    else:
        return {"error": f"Unknown function: {function_name}"}
```

---

# 5. CHAT UI DESIGN

## 5.1 — Chat Widget (Expanded from Current Avery)

```
┌──────────────────────────────────────────┐
│  Avery AI 🤖                    [─] [×]  │
│─────────────────────────────────────────│
│                                          │
│  ┌────────────────────────────────────┐  │
│  │ 🤖 Hey! 👋 I'm Avery, your setup │  │
│  │ assistant. I'm going to help you  │  │
│  │ build your coaching store in the  │  │
│  │ next few minutes.                 │  │
│  │                                   │  │
│  │ First — what should I call you?   │  │
│  └────────────────────────────────────┘  │
│                                          │
│  ████░░░░░░░░░░░░░░░░ 20%              │
│                                          │
│  ┌──────────────────────────────────┐    │
│  │ Type a message...          [Send]│    │
│  └──────────────────────────────────┘    │
│                                          │
└──────────────────────────────────────────┘
```

## 5.2 — Full-Screen Onboarding Mode

For the initial onboarding, Avery should take over the FULL SCREEN (not just the bottom-right widget). This prevents the coach from being distracted by the complex admin panel.

```
┌──────────────────────────────────────────────────────────────┐
│  KLIQ                                                        │
│                                                              │
│  ┌────────────────────────────┐  ┌────────────────────────┐  │
│  │                            │  │                        │  │
│  │     LIVE STORE PREVIEW     │  │    AVERY CONVERSATION  │  │
│  │                            │  │                        │  │
│  │  ┌──────────────────────┐  │  │  🤖 Hey Sarah! I've    │  │
│  │  │  [Hero Banner]       │  │  │  just published 3      │  │
│  │  │  Sarah Jones         │  │  │  blogs to your store.  │  │
│  │  │  HIIT & Strength     │  │  │                        │  │
│  │  │  Subscribe £12.99/mo │  │  │  Check out the preview │  │
│  │  │                      │  │  │  on the left! 👈       │  │
│  │  │  📝 Blog 1           │  │  │                        │  │
│  │  │  📝 Blog 2           │  │  │  How does it look?     │  │
│  │  │  📝 Blog 3           │  │  │                        │  │
│  │  │                      │  │  │  [Looks great! ✅]     │  │
│  │  │  🔗 sarahjones.      │  │  │  [Change something]    │  │
│  │  │     joinkliq.io      │  │  │                        │  │
│  │  └──────────────────────┘  │  │  ████████████░░ 70%    │  │
│  │                            │  │                        │  │
│  │  Updates in real-time as   │  │  ┌──────────────────┐  │  │
│  │  Avery makes changes! ←    │  │  │ Type...    [Send]│  │  │
│  │                            │  │  └──────────────────┘  │  │
│  └────────────────────────────┘  └────────────────────────┘  │
│                                                              │
│  [Skip setup — go to dashboard →]                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Key design decisions:**
- **Split screen:** Live preview on left, conversation on right
- **Real-time updates:** As Avery publishes blogs or changes the bio, the preview updates instantly
- **Skip option:** Always available but de-emphasised at the bottom
- **Progress bar:** Visible in the conversation panel
- **After onboarding complete:** Avery minimises to the bottom-right widget (current position)

## 5.3 — Button Types

| Type | Example | Behaviour |
|------|---------|-----------|
| **Action button** | [Connect Instagram] | Triggers OAuth popup or API call |
| **Choice button** | [£9.99/mo] [£14.99/mo] | Sends choice as message, Avery responds |
| **Navigation button** | [Preview blogs] | Opens preview panel or navigates |
| **Confirmation button** | [Publish all 3 ✅] | Executes action immediately |
| **Skip button** | [I'll do it later] | Moves to next phase, schedules reminder |

---

# 6. COST ANALYSIS

| Component | Cost Per Coach | Monthly (100 coaches) | Monthly (1,000 coaches) |
|-----------|---------------|----------------------|------------------------|
| OpenAI GPT-4o (onboarding: ~20 messages × 500 tokens) | ~$0.10 | $10 | $100 |
| OpenAI GPT-4o (ongoing: ~10 messages/week × 500 tokens) | ~$0.20/mo | $20 | $200 |
| Blog generation (3 initial + 2/week) | ~$0.08/mo | $8 | $80 |
| Social API calls | Free | Free | Free |
| Infrastructure (Redis, DB) | — | $20 | $50 |
| **Total** | **~$0.38/coach/month** | **~$58/month** | **~$430/month** |

**ROI:** If Avery increases 90-day retention from 8.8% to 25% (conservative), and each retained coach generates ~£50/month in platform fees, that's:
- 100 coaches × 16.2% retention lift × £50 = **£810/month additional revenue**
- Cost: £58/month
- **ROI: 14x**

---

# 7. EDGE CASES & GUARDRAILS

| Scenario | Handling |
|----------|---------|
| Coach asks something Avery can't do | "That's a great question! I'm not able to do that yet, but I can connect you with our support team → [Chat with support]" |
| Coach gets frustrated | Detect negative sentiment → "I hear you, Sarah. Want me to simplify things? I can set up the basics and you can customise later." |
| Coach asks about competitors | Redirect positively: "I'm not sure about [competitor], but here's what KLIQ offers..." |
| Coach provides inappropriate content | Content moderation filter on all AI-generated text. Flag for review. |
| OAuth fails (social connect) | "Hmm, the connection didn't go through. Want to try again, or skip this for now?" |
| AI generates poor blog content | Coach can tap "Regenerate" (max 3 times). If still unhappy: "No worries — you can edit it yourself or I'll try a completely different angle." |
| Coach closes chat mid-onboarding | Save state. Next time they open the admin panel: "Welcome back, Sarah! We were setting up your pricing. Want to continue?" |
| Coach returns after days | "Hey Sarah! It's been a few days. Your store is still at 60%. Want to pick up where we left off?" |
| Multiple coaches onboarding simultaneously | Each coach has isolated context. No cross-contamination. |
| Coach asks Avery to do something harmful | Refuse gracefully. "I can't do that, but here's what I can help with..." |
| Rate limiting | Max 50 messages per hour per coach. After limit: "I need a quick break! I'll be back in a few minutes." |

---

# 8. ANALYTICS & TRACKING

## Events to Track

| Event | Properties | Purpose |
|-------|-----------|---------|
| `avery_conversation_started` | coach_id, phase, device | Track onboarding starts |
| `avery_message_sent` | coach_id, phase, message_length, has_buttons | Message volume |
| `avery_button_clicked` | coach_id, button_label, button_action, phase | Which options coaches choose |
| `avery_function_executed` | coach_id, function_name, success, duration_ms | Action success rate |
| `avery_blog_generated` | coach_id, source, published, edited | Blog generation effectiveness |
| `avery_phase_completed` | coach_id, phase, duration_seconds | Time per phase |
| `avery_onboarding_completed` | coach_id, total_duration, phases_skipped | Full completion tracking |
| `avery_free_text_used` | coach_id, phase, intent_detected | How often coaches type vs click buttons |
| `avery_skip_clicked` | coach_id, phase, item_skipped | What coaches skip |
| `avery_nudge_sent` | coach_id, nudge_type, channel | Nudge delivery |
| `avery_nudge_responded` | coach_id, nudge_type, response_time | Nudge effectiveness |
| `avery_error` | coach_id, error_type, function_name | Error tracking |

## Key Metrics Dashboard

| Metric | Target |
|--------|--------|
| Onboarding completion rate (all 6 phases) | 65% |
| Avg onboarding time (phases 1-5) | Under 5 minutes |
| Blog publish rate (during onboarding) | 80% |
| Store share rate (during onboarding) | 40% |
| Free-text vs button usage ratio | 30% free-text / 70% buttons |
| Coach satisfaction (post-onboarding survey) | 4.5/5 |
| 7-day return rate (coaches who come back) | 60% |
| Nudge → action conversion rate | 25% |
| Avery ongoing usage (post-onboarding, weekly) | 40% of coaches |

---

# 9. IMPLEMENTATION PLAN

## Sprint Breakdown

| Sprint | Weeks | Deliverables |
|--------|-------|-------------|
| **Sprint 1** | 1-2 | Chat UI (full-screen onboarding mode + widget), conversation state machine, basic message flow (no AI yet — scripted responses) |
| **Sprint 2** | 3-4 | OpenAI integration with function calling, system prompt, 12 tool functions, streaming responses |
| **Sprint 3** | 5-6 | Social OAuth integration (Instagram, TikTok, YouTube), content import pipeline, AI blog generation within conversation |
| **Sprint 4** | 7-8 | Store preview (live-updating left panel), template application, profile/bio setup via conversation |
| **Sprint 5** | 9-10 | Ongoing assistant (daily check-ins, proactive nudges, reactive Q&A), analytics dashboard |
| **Sprint 6** | 11-12 | Polish, edge cases, A/B testing framework (Avery vs static onboarding), performance optimisation |

## Dependencies

```
Sprint 1 (Chat UI) ← No dependencies
    ↓
Sprint 2 (OpenAI + Functions) ← Needs Chat UI
    ↓
Sprint 3 (Social + Blogs) ← Needs Function Calling working
    ↓
Sprint 4 (Store Preview) ← Needs Blog generation + Profile functions
    ↓
Sprint 5 (Ongoing Assistant) ← Needs all above
    ↓
Sprint 6 (Polish + A/B Test) ← Needs everything stable
```

## Team Requirements

| Role | Allocation | Responsibilities |
|------|-----------|-----------------|
| **Full-Stack Engineer** | 100% | Chat UI, WebSocket/SSE streaming, state management |
| **Backend Engineer** | 100% | OpenAI integration, function execution, conversation engine, database |
| **Frontend Engineer** | 50% | Split-screen layout, live preview, button components, animations |
| **Designer** | 50% | Chat UI design, onboarding flow, celebration animations |
| **Product/AI** | 25% | System prompt tuning, conversation testing, edge case handling |

---

# 10. A/B TEST PLAN

Before full rollout, test Avery against the current onboarding:

| Variant | Description | % of Traffic |
|---------|-------------|-------------|
| **Control** | Current: niche question → empty dashboard | 30% |
| **Variant A** | Static scorecard (PRD 4) + 5-min storefront (PRD 2) | 30% |
| **Variant B** | Avery AI conversational onboarding (this PRD) | 40% |

**Primary metric:** 30-day retention rate
**Secondary metrics:** Time to first blog, time to first subscriber, store share rate, onboarding completion rate

**Minimum sample size:** 200 coaches per variant (600 total)
**Expected duration:** 6-8 weeks (based on current signup volume)

---

# 11. RISK REGISTER

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| AI generates off-brand or incorrect content | Medium | High | Content moderation API, coach review before publish, regenerate option |
| OpenAI API downtime | Low | High | Fallback to scripted responses for core onboarding flow |
| Coaches find AI conversation annoying | Medium | Medium | Always offer "Skip setup" option, A/B test against static flow |
| High API costs at scale | Low | Medium | Cache common responses, use GPT-4o-mini for simple queries, GPT-4o for generation |
| Social OAuth breaks (platform API changes) | Medium | Medium | Graceful fallback to niche-template blogs, monitor API status |
| Coach data privacy concerns | Low | High | Clear consent during social connect, data deletion on request, GDPR compliance |
| Conversation loops (coach and AI go in circles) | Medium | Low | Max 3 attempts per phase, then offer to skip or connect to human |
