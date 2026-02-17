# AVERY AI — Technical Specification & Sprint Plan
## Engineering Documentation for KLIQ Conversational Onboarding Assistant

---

# PHASE 1: CHAT UI & CONVERSATION FRAMEWORK (Weeks 1-2)

## Architecture Decision
Avery is a React component embedded in the existing KLIQ admin panel. Full-screen mode overlays during onboarding; widget mode (bottom-right) post-onboarding. Shares auth, routing, and state with admin panel.

---

## Ticket 1.1: Chat Widget Component

**Type:** Frontend | **Estimate:** 3 days | **Priority:** P0

### File Structure
```
src/components/avery/
  AveryProvider.tsx        — Context provider, manages state
  AveryWidget.tsx          — Bottom-right floating widget
  AveryChatPanel.tsx       — Expanded chat panel
  AveryFullScreen.tsx      — Full-screen onboarding layout
  AveryStorePreview.tsx    — Left panel store preview (Phase 4)
  components/
    MessageBubble.tsx      — Individual message (coach or Avery)
    ButtonGroup.tsx        — Action/choice buttons below messages
    ProgressBar.tsx        — Onboarding progress indicator
    TypingIndicator.tsx    — "Avery is typing..." animation
    PreviewCard.tsx        — Blog/bio/store preview inline
    CelebrationOverlay.tsx — Confetti/badge animations
  hooks/
    useAveryChat.ts        — WebSocket connection + message state
    useAveryContext.ts     — Coach context (phase, preferences)
    useOnboardingState.ts  — Scorecard progress tracking
  types/
    avery.types.ts         — TypeScript interfaces
```

### Core TypeScript Interfaces

```typescript
interface AveryState {
  mode: 'minimised' | 'expanded' | 'fullscreen';
  messages: AveryMessage[];
  isTyping: boolean;
  progressPct: number;
  currentPhase: OnboardingPhase;
  coachContext: CoachContext;
  unreadCount: number;
}

interface AveryMessage {
  id: string;
  role: 'coach' | 'avery' | 'system';
  content: string;
  timestamp: Date;
  buttons?: AveryButton[];
  preview?: AveryPreview;
  progressPct?: number;
  functionCalls?: FunctionCallResult[];
}

interface AveryButton {
  label: string;
  action: string;
  value?: string;
  variant: 'primary' | 'secondary' | 'skip';
  icon?: string;
}

interface AveryPreview {
  type: 'blog' | 'bio' | 'store' | 'share_post' | 'analytics';
  title?: string;
  content: string;
  imageUrl?: string;
  actions?: AveryButton[];
}

type OnboardingPhase = 'discovery' | 'social_connect' | 'content_import' | 'profile_setup' | 'pricing' | 'launch' | 'next_steps' | 'complete';
```

### Acceptance Criteria
- [ ] Widget renders in bottom-right with Avery icon + unread badge
- [ ] Full-screen mode: split layout (60% preview / 40% chat)
- [ ] Smooth transitions between minimised → expanded → full-screen
- [ ] Mobile responsive (full-width on mobile, preview hidden)
- [ ] Persists across page navigation

### Styling (Design Tokens)
```css
:root {
  --avery-primary: #6C5CE7;
  --avery-msg-coach: #6C5CE7;
  --avery-msg-avery: #F0F0F5;
  --avery-border-radius: 16px;
  --avery-font: 'Inter', sans-serif;
}
```

---

## Ticket 1.2: Real-Time Messaging (WebSocket)

**Type:** Full-Stack | **Estimate:** 3 days | **Priority:** P0

### WebSocket Protocol

```typescript
// Client → Server
interface ClientMessage {
  type: 'coach_message' | 'button_click' | 'typing_start' | 'typing_stop';
  payload: { text?: string; button?: AveryButton; };
  messageId: string;
}

// Server → Client
interface ServerMessage {
  type: 'avery_message' | 'avery_typing' | 'avery_stream_chunk' | 'avery_stream_end'
      | 'function_executing' | 'function_complete' | 'progress_update'
      | 'store_preview_update' | 'trigger_oauth' | 'error';
  payload: any;
  messageId: string;
}
```

### Backend WebSocket Server

