# Plan Brief — User Interrogation

I'll set up your Google Search Ads campaign. I need 11 quick answers. Tell me your business and I'll ask each question; you can answer them all in one message if you prefer.

**Required:**

1. **What does your business do, in one sentence?**
2. **Who is your ideal customer?** (demographics, situation, the problem they have)
3. **What's your USP — your unique selling proposition?** Pick whichever of these is true for you (1+ is fine):
   - Unique because of the **buyer** you serve (specific niche, demographic, vertical)
   - Unique because of **what** you sell (specific product, service, your personal story)
   - Unique because of an **unusual angle** (specific outcome, track record, quality, payment plan)
   - Unique because of **what you don't do** (avoid certain types of work, missing problematic ingredients)
   - Unique because of **time promises** (response time, deadline, duration)
   - Unique because of **guarantee** (refund, replacement, "X or it's free")
4. **What's the single action you want a visitor to take?** (call, fill out form, buy online, book appointment)
5. **What is one converted customer worth to you?** (per-sale or lifetime — give a number)
6. **What geographic area do you serve?** (city, state, country, or all)
7. **What's your monthly ad budget?** (per-month dollar amount)
8. **Are you running on Google Ads now?** If yes, what's working and what isn't?
9. **Do your competitors bid on your business name?** (run a quick search of your name to check)
10. **Top 5 competitor names + websites** (so I can mine their ads for ideas + treat them as negatives where appropriate)
11. **Are most of your customers on desktop or mobile?** (gut answer is fine)

Optional but useful:
- **What vertical/industry?** (legal, home_services, health, real_estate, ecommerce, b2b, education, travel, finance, default)
- **Landing page base URL?** (default `https://example.com`; we use this as a placeholder if you don't have dedicated landing pages yet)

Once you answer, I'll fill in `brief.json`, run `plan.py`, emit the CSVs, validate them, and walk you through importing into Google Ads Editor.

**Before we start, six prerequisites** — confirm each (or fix it first):

- [ ] Conversion tracking is installed and matches your real conversions (CRM/Stripe count)
- [ ] You have a coherent landing page (not just a homepage) for each main product/service
- [ ] Your Google Ads account is in **Expert Mode** (not Smart Mode)
- [ ] `Ad Suggestions` is OFF (Settings → Account Settings)
- [ ] `Automated Assets` is OFF (Ads & Assets → Assets → Account-level automated assets → Advanced Settings)
- [ ] 2-step verification is on your Google Ads account (security)

If any of these is missing, fix it before we run the plan — wasted ad spend compounds from any of these holes.
