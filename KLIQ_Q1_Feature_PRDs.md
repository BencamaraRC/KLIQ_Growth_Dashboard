# KLIQ Q1 2026 — Detailed Feature PRDs
## AI Blog Writer | 5-Min Storefront | Mobile→Desktop Bridge | Activation Scorecard | Anti-Bot

---

# CURRENT STATE ANALYSIS (From Admin Panel Screenshots)

## What Exists Today

### Signup → Onboarding Flow
1. **Create Account** — Email/password or Google SSO
2. **Single onboarding modal** — "Welcome to KLIQ: Which niche describes your business?" (Business / Lifestyle / Fitness / Executive / Something else?)
3. **Click "Finish"** → lands directly on App Builder page
4. **That's it.** One question, then full admin panel.

### "Your Store" Page — Real New Coach (Milo Silveira)

This is the **actual screen a brand-new coach sees** after the single niche question:

**Orange banner (top):** "Urgent! To start earning you need to setup stripe → Connect now"

**Top bar:**
- Coach name dropdown: "Milo Silveira"
- "Edit Profile" | "Change theme" buttons
- Subdomain URL: `milosilveira.joinkliq.io`
- Preview button

**Left sidebar (10 items — overwhelming for a new user):**
- Dashboard
- **Your Store** (currently selected)
- App →
- Features →
- Settings →
- Categories
- Media Storage
- Modules
- Help Center →
- Applications
- Self Serve →
- Logs

**Main content area (storefront editor):**
```
┌─────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────┐   │
│  │  [Purple/pink gradient hero banner]              │   │
│  │  ┌────┐                                          │   │
│  │  │ �️ │  ← Placeholder icon (NO profile photo)  │   │
│  │  └────┘                                          │   │
│  │  Milo Silveira    ← Name only (NO bio, NO niche) │   │
│  │                   Log in | Sign up                │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  + New section                                          │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  1:1 Book & Meet                    ↑ ↓  ✏️ Edit  🗑️  │
│  ┌──────────────────────────────────────────────────┐   │
│  │  🖼️ (no image)  │  1:1 with Milo Silveira       │   │
│  │                  │  60 mins                       │   │
│  │                  │  $ 0.10                        │   │
│  │                  │  [Book Now]                    │   │
│  └──────────────────────────────────────────────────┘   │
│  ↑ Auto-created by system (good!) but $0.10 is a       │
│    placeholder price — coach doesn't know to change it  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  Ask me anything                           ↑ ↓  🗑️     │
│                    🔧 Setup                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [Avery AI chatbot widget — bottom right corner]        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Key observations:**
1. **No profile photo** — just a placeholder icon in the hero
2. **No bio or category** — just the name "Milo Silveira"
3. **Generic purple gradient** banner — no personalisation
4. **1:1 session auto-created at $0.10** — system has auto-setup logic (good foundation!) but the price is meaningless and there's no image
5. **Ask me anything = empty** "Setup" state
6. **No blog section at all** — blogs aren't even listed as a default section, despite being the #1 retention driver
7. **No live streams section** — unlike the demo
8. **10 sidebar items** — Dashboard, Your Store, App, Features, Settings, Categories, Media Storage, Modules, Help Center, Applications, Self Serve, Logs — massively overwhelming for a new coach
9. **"Avery AI" chatbot** in bottom-right — existing AI assistant (potential to leverage for onboarding guidance)
10. **Stripe banner is the FIRST thing they see** — before they've even set up their store

### What's Good (Keep & Build On)
- **Subdomain system** already works (`coachname.joinkliq.io`) — no new infrastructure needed
- **Theme system** exists ("Change theme" button) — extend with niche-specific templates
- **Section-based storefront builder** — flexible, can add blog section automatically
- **Auto-created 1:1 session** — proves the system can auto-generate content; extend this to blogs
- **Avery AI chatbot** — already exists; could be enhanced to guide onboarding or replaced by scorecard
- **Edit Profile button** — exists but coach doesn't know to click it first
- **Stripe connection prompt** — important, but should come AFTER store is set up

### What's Broken (Fix These)

| Problem | Impact | PRD Fix |
|---------|--------|---------|
| **Only 1 onboarding question** (niche) — no profile photo, no social connect, no content setup | 73.3% never take a meaningful action | **5-Min Storefront** (7-step guided flow) |
| **Lands on "Your Store" with empty sections** — no guidance on what to do first or in what order | Coaches feel overwhelmed, don't know where to start | **Activation Scorecard** (prioritised 5-item checklist) |
| **No blog section** in the default storefront layout — not even listed | Blog = #1 retention driver (6.8x) but coaches don't know it exists | **AI Blog Writer** + auto-add blog section to storefront |
| **No profile photo, no bio** — hero area is a placeholder icon + name only | Store looks unfinished and unprofessional; no reason for visitors to subscribe | **5-Min Storefront** Step 3 (photo + AI bio) |
| **1:1 session at $0.10** — auto-created but with meaningless price and no image | Coaches don't realise they need to change this; visitors see a $0.10 session | **5-Min Storefront** Step 5 (pricing guidance with niche benchmarks) |
| **10 sidebar items visible immediately** — Dashboard, App, Features, Settings, Categories, Media Storage, Modules, Help Center, Applications, Self Serve, Logs | Cognitive overload for a new coach who just wants to set up their store | Consider **progressive disclosure** — show only Dashboard + Your Store initially, unlock others as coach progresses |
| **Stripe banner is first thing** — "Urgent!" feels aggressive before store is even set up | Adds anxiety; coach hasn't earned anything yet so Stripe feels premature | Move Stripe setup to **after** first content is published |
| **No mobile-to-desktop bridge** — mobile signups see same complex admin panel | Mobile 90-day retention = 2.1% vs 7.0% desktop | **Mobile→Desktop Bridge** (magic link + mobile quick wins) |
| **No bot protection** on signup | Inflated numbers, wasted resources | **Anti-Bot** (reCAPTCHA + email verify + pattern detection) |
| **Avery AI chatbot** exists but doesn't guide onboarding | Missed opportunity — could walk coaches through setup steps | Enhance Avery or replace with **Activation Scorecard** as primary guide |

---

## PROPOSED NEW FLOW (Current → New)

### Current Flow (3 steps, ~2 minutes, ends with empty page)
```
Create Account → Niche Question → Empty App Builder
     30 sec         10 sec          ❌ STUCK HERE
```

### New Flow (7 steps, ~5 minutes, ends with LIVE store + content)
```
Create Account → Template → Photo/Bio → AI Content → Price → LIVE Store → Share
     30 sec       30 sec     30 sec      60 sec auto   30 sec   instant    60 sec
                                            ↑
                                   Social connect happens here
                                   (feeds AI Blog Writer)