```typescript
import { WebSocketServer } from 'ws';

wss.on('connection', async (ws, req) => {
  const coachId = await authenticateWebSocket(req);
  if (!coachId) { ws.close(4001, 'Unauthorized'); return; }
  
  const context = await loadCoachContext(coachId);
  
  if (!context.hasInteracted) {
    await sendWelcomeMessage(ws, context);
  } else {
    await sendResumeMessage(ws, context);
  }
  
  ws.on('message', async (data) => {
    const msg = JSON.parse(data.toString());
    switch (msg.type) {
      case 'coach_message': await handleCoachMessage(ws, coachId, msg.payload.text); break;
      case 'button_click': await handleButtonClick(ws, coachId, msg.payload.button); break;
    }
  });
  
  ws.on('close', () => saveConversationState(coachId));
});
```

### Streaming Response Handler

```typescript
async function streamAveryResponse(ws, coachId, openaiStream) {
  ws.send(JSON.stringify({ type: 'avery_typing', payload: { isTyping: true } }));
  
  let fullContent = '';
  for await (const chunk of openaiStream) {
    const delta = chunk.choices[0]?.delta;
    if (delta?.content) {
      fullContent += delta.content;
      ws.send(JSON.stringify({ type: 'avery_stream_chunk', payload: { text: delta.content } }));
    }
  }
  
  ws.send(JSON.stringify({ type: 'avery_stream_end' }));
  ws.send(JSON.stringify({ type: 'avery_typing', payload: { isTyping: false } }));
  
  await saveMessage(coachId, 'avery', fullContent);
}
```

---

## Ticket 1.3: Conversation State Machine

**Type:** Backend | **Estimate:** 2 days | **Priority:** P0

```typescript
const PHASE_ORDER = ['discovery','social_connect','content_import','profile_setup','pricing','launch','next_steps'];

const PHASE_COMPLETION = {
  discovery: (ctx) => !!ctx.preferredName && !!ctx.niche,
  social_connect: (ctx) => ctx.socialConnections.length > 0, // OR skipped
  content_import: (ctx) => ctx.blogCount >= 3,               // OR skipped
  profile_setup: (ctx) => ctx.hasProfilePhoto && ctx.hasBio,
  pricing: (ctx) => ctx.subscriptionPrice > 0,
  launch: (ctx) => ctx.storeShared,
  next_steps: () => true,
};

// Each phase has: onEnter(), onMessage(), onButtonClick()
// At ANY point coach can: ask a question, request a change, say "skip", close chat
```

### Phase Handler Example (Discovery)

```typescript
discovery: {
  async onEnter(ws, context) {
    if (!context.preferredName) {
      return sendMessage(ws, {
        content: "Hey! 👋 I'm Avery, your setup assistant. First — what should I call you?",
        progressPct: 20,
      });
    }
    if (!context.niche) {
      return sendMessage(ws, {
        content: `Great, ${context.preferredName}! What kind of coaching do you do?`,
        buttons: [
          { label: 'Fitness & Training', action: 'set_niche', value: 'fitness', variant: 'secondary' },
          { label: 'Wellness & Mindfulness', action: 'set_niche', value: 'wellness', variant: 'secondary' },
          { label: 'Business & Executive', action: 'set_niche', value: 'business', variant: 'secondary' },
          { label: 'Lifestyle & Creator', action: 'set_niche', value: 'lifestyle', variant: 'secondary' },
        ],
      });
    }
  },
  async onMessage(ws, context, message) {
    if (!context.preferredName) {
      context.preferredName = extractName(message);
      return this.onEnter(ws, context);
    }
    if (!context.specialty) {
      context.specialty = message;
      return completePhase(ws, context, 'discovery');
    }
  },
}
```

---

## Ticket 1.4: Database Tables

**Type:** Backend | **Estimate:** 1 day | **Priority:** P0

