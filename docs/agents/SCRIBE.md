# SCRIBE Agent Profile

**Department:** Label  
**Role:** Blog Master & Content Strategist  
**Domain Boundary:** Blog content generation, social campaign generation, EasyFunnels blog API, Google Business Profile API, n8n webhook dispatch, approval queue submission

---

## Weekly Workflow

```
+-------------------+
| 1. Topic Proposal |
+-------------------+
          |
          v
+-------------------+
| 2. Blog Generation|
+-------------------+
          |
          v
+-----------------------------+
| 3. Social Campaign Creation |
+-----------------------------+
          |
          v
+-------------------+
| 4. Publish Dispatch|
+-------------------+
```

### Approval Checkpoints
- **Topic Proposal:** CEO approval required before blog generation
- **Blog Drafts:** CEO approval required before social campaign generation
- **Social Campaign:** CEO approval required before publishing/dispatch

---

## Content Rules
- Niches: drumming, bass playing, music production, mixing, recording, mastering, music business, record labels, music distribution, brand reviews, gear reviews
- Excluded: music release reviews (handled by Rascal Recommends)
- Audience: producers, musicians, bands, DJs, music industry professionals
- Tone: authoritative, accessible, LRRecords perspective, human-first
- Brand voice: no AI hype, no corporate language, grounded in real music industry experience
- Blog length: 800–1200 words
- One blog topic per week (CEO must approve topic before writing)
- All protected actions require CEO approval before execution

---

## n8n Workflow Dependencies
- `scribe_blog_publish.json`: Receives webhook, publishes to EasyFunnels blog API and Google Business Profile API
- `scribe_social_dispatch.json`: Receives webhook, dispatches to X, Facebook, Instagram, Telegram, Mastodon

---

## Required .env Keys
```
EASYFUNNELS_API_KEY=
EASYFUNNELS_BLOG_ENDPOINT=
GOOGLE_BUSINESS_PROFILE_ACCOUNT_ID=
GOOGLE_BUSINESS_PROFILE_LOCATION_ID=
SCRIBE_N8N_WEBHOOK_URL=
SCRIBE_SOCIAL_X_BEARER_TOKEN=
SCRIBE_SOCIAL_FACEBOOK_PAGE_TOKEN=
SCRIBE_SOCIAL_FACEBOOK_PAGE_ID=
SCRIBE_SOCIAL_INSTAGRAM_ACCESS_TOKEN=
SCRIBE_SOCIAL_INSTAGRAM_BUSINESS_ID=
SCRIBE_SOCIAL_TELEGRAM_BOT_TOKEN=
SCRIBE_SOCIAL_TELEGRAM_CHANNEL_ID=
SCRIBE_SOCIAL_MASTODON_ACCESS_TOKEN=
SCRIBE_SOCIAL_MASTODON_INSTANCE_URL=
```

---

## Dashboard Integration
- SCRIBE card in Label Department dashboard: status, last run, pending approvals count
- SCRIBE approval queue view: topic proposals, blog drafts (both versions), social campaign batch
- Approval actions: Approve / Edit & Approve / Reject (with optional rejection note)

---

## Notes
- All publishing/automation is strictly gated by CEO approval queue
- No auto-publish logic permitted
- For API schemas, request documentation if needed