```

### Where Each PRD Plugs Into the Current UI

```
CURRENT ADMIN PANEL
┌──────────────────────────────────────────────────────────────┐
│  ┌─────────┐                                                 │
│  │ Sidebar │  ┌──────────────────────────────────────────┐   │
│  │         │  │                                          │   │
│  │ Dashboard│  │  ┌──── ACTIVATION SCORECARD (PRD 4) ──┐ │   │
│  │ Your    │  │  │ 🚀 YOUR LAUNCH PROGRESS    ████░ 60%│ │   │
│  │  space  │  │  │ ✅ Profile photo                     │ │   │
│  │ App     │  │  │ ✅ Socials connected                 │ │   │
│  │ Features│  │  │ ✅ 3 AI blogs published              │ │   │
│  │ Settings│  │  │ ⬜ Share your store link              │ │   │
│  │ Media   │  │  │ ⬜ Schedule first live session        │ │   │
│  │         │  │  └──────────────────────────────────────┘ │   │
│  │         │  │                                          │   │
│  │         │  │  ┌──── AI BLOG SECTION (PRD 1) ────────┐ │   │
│  │         │  │  │ 📝 AI Blog Drafts              [2]  │ │   │
│  │         │  │  │ "Why Rest Days Matter" [Review →]    │ │   │
│  │         │  │  │ "My Pre-Workout Guide" [Review →]    │ │   │
│  │         │  │  └──────────────────────────────────────┘ │   │
│  │         │  │                                          │   │
│  │         │  │  Ask me anything    [✅ Set up]           │   │
│  │         │  │  Live streams       [🔧 Setup →]         │   │
│  │         │  │  1:1 coaching       [🔧 Setup →]         │   │
│  │         │  │                                          │   │
│  └─────────┘  └──────────────────────────────────────────┘   │
│                                                              │
│  ┌──── MOBILE BRIDGE (PRD 3) ────────────────────────────┐   │
│  │ Detected: Mobile signup → "Email me a desktop link"   │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──── ANTI-BOT (PRD 5) ─────────────────────────────────┐   │
│  │ reCAPTCHA v3 on signup page (invisible)               │   │
│  │ Email verification (background, non-blocking)          │   │
│  │ Pattern detection (server-side)                        │   │
│  └───────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Storefront: Current vs Proposed

**CURRENT (empty store):**
```
┌─────────────────────────────────────────┐
│  [HERO BANNER - coach photo + name]     │
│  Log in | Sign up                       │
│  Home | Program | Library | Community   │
│                                         │
│         (nothing here)                  │
│                                         │
│  Powered by KLIQ                        │
└─────────────────────────────────────────┘
```

**PROPOSED (after 5-Min Storefront + AI Blog Writer):**
```
┌─────────────────────────────────────────┐
│  [HERO BANNER - coach photo + name]     │
│  [AI-written bio paragraph]             │
│  [Subscribe £14.99/mo] button           │
│  Home | Program | Library | Community   │
│                                         │
│  📝 LATEST ARTICLES                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ Blog 1  │ │ Blog 2  │ │ Blog 3  │   │
│  │ (AI)    │ │ (AI)    │ │ (AI)    │   │
│  └─────────┘ └─────────┘ └─────────┘   │
│                                         │
│  🎥 LIVE SESSIONS                       │
│  "Next session: TBD" [Notify me]        │
│                                         │
│  💬 ASK ME ANYTHING                     │
│  [Submit a question →]                  │
│                                         │
│  📱 Follow: [IG] [TikTok] [YouTube]    │
│  Powered by KLIQ                        │
└─────────────────────────────────────────┘
```

---

# PRD 1: AI BLOG WRITER FROM SOCIAL CONTENT

## 1.1 — Problem Statement

**Data:** Blog engagement in Week 1 = 50.8% coach retention (vs 7.5% without). It's the single strongest retention signal on the platform — a 6.8x multiplier.

**Reality:** <5% of coaches publish a blog in their first week. Most coaches are fitness professionals, not writers. They already have content on Instagram, TikTok, and YouTube — short captions, video scripts, workout tips — but they don't know how to turn that into blog posts.

**Opportunity:** If we can get 50% of coaches to publish 3+ blogs in Week 1 (via AI), we could increase 90-day retention from 8.8% to ~20%.

## 1.2 — Solution Overview

An AI-powered system that:
1. Connects to the coach's social media accounts
2. Pulls their best-performing content (posts, captions, video transcripts)
3. Generates blog post drafts using AI
4. Presents drafts for one-tap approval or light editing
5. Publishes to the coach's KLIQ store
6. Runs weekly to generate new drafts from new social posts

## 1.3 — User Flow

### First-Time Setup (During Onboarding)

```
Screen 1: "Connect Your Socials"
┌─────────────────────────────────────────┐
│                                         │
│  Let's import your best content and     │
│  turn it into blogs for your store.     │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ 📸 Connect Instagram            │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │ 🎵 Connect TikTok               │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │ ▶️  Connect YouTube              │    │
│  └─────────────────────────────────┘    │
│                                         │
│  [Skip for now]                         │
│                                         │
└─────────────────────────────────────────┘

Screen 2: "Importing Your Content..." (loading)
┌─────────────────────────────────────────┐
│                                         │
│  ⏳ Pulling your top posts...           │
│                                         │
│  Found 47 Instagram posts              │
│  Found 23 TikTok videos                │
│                                         │
│  Selecting your 5 best-performing...    │
│                                         │
└─────────────────────────────────────────┘

Screen 3: "Your AI Blog Drafts Are Ready!"
┌─────────────────────────────────────────┐
│                                         │
│  We turned your top posts into 3 blog   │
│  articles. Review and publish!          │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ 📝 "5 Morning Stretches That     │    │
│  │     Changed My Routine"          │    │
│  │     Based on your IG post (2.3K  │    │
│  │     likes)                       │    │
│  │     [Edit] [Publish ✓]           │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ 📝 "The Protein Myth: What I     │    │
│  │     Tell All My Clients"         │    │
│  │     Based on your TikTok (45K   │    │
│  │     views)                       │    │
│  │     [Edit] [Publish ✓]           │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ 📝 "My Go-To HIIT Workout for   │    │
│  │     Busy Professionals"          │    │
│  │     Based on your IG Reel (1.8K  │    │
│  │     likes)                       │    │
│  │     [Edit] [Publish ✓]           │    │
│  └─────────────────────────────────┘    │
│                                         │
│  [Publish All 3 →]                      │
│                                         │
└─────────────────────────────────────────┘
```

### Edit View

```
┌─────────────────────────────────────────┐
│  ← Back                    [Publish ✓]  │
│                                         │
│  Title:                                 │
│  ┌─────────────────────────────────┐    │
│  │ 5 Morning Stretches That Changed│    │
│  │ My Routine                      │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Cover Image: [Your IG photo]           │
│  [Change Image]                         │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ As a fitness coach, I get asked │    │
│  │ about morning routines more     │    │
│  │ than anything else. Here are    │    │
│  │ the 5 stretches I do every      │    │
│  │ single morning — and why they   │    │
│  │ work.                           │    │
│  │                                 │    │
│  │ ## 1. Cat-Cow Stretch           │    │
│  │ This is the first thing I do    │    │
│  │ when I get out of bed...        │    │
│  │                                 │    │
│  │ [... 300-500 words ...]         │    │
│  │                                 │    │
│  │ ---                             │    │
│  │ Want more tips like this?       │    │
│  │ Subscribe to [App Name] for     │    │
│  │ daily workouts and nutrition    │    │
│  │ guides.                         │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Category: [Fitness ▼]                  │
│  Tags: [stretching] [morning] [routine] │
│                                         │
│  ┌──────────┐  ┌──────────────────┐     │
│  │ Regenerate│  │ Publish ✓        │     │
│  └──────────┘  └──────────────────┘     │
│                                         │
│  Original post: [View on Instagram →]   │
│                                         │
└─────────────────────────────────────────┘
```