```sql
CREATE TABLE avery_messages (
    id BIGSERIAL PRIMARY KEY,
    coach_id INTEGER NOT NULL,
    application_id INTEGER NOT NULL,
    role VARCHAR(10) NOT NULL CHECK (role IN ('coach','avery','system')),
    content TEXT NOT NULL,
    buttons JSONB,
    preview JSONB,
    progress_pct SMALLINT,
    function_calls JSONB,
    phase VARCHAR(30),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_avery_msg_coach ON avery_messages(coach_id, created_at DESC);

CREATE TABLE avery_coach_context (
    coach_id INTEGER PRIMARY KEY,
    application_id INTEGER NOT NULL,
    preferred_name VARCHAR(100),
    niche VARCHAR(50),
    specialty VARCHAR(200),
    tone_preference VARCHAR(20) DEFAULT 'casual',
    current_phase VARCHAR(30) DEFAULT 'discovery',
    phase_data JSONB DEFAULT '{}',
    onboarding_complete BOOLEAN DEFAULT FALSE,
    onboarding_completed_at TIMESTAMPTZ,
    total_messages INTEGER DEFAULT 0,
    last_interaction_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE avery_nudges (
    id BIGSERIAL PRIMARY KEY,
    coach_id INTEGER NOT NULL,
    nudge_type VARCHAR(50) NOT NULL,
    scheduled_for TIMESTAMPTZ NOT NULL,
    message_content TEXT NOT NULL,
    buttons JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    sent_at TIMESTAMPTZ,
    responded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_nudges_pending ON avery_nudges(status, scheduled_for) WHERE status = 'pending';

CREATE TABLE avery_events (
    id BIGSERIAL PRIMARY KEY,
    coach_id INTEGER NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_avery_events ON avery_events(event_name, created_at DESC);
```

---

## Ticket 1.5: Scripted Fallback (No AI)

**Type:** Backend | **Estimate:** 2 days | **Priority:** P1

Fully scripted version that works WITHOUT OpenAI. Serves as: (a) Sprint 1 MVP, (b) fallback if OpenAI is down, (c) A/B test baseline.

```typescript
const SCRIPTED_RESPONSES = {
  'discovery:no_name': { content: "Hey! 👋 I'm Avery. What should I call you?" },
  'discovery:has_name:no_niche': { content: "Great, {name}! What kind of coaching do you do?", buttons: [...] },
  'discovery:has_niche:no_specialty': { content: "Nice! What's your specialty within {niche}?" },
  // ... all phases scripted with template variables
};
```

---

## Sprint 1 Definition of Done
- [ ] Chat widget renders (bottom-right + full-screen)
- [ ] WebSocket messaging working
- [ ] Scripted onboarding conversation flows through all phases
- [ ] Buttons render and send events
- [ ] Progress bar updates
- [ ] Conversation persists across refreshes
- [ ] All DB tables created
- [ ] Basic analytics events tracked

---
---

# PHASE 2: OPENAI INTEGRATION & FUNCTION CALLING (Weeks 3-4)

## Ticket 2.1: OpenAI Service Layer

**Type:** Backend | **Estimate:** 3 days | **Priority:** P0

```typescript
export class OpenAIService {
  private readonly MODEL = 'gpt-4o';
  private readonly MAX_TOKENS = 500;
  
  async generateResponse(input: ConversationInput) {
    const messages = this.buildMessages(input);
    return openai.chat.completions.create({
      model: this.MODEL,
      messages,
      tools: AVERY_TOOLS,  // 12 function definitions
      tool_choice: 'auto',
      stream: true,
      max_tokens: this.MAX_TOKENS,
      temperature: 0.7,
    });
  }
  
  private buildMessages(input) {
    return [
      { role: 'system', content: this.buildSystemPrompt(input.context, input.storeState) },
      ...input.history.slice(-20).map(msg => ({
        role: msg.role === 'coach' ? 'user' : 'assistant',
        content: msg.content,
      })),
      { role: 'user', content: input.coachMessage },
    ];
  }
  
  private buildSystemPrompt(context, store) {
    return `${AVERY_SYSTEM_PROMPT}

CONTEXT: Coach: ${context.preferredName}, Niche: ${context.niche}, Phase: ${context.currentPhase}
STORE: URL: ${store.url}, Blogs: ${store.blogCount}, Price: ${store.price || 'Not set'}
SCORECARD: Photo: ${context.hasProfilePhoto?'✅':'⬜'}, Socials: ${context.socialConnections.length>0?'✅':'⬜'}, Blogs: ${store.blogCount>=3?'✅':'⬜'}, Shared: ${store.storeShared?'✅':'⬜'}, Live: ${store.liveScheduled?'✅':'⬜'}

PHASE INSTRUCTIONS: ${this.getPhaseInstructions(context.currentPhase)}`;
  }
}
```