### Ongoing (Weekly Pipeline)

```
Push Notification (Monday AM):
"📝 2 new AI blog drafts ready from your latest posts → Review"

Dashboard Widget:
┌─────────────────────────────────────────┐
│  AI BLOG DRAFTS                    [2]  │
│                                         │
│  📝 "Why Rest Days Are Non-Negotiable"  │
│     From your IG post (Jan 12)          │
│     [Review →]                          │
│                                         │
│  📝 "My Pre-Workout Meal Prep Guide"    │
│     From your TikTok (Jan 14)           │
│     [Review →]                          │
│                                         │
└─────────────────────────────────────────┘
```

## 1.4 — Technical Architecture

### Social Media Integration

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Instagram    │     │   TikTok     │     │   YouTube    │
│  Graph API    │     │   API        │     │   Data API   │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│                 SOCIAL CONTENT INGESTION                 │
│                                                         │
│  1. OAuth token storage (encrypted)                     │
│  2. Content pull (posts, captions, images, metrics)     │
│  3. Engagement scoring (likes, comments, shares, views) │
│  4. Top 5 selection by engagement score                 │
│  5. Image/video URL extraction                          │
│  6. Caption/transcript extraction                       │
│                                                         │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   AI BLOG GENERATION                    │
│                                                         │
│  Input:                                                 │
│  - Social post caption/transcript                       │
│  - Post type (image, video, carousel, reel)             │
│  - Engagement metrics                                   │
│  - Coach profile (name, niche, bio)                     │
│  - Existing blog tone (if any)                          │
│                                                         │
│  LLM: OpenAI GPT-4o / Claude 3.5 Sonnet                │
│                                                         │
│  Output:                                                │
│  - Blog title                                           │
│  - Blog body (300-500 words, structured with headings)  │
│  - Category suggestion                                  │
│  - Tag suggestions                                      │
│  - CTA paragraph                                        │
│                                                         │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                    BLOG DRAFT QUEUE                      │
│                                                         │
│  Table: ai_blog_drafts                                  │
│  - id, coach_id, application_id                         │
│  - source_platform (instagram/tiktok/youtube)           │
│  - source_post_id, source_post_url                      │
│  - source_caption, source_engagement_score              │
│  - generated_title, generated_body                      │
│  - generated_category, generated_tags                   │
│  - cover_image_url                                      │
│  - status (draft/approved/published/rejected)           │
│  - created_at, published_at                             │
│  - coach_edits (text diff if edited)                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### API Specifications

#### Instagram Graph API
- **Scope:** `instagram_basic`, `instagram_manage_insights`, `pages_show_list`
- **Endpoints:**
  - `GET /{ig-user-id}/media` — List posts (id, caption, media_type, media_url, timestamp, permalink)
  - `GET /{media-id}/insights` — Engagement metrics (impressions, reach, likes, comments, shares)
- **Rate limit:** 200 calls/user/hour
- **Token refresh:** Long-lived tokens (60 days), auto-refresh via `GET /oauth/access_token?grant_type=fb_exchange_token`

#### TikTok API
- **Scope:** `user.info.basic`, `video.list`
- **Endpoints:**
  - `POST /v2/video/list/` — List videos (id, title, description, duration, cover_image_url, create_time)
  - Video stats: view_count, like_count, comment_count, share_count
- **Rate limit:** 600 requests/minute
- **Token refresh:** Refresh token flow (valid 365 days)
- **Note:** Video transcripts not available via API — use caption/description text only, or integrate Whisper API for audio transcription of downloaded videos

#### YouTube Data API v3
- **Scope:** `youtube.readonly`
- **Endpoints:**
  - `GET /channels?mine=true` — Get channel ID
  - `GET /search?channelId={id}&type=video&order=viewCount` — Top videos
  - `GET /videos?id={id}&part=snippet,statistics` — Video details + stats
  - `GET /captions?videoId={id}` — Caption tracks (for transcript)
- **Rate limit:** 10,000 units/day per project
- **Token refresh:** OAuth 2.0 refresh tokens

### AI Prompt Template

```
SYSTEM PROMPT:
You are a blog writer for fitness and wellness coaches. Your job is to 
transform short social media posts into engaging, informative blog articles.

Rules:
- Write in the coach's voice and tone (analyse their existing captions)
- Target 300-500 words
- Use clear headings (H2) to structure the content
- Include practical, actionable advice
- End with a CTA: "Want more [topic]? Subscribe to [App Name] for 
  [specific benefit]."
- Do NOT invent facts or statistics the coach didn't mention
- Do NOT use generic filler — every sentence should add value
- Match the coach's level of formality (casual vs professional)

USER PROMPT:
Coach name: {coach_name}
Coach niche: {coach_niche}
Coach bio: {coach_bio}
App name: {app_name}

Source post platform: {platform}
Source post caption: {caption}
Source post type: {post_type}
Engagement: {likes} likes, {comments} comments, {shares} shares

Previous blog titles (for tone reference): {existing_titles}

Generate a blog post based on this social media content. Include:
1. An engaging title (not clickbait)
2. A structured article with 2-4 headings
3. A closing CTA paragraph
```

### Cost Estimate

| Component | Cost Per Coach | Monthly (100 coaches) |
|-----------|---------------|----------------------|
| OpenAI GPT-4o (3 blogs × ~800 tokens out) | ~$0.02 | $2.00 |
| OpenAI GPT-4o (weekly: 2 blogs × 4 weeks) | ~$0.05 | $5.00 |
| Instagram API | Free | Free |
| TikTok API | Free | Free |
| YouTube API | Free (within quota) | Free |
| Image storage (S3/GCS) | ~$0.01 | $1.00 |
| **Total** | **~$0.08/coach/month** | **~$8/month** |

**AI cost is negligible.** Even at 1,000 coaches, it's ~$80/month.

## 1.5 — Database Schema

```sql
CREATE TABLE ai_blog_drafts (
    id SERIAL PRIMARY KEY,
    coach_id INTEGER NOT NULL REFERENCES users(id),
    application_id INTEGER NOT NULL REFERENCES applications(id),
    
    -- Source
    source_platform VARCHAR(20) NOT NULL, -- instagram, tiktok, youtube
    source_post_id VARCHAR(255) NOT NULL,
    source_post_url TEXT,
    source_caption TEXT,
    source_media_url TEXT,
    source_engagement_score INTEGER, -- composite score
    source_post_date TIMESTAMP,
    
    -- Generated content
    generated_title VARCHAR(255),
    generated_body TEXT,
    generated_category VARCHAR(100),
    generated_tags TEXT[], -- array of tags
    cover_image_url TEXT,
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft', -- draft, approved, published, rejected
    coach_edited BOOLEAN DEFAULT FALSE,
    coach_edit_diff TEXT, -- JSON diff of changes
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    published_at TIMESTAMP,
    
    UNIQUE(application_id, source_post_id) -- prevent duplicate generation
);

CREATE TABLE social_connections (
    id SERIAL PRIMARY KEY,
    coach_id INTEGER NOT NULL REFERENCES users(id),
    platform VARCHAR(20) NOT NULL, -- instagram, tiktok, youtube
    platform_user_id VARCHAR(255),
    platform_username VARCHAR(255),
    access_token TEXT NOT NULL, -- encrypted
    refresh_token TEXT, -- encrypted
    token_expires_at TIMESTAMP,
    last_sync_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(coach_id, platform)
);

CREATE TABLE social_posts_cache (
    id SERIAL PRIMARY KEY,
    social_connection_id INTEGER REFERENCES social_connections(id),
    platform VARCHAR(20) NOT NULL,
    post_id VARCHAR(255) NOT NULL,
    post_type VARCHAR(50), -- image, video, carousel, reel, short
    caption TEXT,
    media_url TEXT,
    permalink TEXT,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    engagement_score INTEGER, -- calculated composite
    posted_at TIMESTAMP,
    synced_at TIMESTAMP DEFAULT NOW(),
    used_for_blog BOOLEAN DEFAULT FALSE,
    
    UNIQUE(platform, post_id)
);
```