---

## Ticket 2.2: Function Executor (12 Tools)

**Type:** Backend | **Estimate:** 4 days | **Priority:** P0

### All 12 Functions

| # | Function | KLIQ API Call | Scorecard Update |
|---|----------|--------------|-----------------|
| 1 | `update_coach_profile` | PUT /api/profile | ✅ profile_photo |
| 2 | `connect_social_account` | Triggers OAuth popup | ✅ socials_connected |
| 3 | `generate_blog_posts` | POST /api/blogs (×3) | ✅ blogs_published |
| 4 | `set_subscription_price` | PUT /api/pricing | — |
| 5 | `apply_store_template` | PUT /api/theme | — |
| 6 | `get_store_analytics` | GET /api/analytics | — |
| 7 | `get_niche_benchmarks` | BigQuery query | — |
| 8 | `schedule_live_session` | POST /api/live-sessions | ✅ live_scheduled |
| 9 | `generate_share_content` | AI generation | ✅ store_shared |
| 10 | `update_scorecard` | PUT /api/scorecard | — |
| 11 | `setup_stripe` | Stripe Connect redirect | — |
| 12 | `get_social_top_posts` | Platform API calls | — |

### Executor Pattern

```typescript
export class FunctionExecutor {
  async execute(coachId, applicationId, functionName, args) {
    const handler = FUNCTION_MAP[functionName];
    const result = await handler(coachId, applicationId, args);
    
    // Auto-update scorecard based on action
    await this.updateScorecardFromAction(coachId, applicationId, functionName);
    
    // Notify store preview via WebSocket
    if (STORE_MODIFYING_FUNCTIONS.includes(functionName)) {
      await this.notifyStorePreviewUpdate(coachId, applicationId);
    }
    
    return result;
  }
}
```

### Key Implementation: `get_niche_benchmarks`