## 1.6 — Weekly Cron Job

```
Schedule: Every Monday at 6:00 AM UTC

For each coach with active social connections:
  1. Pull new posts since last_sync_at
  2. Calculate engagement scores
  3. Select top 2 unused posts (not already used_for_blog)
  4. Generate 2 blog drafts via AI
  5. Save to ai_blog_drafts with status='draft'
  6. Send push notification: "2 new AI blog drafts ready → Review"
  7. Update last_sync_at
```

## 1.7 — Success Metrics

| Metric | Baseline | 30-Day Target | 90-Day Target |
|--------|----------|--------------|--------------|
| Coaches connecting socials | 0% | 40% | 60% |
| Coaches with 3+ blogs in Week 1 | <5% | 50% | 65% |
| AI draft → published rate | N/A | 60% | 75% |
| Coach edit rate (vs publish as-is) | N/A | 30% | 40% |
| Blog reads per published AI blog | N/A | 15 | 30 |
| Coach 90-day retention (blog publishers) | 50.8% | 50% | 55% |

## 1.8 — Edge Cases & Guardrails

| Scenario | Handling |
|----------|---------|
| Coach has no social accounts | Skip social import, offer manual blog templates + AI writing assistant |
| Coach has <5 posts | Use all available posts, supplement with niche-specific prompts |
| Social post is just an image (no caption) | Use image recognition to describe content, generate blog from visual |
| Generated blog is low quality | Coach can tap "Regenerate" for a new version (max 3 regenerations) |
| Coach's social token expires | Send email: "Reconnect your [Platform] to keep getting AI blogs" |
| Duplicate content detection | Hash source_post_id to prevent re-generating from same post |
| Coach publishes then deletes | Soft delete, keep in database for analytics |
| Offensive/inappropriate content | Content moderation filter before publishing (OpenAI moderation API) |

---

# PRD 2: "STORE IN 5 MINUTES" WEB STOREFRONT FAST TRACK

## 2.1 — Problem Statement

**Data:** 74.5% of coaches drop off between completing onboarding and creating their first content. They face a blank dashboard with no content, no users, no revenue — just zeros.

**Current signup flow:** Create account → Password → Creator type → Onboarding steps → Blank dashboard. Total time: 5-10 minutes. Result: a blank page.

**New flow goal:** Create account → Template → Photo → AI content → Price → LIVE STORE in under 5 minutes. Result: a shareable URL with real content.

## 2.2 — User Flow (7 Steps, Under 5 Minutes)

### Step 1: Sign Up (30 seconds)

```
┌─────────────────────────────────────────┐
│                                         │
│  Create your coaching store             │
│                                         │
│  [Sign Up with Google]                  │
│                                         │
│  ─── or ───                             │
│                                         │
│  Name:     [________________]           │
│  Email:    [________________]           │
│  Password: [________________]           │
│                                         │
│  [Create Account →]                     │
│                                         │
│  Already have an account? [Log in]      │
│                                         │
└─────────────────────────────────────────┘
```