```typescript
// Queries existing BigQuery table d1_coach_growth_stages
async function getNicheBenchmarks(niche, specialty) {
  const query = `
    SELECT
      ROUND(AVG(avg_sub_price), 2) as avg_price,
      ROUND(MIN(avg_sub_price), 2) as min_price,
      ROUND(MAX(avg_sub_price), 2) as max_price,
      ROUND(AVG(mrr), 2) as avg_mrr,
      ROUND(MAX(mrr), 2) as top_mrr,
      ROUND(AVG(total_subs), 0) as avg_subs,
      COUNT(*) as coach_count
    FROM \`rcwl-data.powerbi_dashboard.d1_coach_growth_stages\`
    WHERE total_subs > 0
  `;
  return await bigqueryClient.query(query);
}
```

---

## Ticket 2.3: Prompt Engineering & Testing

**Type:** Backend/AI | **Estimate:** 3 days | **Priority:** P0

### 20 Test Scenarios

| # | Scenario | Expected Behaviour |
|---|----------|-------------------|
| 1 | Happy path: fitness + Instagram | Full flow in 6 phases |
| 2 | Skip social, use niche templates | Blogs from templates |
| 3 | Free-text: "Can you make it more casual?" | Rewrites bio immediately |
| 4 | Free-text: "I was thinking £12.99" | Extracts price, calls set_price |
| 5 | Mid-flow question: "How do live sessions work?" | Answers, returns to flow |
| 6 | Resume after closing chat | "Welcome back, we were on..." |
| 7 | Coach says just "hi" | Avery responds contextually |
| 8 | Coach types niche as free text: "I teach yoga" | Classifies as wellness |
| 9 | Coach asks to regenerate blog | Calls generate_blog_posts again |
| 10 | Coach provides name with typo | Uses as-is (don't correct names) |
| 11 | Negative sentiment: "this is confusing" | Simplifies, offers to skip |
| 12 | Coach asks about pricing competitors | Redirects to KLIQ benchmarks |
| 13 | OAuth fails | Offers retry or skip |
| 14 | Coach wants custom template | Offers variants for their niche |
| 15 | Coach asks "how am I doing?" | Calls get_store_analytics |
| 16 | Coach asks Avery to write a specific blog | Calls generate_blog_posts(custom_topic) |
| 17 | Coach sends empty message | Avery prompts with current phase question |
| 18 | Coach sends very long message | Avery extracts intent, responds concisely |
| 19 | Coach asks to delete a blog | Avery confirms, then deletes |
| 20 | Coach completes all 5 scorecard items | Celebration + badge |

---

## Ticket 2.4: Error Handling & Fallbacks

**Type:** Backend | **Estimate:** 2 days | **Priority:** P0

| Error | Retry? | Fallback | User Message |
|-------|--------|----------|-------------|
| OpenAI rate limit | Yes (3×) | Scripted response | (silent retry) |
| OpenAI timeout | Yes (2×) | Scripted response | "Give me one sec... 🤔" |
| OpenAI API error | No | Scripted response | (silent fallback) |
| Function: profile update failed | Yes (1×) | — | "Couldn't update profile. Trying again..." |
| Function: blog gen failed | Yes (2×) | — | "Blog generation hit a snag. Trying different approach..." |
| Function: OAuth failed | No | — | "Connection didn't go through. Try again or skip?" |
| WebSocket disconnected | Yes (5×) | Reconnect | "Lost connection. Reconnecting..." |

---

## Sprint 2 Definition of Done
- [ ] GPT-4o integration with streaming
- [ ] All 12 functions defined and callable
- [ ] Function executor handles all 12 with KLIQ API calls
- [ ] Free-text understood (name, price, tone, niche)
- [ ] Error handling with fallback to scripted
- [ ] 20 test scenarios passing
- [ ] Response time < 2s (non-function), < 5s (with function)
- [ ] Token usage tracking

---
---

# PHASE 3: SOCIAL OAUTH & BLOG GENERATION (Weeks 5-6)

## Ticket 3.1: Instagram OAuth

**Type:** Full-Stack | **Estimate:** 4 days | **Priority:** P0

**PRE-REQUISITE:** Submit Meta app for review in Week 1 (takes 2-4 weeks). Request: `user_profile`, `user_media`.

### OAuth Flow
```
Coach clicks "Connect Instagram" → Popup opens → Coach authorises →
Redirect with auth code → Backend exchanges for long-lived token (60 days) →
Store encrypted → Fetch profile + media → WebSocket: oauth_complete →
Avery continues conversation
```

### Backend Service

```typescript
export class InstagramService {
  async exchangeCodeForToken(code: string) {
    // Short-lived token
    const short = await fetch('https://api.instagram.com/oauth/access_token', {
      method: 'POST',
      body: new URLSearchParams({ client_id, client_secret, grant_type: 'authorization_code', redirect_uri, code }),
    }).then(r => r.json());
    
    // Exchange for long-lived (60 days)
    const long = await fetch(
      `https://graph.instagram.com/access_token?grant_type=ig_exchange_token&client_secret=${secret}&access_token=${short.access_token}`
    ).then(r => r.json());
    
    return { accessToken: long.access_token, expiresAt: new Date(Date.now() + long.expires_in * 1000) };
  }
  
  async getTopPosts(accessToken: string, count = 5) {
    const media = await fetch(
      `https://graph.instagram.com/me/media?fields=id,caption,media_type,media_url,timestamp,permalink,like_count,comments_count&limit=50&access_token=${accessToken}`
    ).then(r => r.json());
    
    return media.data
      .filter(m => m.caption?.length > 20)
      .map(m => ({ ...m, score: (m.like_count||0) + (m.comments_count||0) * 3 }))
      .sort((a, b) => b.score - a.score)
      .slice(0, count);
  }
}
```

### Frontend: OAuth Popup

```typescript
export function useOAuth() {
  const openPopup = (platform: string) => {
    const popup = window.open(OAUTH_URLS[platform], `${platform}_oauth`, 'width=600,height=700');
    window.addEventListener('message', (event) => {
      if (event.data?.type === 'oauth_callback') {
        fetch(`/api/social/${platform}/callback`, {
          method: 'POST', body: JSON.stringify({ code: event.data.code }),
        }).then(r => r.json()).then(data => {
          averyWs.send(JSON.stringify({ type: 'oauth_complete', payload: { platform, ...data } }));
        });
        popup?.close();
      }
    }, { once: true });
  };
  return { openPopup };
}
```

---

## Ticket 3.2: TikTok OAuth

**Type:** Full-Stack | **Estimate:** 3 days | **Priority:** P1

```typescript
export class TikTokService {
  async exchangeCodeForToken(code: string) {
    return fetch('https://open.tiktokapis.com/v2/oauth/token/', {
      method: 'POST',
      body: new URLSearchParams({ client_key, client_secret, code, grant_type: 'authorization_code', redirect_uri }),
    }).then(r => r.json());
    // Returns: access_token, refresh_token (365 days), open_id
  }
  
  async getTopVideos(accessToken: string, count = 5) {
    const res = await fetch('https://open.tiktokapis.com/v2/video/list/', {
      method: 'POST',
      headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        max_count: 50,
        fields: ['id','title','video_description','cover_image_url','view_count','like_count','comment_count','share_count'],
      }),
    }).then(r => r.json());
    
    return res.data.videos
      .filter(v => (v.video_description||v.title||'').length > 20)
      .map(v => ({ ...v, score: (v.like_count||0) + (v.comment_count||0)*3 + (v.share_count||0)*5 }))
      .sort((a, b) => b.score - a.score)
      .slice(0, count);
  }
}
```

---

## Ticket 3.3: YouTube OAuth

**Type:** Full-Stack | **Estimate:** 2 days | **Priority:** P2

```typescript
export class YouTubeService {
  // Standard Google OAuth2 → youtube.readonly scope
  // GET /youtube/v3/search?channelId={id}&type=video&order=viewCount&maxResults=5
  // GET /youtube/v3/videos?id={ids}&part=snippet,statistics
  // Returns: title, description, thumbnailUrl, viewCount, likeCount
}
```

---

## Ticket 3.4: AI Blog Generation Pipeline

**Type:** Backend | **Estimate:** 4 days | **Priority:** P0

### From Social Content

```typescript
export class BlogGeneratorService {
  async generateFromSocial(applicationId, socialPosts, tone) {
    const context = await this.getAppContext(applicationId);
    const drafts = [];
    
    for (const post of socialPosts) {
      const response = await openai.chat.completions.create({
        model: 'gpt-4o',
        messages: [
          { role: 'system', content: BLOG_SYSTEM_PROMPT },
          { role: 'user', content: this.buildPrompt(post, context, tone) },
        ],
        response_format: { type: 'json_object' },
        max_tokens: 1500,
      });
      
      const blog = JSON.parse(response.choices[0].message.content);
      
      // Content moderation
      const mod = await openai.moderations.create({ input: blog.body });
      if (mod.results[0].flagged) continue;
      
      drafts.push(await this.saveDraft(applicationId, {
        title: blog.title, body: blog.body, category: blog.category,
        tags: blog.tags, coverImageUrl: post.mediaUrl,
        sourcePlatform: post.platform, sourcePostId: post.id,
      }));
    }
    return drafts;
  }
  
  async generateFromNiche(applicationId, niche, specialty, count, tone) {
    // Step 1: Generate topics
    // Step 2: Generate full blog for each topic
    // Same pattern, using niche-specific prompts instead of social captions
  }
}
```

### Blog Prompt Template

```
Transform this social media post into a blog article.
Coach: {name}, Niche: {niche}, Specialty: {specialty}, Tone: {tone}
Source: {platform}, Caption: {caption}, Engagement: {likes} likes

Return JSON: { title, body (300-500 words with H2 headings), category, tags }
Rules: First person, actionable advice, CTA at end, no invented facts.
```

---

## Ticket 3.5: Weekly Blog Cron Job

**Type:** Backend | **Estimate:** 1 day | **Priority:** P1

```
Schedule: Monday 6:00 AM UTC
For each coach with active social connections:
  1. Pull new posts since last_sync_at
  2. Select top 2 unused posts
  3. Generate 2 blog drafts
  4. Send push notification + queue Avery message
  5. Update last_sync_at
```

---

## Sprint 3 Definition of Done
- [ ] Instagram OAuth end-to-end
- [ ] TikTok OAuth end-to-end
- [ ] YouTube OAuth end-to-end
- [ ] Top posts retrieval for all platforms
- [ ] AI blog generation from social (3 blogs < 30 seconds)
- [ ] AI blog generation from niche templates
- [ ] Blog preview in Avery chat
- [ ] One-tap publish from chat
- [ ] Content moderation on all generated text
- [ ] Weekly cron job
- [ ] Tokens stored encrypted, refresh logic working