**Changes from current:**
- Remove creator type selection (detect from content later)
- Remove separate password requirements screen (inline validation)
- Add Google SSO prominently (currently 27.8% use SSO — make it 50%+)
- Email verification happens in background (don't block flow)

### Step 2: Choose Your Template (30 seconds)

```
┌─────────────────────────────────────────┐
│                                         │
│  Pick a look for your store             │
│                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ FITNESS │ │ WELLNESS│ │ BUSINESS│   │
│  │ [image] │ │ [image] │ │ [image] │   │
│  │ Bold,   │ │ Calm,   │ │ Clean,  │   │
│  │ energetic│ │ minimal │ │ profess.│   │
│  └─────────┘ └─────────┘ └─────────┘   │
│                                         │
│  ┌─────────┐                            │
│  │ CREATOR │                            │
│  │ [image] │                            │
│  │ Modern, │                            │
│  │ vibrant │                            │
│  └─────────┘                            │
│                                         │
│  You can change this anytime.           │
│                                         │
└─────────────────────────────────────────┘
```

**Each template includes:**
- Pre-set colour scheme + typography
- Layout structure (hero, about, content grid, pricing)
- Placeholder content that gets replaced by AI
- Mobile-responsive design

### Step 3: Your Photo & Bio (30 seconds)

```
┌─────────────────────────────────────────┐
│                                         │
│  Add your photo                         │
│                                         │
│       ┌───────────┐                     │
│       │           │                     │
│       │   📷 +    │                     │
│       │           │                     │
│       └───────────┘                     │
│                                         │
│  [Upload Photo]  [Take Selfie]          │
│  [Pull from Instagram]                  │
│                                         │
│  Your store name:                       │
│  ┌─────────────────────────────────┐    │
│  │ [Auto-filled from signup name]  │    │
│  └─────────────────────────────────┘    │
│                                         │
│  [Continue →]                           │
│                                         │
│  We'll write your bio automatically     │
│  from your social profiles.             │
│                                         │
└─────────────────────────────────────────┘
```

**If social connected:** Pull profile photo + bio from Instagram/TikTok. AI enhances bio for storefront context.

**If no social:** Coach uploads photo. AI generates bio from: name + template choice + any text they provide.

### Step 4: AI Content Generation (60 seconds — happens automatically)

```
┌─────────────────────────────────────────┐
│                                         │
│  ✨ Building your store...              │
│                                         │
│  ✅ Store created                       │
│  ✅ Bio written                         │
│  ✅ 3 blog posts generated              │
│  ⏳ Setting up your storefront...       │
│                                         │
│  ████████████░░░░░░░░ 65%              │
│                                         │
│  "Coaches who launch with content       │
│   get 6.8x more subscribers"            │
│                                         │
└─────────────────────────────────────────┘
```

**What happens in the background (parallel):**
1. Create application record in database
2. Provision subdomain: `coachname.joinkliq.io`
3. Apply selected template
4. Set profile photo + AI-generated bio
5. If social connected: generate 3 blog posts from top social content
6. If no social: generate 3 blog posts from niche templates
7. Create default subscription plan (editable)
8. Generate social share assets (OG image, pre-written post)

### Step 5: Set Your Price (30 seconds)

```
┌─────────────────────────────────────────┐
│                                         │
│  Set your subscription price            │
│                                         │
│  Coaches in your niche typically        │
│  charge:                                │
│                                         │
│  £5/mo ──────●────────── £50/mo         │
│                                         │
│  Your price: £ [14.99] /month           │
│                                         │
│  💡 Top fitness coaches on KLIQ charge  │
│     £10-35/month and earn £500-1,800    │
│     per month                           │
│                                         │
│  You can change this anytime.           │
│                                         │
│  [Continue →]                           │
│                                         │
└─────────────────────────────────────────┘
```

**Pricing benchmarks from our data:**

| Niche | Avg Price | Top Earner Price |
|-------|-----------|-----------------|
| Fitness (HIIT/Strength) | £9.96-19.50 | £35.90 (Jenn Lab Fit) |
| Wellness/Yoga | £10-28.45 | £28.45 (Lift Your Vibe) |
| Faith/Community | £22-30.46 | £30.46 (Besties in Jesus) |
| General Creator | £5.70-16.00 | £63.73 (NRFit) |

### Step 6: Your Store is LIVE (30 seconds)

```
┌─────────────────────────────────────────┐
│                                         │
│  🎉 Your store is LIVE!                │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │                                 │    │
│  │  [STORE PREVIEW]                │    │
│  │  coachname.joinkliq.io          │    │
│  │                                 │    │
│  │  Shows: photo, bio, 3 blogs,    │    │
│  │  subscription button            │    │
│  │                                 │    │
│  └─────────────────────────────────┘    │
│                                         │
│  Your URL:                              │
│  🔗 coachname.joinkliq.io  [Copy]      │
│                                         │
│  [View Your Store →]                    │
│  [Share on Social →]                    │
│                                         │
└─────────────────────────────────────────┘
```

### Step 7: Share on Social (60 seconds)

```
┌─────────────────────────────────────────┐
│                                         │
│  Share your store with your audience    │
│                                         │
│  Pre-written post:                      │
│  ┌─────────────────────────────────┐    │
│  │ "I just launched my coaching    │    │
│  │  store! Get exclusive workouts, │    │
│  │  nutrition tips, and live       │    │
│  │  sessions. Check it out 👇      │    │
│  │  coachname.joinkliq.io"         │    │
│  └─────────────────────────────────┘    │
│  [Edit message]                         │
│                                         │
│  ┌──────────┐ ┌──────────┐             │
│  │ 📸 Share  │ │ 💬 Share  │             │
│  │ Instagram │ │ WhatsApp │             │
│  │ Story     │ │          │             │
│  └──────────┘ └──────────┘             │
│  ┌──────────┐ ┌──────────┐             │
│  │ 🐦 Share  │ │ 📋 Copy   │             │
│  │ Twitter  │ │ Link     │             │
│  └──────────┘ └──────────┘             │
│                                         │
│  [Download QR Code]                     │
│                                         │
│  [Go to Dashboard →]                    │
│                                         │
└─────────────────────────────────────────┘
```

## 2.3 — Technical Requirements

### Template Engine

| Component | Technology | Notes |
|-----------|-----------|-------|
| Template storage | JSON schema per template | Colour palette, fonts, layout sections, placeholder text |
| Template rendering | React/Next.js SSR | Server-side rendered for SEO + fast load |
| Subdomain provisioning | Wildcard DNS + reverse proxy | `*.joinkliq.io` → route by subdomain |
| Image processing | Sharp.js / Cloudinary | Resize, crop, optimise profile photos |
| OG image generation | Satori / Puppeteer | Auto-generate social share preview image |

### Template Schema (JSON)

```json
{
  "id": "fitness_bold",
  "name": "Fitness - Bold",
  "category": "fitness",
  "colors": {
    "primary": "#FF4444",
    "secondary": "#1A1A2E",
    "background": "#FFFFFF",
    "text": "#333333",
    "accent": "#FF6B6B"
  },
  "fonts": {
    "heading": "Montserrat",
    "body": "Inter"
  },
  "sections": [
    {
      "type": "hero",
      "layout": "image_left",
      "fields": ["profile_photo", "store_name", "bio", "cta_button"]
    },
    {
      "type": "content_grid",
      "layout": "3_column",
      "fields": ["blog_cards"]
    },
    {
      "type": "pricing",
      "layout": "single_plan",
      "fields": ["price", "features_list", "subscribe_button"]
    },
    {
      "type": "about",
      "layout": "full_width",
      "fields": ["long_bio", "social_links"]
    }
  ],
  "placeholder_bio": "I'm a fitness coach passionate about helping you reach your goals. Subscribe for exclusive workouts, nutrition tips, and live coaching sessions.",
  "placeholder_features": [
    "Exclusive workout programs",
    "Weekly live sessions",
    "Nutrition guides & meal plans",
    "Community access",
    "Direct messaging with me"
  ]
}
```

### Subdomain Provisioning

```
1. Coach signs up with name "Sarah Jones"
2. System generates slug: "sarah-jones"
3. Check availability: sarah-jones.joinkliq.io
4. If taken: sarah-jones-fitness.joinkliq.io (append niche)
5. DNS: Wildcard *.joinkliq.io → KLIQ web server
6. Reverse proxy: extract subdomain → look up application_id → serve store
7. SSL: Wildcard certificate for *.joinkliq.io (Let's Encrypt or Cloudflare)
```

## 2.4 — Niche-Specific AI Content (No Social Connected)

If a coach doesn't connect social accounts, generate blogs from niche templates:

**Fitness template prompts:**
1. "Write a blog post about [coach name]'s approach to [HIIT/strength/yoga] training"
2. "Write a beginner's guide to [niche] from [coach name]'s perspective"
3. "Write a blog about common [niche] mistakes and how to avoid them"

**Wellness template prompts:**
1. "Write about [coach name]'s philosophy on holistic wellness"
2. "Write a guide to building a sustainable wellness routine"
3. "Write about the mind-body connection from [coach name]'s perspective"

## 2.5 — Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Time from signup to live store | Never (most don't launch) | Under 5 minutes |
| % of signups with live store in Day 1 | ~1% | 70% |
| % who share store URL in Day 1 | 0.3% | 25% |
| Store pages with 3+ blog posts | <5% | 65% |
| Bounce rate on store pages | Unknown | <50% |

---

# PRD 3: MOBILE → DESKTOP BRIDGE

## 3.1 — Problem Statement

**Data:** 47.4% of coaches sign up on mobile. Mobile 90-day retention is 2.1% vs 7.0% on desktop (3.3x gap). Mobile lifespan is 4.7 days vs 22.9 days on desktop.

**Why:** Content creation (writing blogs, building modules, setting up programs) is significantly harder on mobile. Coaches who sign up on mobile get stuck at the "create content" step.

**Solution:** Detect mobile signup → offer quick wins on mobile → bridge to desktop for content creation.

## 3.2 — User Flow

### Detection & Prompt (Immediately After Signup on Mobile)

```
┌─────────────────────────────────────────┐
│                                         │
│  Welcome! 🎉                           │
│                                         │
│  Quick tip: Most successful coaches     │
│  build their store on a laptop.         │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ 📧 Email me a link to continue  │    │
│  │    on my laptop                  │    │
│  └─────────────────────────────────┘    │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │ 📱 Continue on mobile            │    │
│  │    (quick setup available)       │    │
│  └─────────────────────────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

### If "Email me a link":

**Email sent immediately:**
```
Subject: Continue building your KLIQ store on desktop

Hi [Name],

Your store is waiting! Click below to pick up exactly 
where you left off — no need to log in again.

[Continue Building →] (magic link button)

This link expires in 7 days.

— The KLIQ Team
```

### If "Continue on mobile" — Mobile Quick Wins:

```
┌─────────────────────────────────────────┐
│                                         │
│  Let's do the quick stuff on mobile!    │
│                                         │
│  ✅ Account created                     │
│  ⬜ Take a profile photo (30 sec)       │
│  ⬜ Connect your socials (60 sec)       │
│  ⬜ Record a voice intro (30 sec)       │
│                                         │
│  Then we'll email you a link to         │
│  finish building on your laptop.        │
│                                         │
│  [Take Profile Photo →]                 │
│                                         │
└─────────────────────────────────────────┘
```

### Nudge Sequence (If No Desktop Open)

| Trigger | Timing | Channel | Message |
|---------|--------|---------|---------|
| Mobile signup, no desktop | +4 hours | Push | "Your store is waiting! Continue on desktop for the best experience → [Magic Link]" |
| Still no desktop | +24 hours | Email | "Quick tip: 70% of successful coaches build on desktop. Continue here → [Magic Link]" |
| Still no desktop | +48 hours | SMS | "Your KLIQ store is ready to build! Open on your laptop → [Short Link]" |
| Desktop opened | Immediately | In-app | "Welcome back! Let's pick up where you left off →" |

## 3.3 — Magic Link Technical Implementation

```
Generate Magic Link:
─────────────────────
1. Create JWT token:
   {
     "coach_id": 12345,
     "application_id": 67890,
     "device": "desktop",
     "onboarding_state": {
       "step_completed": 2,
       "profile_photo": "url",
       "social_connections": ["instagram"],
       "template_id": "fitness_bold"
     },
     "exp": now() + 7 days,
     "iat": now()
   }

2. Sign with server secret key (HS256)

3. Generate URL:
   https://admin.joinkliq.io/continue?token={jwt}

4. Store in database:
   magic_links table:
   - id, coach_id, token_hash, device_target
   - onboarding_state (JSON)
   - created_at, expires_at, used_at
   - is_used (boolean)

Consume Magic Link:
─────────────────────
1. User clicks link on desktop browser
2. Validate JWT (not expired, not used)
3. Create authenticated session (set cookie)
4. Mark magic link as used
5. Restore onboarding state from JWT payload
6. Redirect to next incomplete onboarding step
7. Log event: magic_link_used (device, time_since_creation)
```

### Database Schema

```sql
CREATE TABLE magic_links (
    id SERIAL PRIMARY KEY,
    coach_id INTEGER NOT NULL REFERENCES users(id),
    token_hash VARCHAR(64) NOT NULL, -- SHA-256 of JWT
    device_target VARCHAR(20) DEFAULT 'desktop',
    onboarding_state JSONB, -- serialised progress
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    is_used BOOLEAN DEFAULT FALSE,
    source_device VARCHAR(20), -- mobile, tablet
    target_device_actual VARCHAR(20), -- what device actually opened it
    
    INDEX idx_token_hash (token_hash),
    INDEX idx_coach_id (coach_id)
);

CREATE TABLE device_sessions (
    id SERIAL PRIMARY KEY,
    coach_id INTEGER NOT NULL,
    device_type VARCHAR(20) NOT NULL, -- mobile, desktop, tablet
    user_agent TEXT,
    first_seen_at TIMESTAMP DEFAULT NOW(),
    last_seen_at TIMESTAMP DEFAULT NOW(),
    session_count INTEGER DEFAULT 1,
    
    INDEX idx_coach_device (coach_id, device_type)
);
```

## 3.4 — Cross-Device State Sync

When a coach starts on mobile and continues on desktop, their progress must be seamless:

| State | Stored In | Synced Via |
|-------|-----------|-----------|
| Profile photo | CDN + database | URL in JWT payload |
| Social connections | OAuth tokens in DB | Shared coach_id |
| Template selection | application settings | Shared application_id |
| Onboarding step | onboarding_state JSON | JWT payload + DB |
| AI blog drafts | ai_blog_drafts table | Shared application_id |

## 3.5 — Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Mobile signups that open on desktop (24h) | Unknown (~5%) | 40% |
| Magic link click-through rate | N/A | 35% |
| Mobile-to-desktop bridge completion | N/A | 25% |
| Mobile signup 90-day retention (with bridge) | 2.1% | 7% |
| Time from mobile signup to desktop open | N/A | <4 hours (median) |

---

# PRD 4: COACH ACTIVATION SCORECARD

## 4.1 — Problem Statement

**Data:** 73.3% of coaches never take a meaningful action after signup. The onboarding flow completes, then coaches face a blank dashboard with no guidance on what to do next.

**Industry data:** Gamified onboarding checklists increase activation by 40% (Talana case study). Progress bars leverage the Zeigarnik Effect — people feel compelled to complete unfinished tasks.

## 4.2 — The Scorecard

### Dashboard Widget (Always Visible Until 100%)

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  🚀 YOUR LAUNCH PROGRESS                    ████░░ 60% │
│                                                         │
│  ✅ Profile photo uploaded              Done            │
│  ✅ Socials connected (Instagram)       Done            │
│  ✅ 3 AI blogs published                3/3             │
│  ⬜ Share your store link               0/1    [Do →]   │
│  ⬜ Schedule first live session          0/1    [Do →]   │
│                                                         │
│  ─────────────────────────────────────────────────────  │
│  🏆 Coaches who complete all 5 steps are 6.8x more     │
│     likely to be active at 90 days                      │
│                                                         │
│  ⏰ Day 3 of 7 — complete 2 more items to earn          │
│     "Launch Champion" badge                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### The 5 Items (Carefully Chosen from Data)

| # | Item | Why (Data) | Time | Completion Trigger |
|---|------|-----------|------|-------------------|
| 1 | **Upload profile photo** | Profile action = +4.2pp retention signal | 30 sec | `profile_image_added` event |
| 2 | **Connect social accounts** | Feeds AI blog writer; creates content pipeline | 60 sec | `social_connection.is_active = true` |
| 3 | **Publish 3 AI blogs** | Blog = #1 retention driver (+43pp) | 2 min | 3× `blog_published` events |
| 4 | **Share store link** | Only 0.3% currently do this; drives first visitors | 30 sec | `copy_url_clicked` OR `share_url_clicked` event |
| 5 | **Schedule first live session** | Live sessions = +28pp retention lift | 2 min | `live_session_created` event |

**Why 5 items:**
- Industry best practice: 3-5 items (not 12)
- Each takes under 2 minutes
- Total: under 10 minutes to 100%
- Every item produces a visible, meaningful result
- Each is backed by retention data

### Progress Bar Psychology

| Progress | Visual | Psychological Effect |
|----------|--------|---------------------|
| 0% | ░░░░░░░░░░ | "I haven't started" — low motivation |
| **20%** (start here) | **██░░░░░░░░** | **Pre-fill 1 item (account created) to trigger Zeigarnik Effect** |
| 40% | ████░░░░░░ | "I'm almost halfway" — momentum building |
| 60% | ██████░░░░ | "More than half done" — strong pull to finish |
| 80% | ████████░░ | "So close!" — very high completion drive |
| 100% | ██████████ | Celebration! Confetti + badge + congratulations |

**Key design decision:** Start the bar at 20% (1/5 complete — "Account created"). Never show 0%. This leverages the endowed progress effect — people who feel they've already started are more likely to finish.

### Celebration Moments

| Milestone | Animation | Message | Sound |
|-----------|-----------|---------|-------|
| Each item completed | Checkmark animation + bar fills | "Nice! [X] of 5 complete" | Soft chime |
| 60% (3/5) | Confetti burst | "You're ahead of 72% of new coaches!" | Celebration sound |
| 100% (5/5) | Full-screen confetti + badge | "🏆 LAUNCH CHAMPION! You've done what the top 8.8% do!" | Fanfare |

### Badge System

```
┌─────────────────────────────────────────┐
│                                         │
│  🏆 LAUNCH CHAMPION                    │
│                                         │
│  Awarded to [Coach Name]               │
│  Completed all 5 launch steps          │
│  in [X] days                           │
│                                         │
│  Only 8.8% of coaches achieve this.    │
│                                         │
│  [Share Badge on Social →]             │
│                                         │
└─────────────────────────────────────────┘
```

Badge appears on:
- Coach's dashboard (permanent)
- Coach's public storefront (trust signal for users)
- Coach's profile in any future KLIQ directory

## 4.3 — Nudge Sequence

| Trigger | Timing | Channel | Message |
|---------|--------|---------|---------|
| Signup complete, scorecard at 20% | Immediately | In-app | Scorecard appears on dashboard |
| Scorecard at 20% after 2 hours | +2h | Push | "Your store is almost ready! Complete step 2 to get ahead →" |
| Scorecard < 60% | Day 2 AM | Email | "You're [X]% through your launch checklist. Complete [next item] today → [Deeplink]" |
| Blogs not published | Day 2 PM | Push | "Your AI blogs are ready to review! Publish in 1 tap →" |
| Store not shared | Day 3 | Push | "Your store is live but nobody knows! Share your link →" |
| No live session | Day 4 | Push | "Top coaches go live in their first week. Schedule yours →" |
| Scorecard at 80% | On event | Push | "SO CLOSE! Just 1 more item to earn Launch Champion →" |
| 100% complete | On event | Push + Email | "🏆 You're a Launch Champion! Here's what to do next →" |
| Day 7, scorecard < 100% | Day 7 | Email | "Your launch week is ending! [X] items left. Complete now →" |

## 4.4 — Database Schema

```sql
CREATE TABLE coach_scorecard (
    id SERIAL PRIMARY KEY,
    coach_id INTEGER NOT NULL REFERENCES users(id),
    application_id INTEGER NOT NULL REFERENCES applications(id),
    
    -- Items (boolean)
    profile_photo_done BOOLEAN DEFAULT FALSE,
    profile_photo_at TIMESTAMP,
    
    socials_connected_done BOOLEAN DEFAULT FALSE,
    socials_connected_at TIMESTAMP,
    socials_platform VARCHAR(20), -- which platform connected first
    
    blogs_published_done BOOLEAN DEFAULT FALSE,
    blogs_published_at TIMESTAMP,
    blogs_published_count INTEGER DEFAULT 0,
    
    store_shared_done BOOLEAN DEFAULT FALSE,
    store_shared_at TIMESTAMP,
    store_shared_channel VARCHAR(50), -- instagram, whatsapp, twitter, copy
    
    live_scheduled_done BOOLEAN DEFAULT FALSE,
    live_scheduled_at TIMESTAMP,
    
    -- Computed
    completion_pct INTEGER DEFAULT 20, -- starts at 20% (account created)
    completed_at TIMESTAMP, -- when 100% reached
    days_to_complete INTEGER, -- days from signup to 100%
    
    -- Badge
    badge_earned BOOLEAN DEFAULT FALSE,
    badge_shared BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(coach_id, application_id)
);

CREATE TABLE scorecard_nudges (
    id SERIAL PRIMARY KEY,
    coach_id INTEGER NOT NULL,
    nudge_type VARCHAR(50) NOT NULL, -- e.g., 'day2_blog_reminder'
    channel VARCHAR(20) NOT NULL, -- push, email, in_app
    sent_at TIMESTAMP DEFAULT NOW(),
    opened_at TIMESTAMP,
    acted_at TIMESTAMP, -- when coach completed the nudged action
    
    INDEX idx_coach_nudge (coach_id, nudge_type)
);
```

## 4.5 — API Endpoints

```
GET  /api/scorecard/:applicationId
     → Returns current scorecard state + completion %

POST /api/scorecard/:applicationId/check
     → Recalculates scorecard from events (idempotent)

POST /api/scorecard/:applicationId/share-badge
     → Generates shareable badge image + social post
```

## 4.6 — Success Metrics

| Metric | Current | 30-Day Target | 90-Day Target |
|--------|---------|--------------|--------------|
| Coaches reaching 100% | ~1% (est.) | 30% | 50% |
| Coaches reaching 60%+ | ~5% (est.) | 55% | 70% |
| Avg items completed (of 5) | ~1 | 3.5 | 4.0 |
| Days to 100% (median) | Never | 3 days | 2 days |
| Badge share rate | N/A | 15% | 25% |
| Nudge → action conversion | N/A | 20% | 30% |

---

# PRD 5: ANTI-BOT & EMAIL VERIFICATION

## 5.1 — Problem Statement

**Data:** Significant bot activity detected in signup data. Pattern: scrambled Gmail addresses with random dots + numbers, all from "tablet" devices, all "manual" login type.

Examples:
- `vap.a.fu.r.izak1.9.2@gmail.com` (tablet, manual)
- `o.fi.n.uv.if.u.95@gmail.com` (tablet, manual)
- `m.ig.o.qaqa.gi.v.o00@gmail.com` (tablet, manual)

These bots inflate signup numbers, waste resources, and pollute analytics.

## 5.2 — Solution: Three Layers of Protection

### Layer 1: reCAPTCHA v3 (Invisible)

**What:** Google reCAPTCHA v3 runs in the background and scores each user 0.0-1.0 (1.0 = definitely human).

**Implementation:**
```
1. Add reCAPTCHA v3 script to signup page
2. On form submit, get reCAPTCHA token
3. Send token to backend with signup request
4. Backend verifies token with Google API
5. Score < 0.3 → Block signup, show "Please try again"
6. Score 0.3-0.7 → Allow but flag for review
7. Score > 0.7 → Allow (human)
```

**Technical:**
```html
<!-- Frontend -->
<script src="https://www.google.com/recaptcha/api.js?render=SITE_KEY"></script>
<script>
  grecaptcha.ready(function() {
    grecaptcha.execute('SITE_KEY', {action: 'signup'}).then(function(token) {
      document.getElementById('recaptcha_token').value = token;
    });
  });
</script>
```

```python
# Backend verification
import requests

def verify_recaptcha(token):
    response = requests.post(
        'https://www.google.com/recaptcha/api/siteverify',
        data={
            'secret': RECAPTCHA_SECRET_KEY,
            'response': token
        }
    )
    result = response.json()
    return result.get('score', 0), result.get('success', False)
```

**Cost:** Free for up to 1M assessments/month.

### Layer 2: Email Verification

**What:** After signup, send a verification email. Coach must click the link before accessing the dashboard.

**Flow:**
```
1. Coach submits signup form
2. Account created with status='unverified'
3. Email sent: "Verify your email to continue → [Link]"
4. Link contains JWT token (expires in 24 hours)
5. Coach clicks link → status='verified' → redirect to onboarding
6. If not verified in 24h → send reminder email
7. If not verified in 72h → mark as abandoned
```

**Important:** Don't block the ENTIRE flow. Let the coach proceed with template selection and photo upload while verification happens in the background. Only block at "Publish Store" step if still unverified.

```sql
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN email_verified_at TIMESTAMP;
ALTER TABLE users ADD COLUMN verification_token_hash VARCHAR(64);
ALTER TABLE users ADD COLUMN verification_sent_at TIMESTAMP;
```

### Layer 3: Pattern Detection (Heuristic Rules)

**Rules engine to flag suspicious signups:**

```python
def calculate_bot_score(signup_data):
    score = 0
    
    # Rule 1: Scrambled Gmail pattern
    email = signup_data['email']
    if email.endswith('@gmail.com'):
        local = email.split('@')[0]
        dot_count = local.count('.')
        digit_count = sum(c.isdigit() for c in local)
        if dot_count >= 4 and digit_count >= 2:
            score += 40  # Strong bot signal
    
    # Rule 2: Tablet + manual login
    if signup_data['device'] == 'tablet' and signup_data['login_type'] == 'manual':
        score += 20
    
    # Rule 3: Multiple signups from same IP in short window
    recent_from_ip = count_signups_from_ip(
        signup_data['ip'], 
        window_hours=1
    )
    if recent_from_ip >= 3:
        score += 30
    
    # Rule 4: Signup completed in < 5 seconds (too fast for human)
    if signup_data['time_on_form_seconds'] < 5:
        score += 25
    
    # Rule 5: No mouse movement / touch events detected
    if not signup_data.get('has_interaction_events'):
        score += 15
    
    # Rule 6: Known bot user agent patterns
    if is_known_bot_ua(signup_data['user_agent']):
        score += 50
    
    return min(score, 100)

# Thresholds
# 0-30: Human → allow
# 31-60: Suspicious → allow but flag for review
# 61-100: Likely bot → block or require additional verification
```

### Database Schema

```sql
CREATE TABLE signup_security (
    id SERIAL PRIMARY KEY,
    coach_id INTEGER REFERENCES users(id),
    
    -- reCAPTCHA
    recaptcha_score DECIMAL(3,2),
    recaptcha_action VARCHAR(50),
    
    -- Bot detection
    bot_score INTEGER DEFAULT 0,
    bot_flags TEXT[], -- array of triggered rules
    
    -- Email verification
    email_verified BOOLEAN DEFAULT FALSE,
    verification_attempts INTEGER DEFAULT 0,
    
    -- Request metadata
    ip_address INET,
    user_agent TEXT,
    device_type VARCHAR(20),
    time_on_form_seconds INTEGER,
    has_interaction_events BOOLEAN,
    
    -- Status
    status VARCHAR(20) DEFAULT 'allowed', -- allowed, flagged, blocked
    reviewed_by VARCHAR(100), -- admin who reviewed (if flagged)
    reviewed_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for IP rate limiting
CREATE INDEX idx_ip_created ON signup_security(ip_address, created_at);
```

## 5.3 — Admin Dashboard for Flagged Signups

```
┌─────────────────────────────────────────────────────────┐
│  FLAGGED SIGNUPS                           [This Week]  │
│                                                         │
│  12 flagged | 3 blocked | 9 pending review              │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ vap.a.fu.r.izak1.9.2@gmail.com                 │    │
│  │ Bot score: 80 | reCAPTCHA: 0.2 | tablet/manual │    │
│  │ Flags: scrambled_gmail, tablet_manual, fast_form│    │
│  │ [Block] [Allow] [Investigate]                   │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ o.fi.n.uv.if.u.95@gmail.com                    │    │
│  │ Bot score: 60 | reCAPTCHA: 0.4 | tablet/manual │    │
│  │ Flags: scrambled_gmail, tablet_manual           │    │
│  │ [Block] [Allow] [Investigate]                   │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 5.4 — Rate Limiting

```python
# Rate limits
RATE_LIMITS = {
    'signup_per_ip_per_hour': 3,
    'signup_per_ip_per_day': 10,
    'verification_emails_per_account': 5,
    'magic_links_per_account_per_day': 3,
}

# Implementation: Redis-based sliding window
def check_rate_limit(key, limit, window_seconds):
    current = redis.incr(key)
    if current == 1:
        redis.expire(key, window_seconds)
    return current <= limit
```

## 5.5 — Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Bot signups per month | ~50-100 (est.) | <5 |
| False positive rate (real users blocked) | N/A | <1% |
| Email verification rate (24h) | N/A | 80% |
| Time to verify email (median) | N/A | <10 minutes |
| Flagged signups reviewed within 24h | N/A | 100% |

## 5.6 — Rollout Plan

| Week | Action |
|------|--------|
| 1 | Add reCAPTCHA v3 (monitor only, don't block) |
| 2 | Analyse reCAPTCHA scores, set blocking threshold |
| 3 | Enable blocking for score < 0.3 |
| 4 | Add email verification (non-blocking during onboarding) |
| 5 | Add pattern detection rules (flag only, don't block) |
| 6 | Enable blocking for bot_score > 60 |
| 7 | Build admin review dashboard |
| 8 | Add rate limiting |

---

# IMPLEMENTATION TIMELINE

## Sprint Plan (2-Week Sprints)

| Sprint | Dates | Focus | Deliverables |
|--------|-------|-------|-------------|
| **Sprint 1** | Weeks 1-2 | Anti-Bot + Email Verify | reCAPTCHA v3, email verification, pattern detection |
| **Sprint 2** | Weeks 3-4 | 5-Min Storefront (Part 1) | Template engine, subdomain provisioning, signup flow redesign |
| **Sprint 3** | Weeks 5-6 | 5-Min Storefront (Part 2) + AI Blog | Social OAuth, AI blog generation pipeline, store preview |
| **Sprint 4** | Weeks 7-8 | AI Blog Writer (Full) | Weekly cron, edit UI, publish flow, content queue |
| **Sprint 5** | Weeks 9-10 | Mobile→Desktop Bridge | Magic links, device detection, cross-device state sync, nudge sequence |
| **Sprint 6** | Weeks 11-12 | Activation Scorecard | Scorecard UI, event tracking, nudge engine, badge system, celebrations |

## Dependencies

```
Anti-Bot (Sprint 1) ← No dependencies, ship first
    ↓
5-Min Storefront (Sprint 2-3) ← Needs template engine
    ↓
AI Blog Writer (Sprint 3-4) ← Needs social OAuth from Storefront
    ↓
Mobile→Desktop Bridge (Sprint 5) ← Needs storefront flow to bridge TO
    ↓
Activation Scorecard (Sprint 6) ← Needs all above features as checklist items
```

## Team Allocation

| Role | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 | Sprint 5 | Sprint 6 |
|------|----------|----------|----------|----------|----------|----------|
| **Full-Stack 1** | reCAPTCHA | Templates | Store UI | Blog Edit UI | Magic Links | Scorecard UI |
| **Full-Stack 2** | Email verify | Subdomain | Social OAuth | Blog Queue | Nudge Seq | Badge System |
| **Backend** | Pattern detect | API routes | AI pipeline | Cron job | State sync | Event tracking |
| **Designer** | — | Templates | Store flow | Blog flow | Bridge flow | Scorecard + celebrations |
