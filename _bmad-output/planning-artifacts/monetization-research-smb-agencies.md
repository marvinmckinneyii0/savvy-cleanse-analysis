# SAINT Pricing Research — Small and Mid-Size Marketing Agencies

**Written:** 2026-11-11 · **Status:** research and a recommendation for the owner. It does not change the site, the PRD tier table or `sprint-status.yaml`. Agents do not edit price pages or price copy; Marvin decides.

**Ideal customer profile:** small to mid-size marketing agencies (roughly 2–50 people).
**People in the deal:** the agency owner, the decision maker who approves tools (often an ops or account director), and the data analyst who would use SAINT day to day.

## 1. What the market charges

All figures are list prices found on 2026-11-11. Sources disagree, and many are written by competitors, so treat every number as approximate and check the vendor's own page before quoting it.

### Agency reporting tools (closest substitutes for the eventual SaaS)

| Tool | How it charges | Reported 2026 price |
|---|---|---|
| AgencyAnalytics | Per client | About $20–$25 per client per month (Core). Older tiered plans were $59–$349/month. Mid-size agencies report bills of $400–$548/month. |
| Swydo | Per data source | €69/month base with 10 sources, then $4.50 per source (11–100), falling with volume. |
| DashThis | Per dashboard and source | Individual about $44/month for 3 dashboards (after the March 2026 change). Pre-change: $49 / $159 / $309. |
| Supermetrics | Per destination | About $39–$299/month per destination; each destination (Sheets, Looker Studio) is billed separately. |
| Whatagraph | Per data source, annual only | Max from about $812/month (other sources: €699 or $1,118). Prime is quoted. |

### AI data-analysis tools (what an analyst might buy for themselves)

| Tool | Reported 2026 price |
|---|---|
| Julius AI | Free tier with about 15 messages. Paid plans reported at $20–$45/month for individuals and about $450/month for business. |

### Doing it by hand (what a done-for-you report replaces)

| Option | Reported cost |
|---|---|
| Freelance data analyst | About $40–$90/hour on Upwork for general analysis; $65–$115/hour with SQL or BI skills; basic cleaning can be lower. |
| Data-cleansing consultant | $90–$150/hour, or $300 to $2,000+ per project. |
| Solo-consultant marketing audit | About $1,000–$5,000 for a small business (UK guide, converted). |
| Single-channel marketing audit (US) | About $2,500–$7,500. |

### How much agencies spend on software

No independent survey breaks this down by agency size. One modeled index puts a 3-person agency at about $1,060/month across 15 tools and an 8-person agency at about $2,408/month. Use these only as a rough sense of scale.

## 2. What each person cares about

| Person | What makes them buy | What makes them hesitate | How to frame the offer |
|---|---|---|---|
| **Agency owner** | Hours saved, fewer client-facing data mistakes, something to resell | Another monthly tool on top of ~$1,000–$2,400 of stack | Price per client report; show the hours a report replaces (4–8 analyst hours ≈ $160–$900) |
| **Decision maker** (ops / account director) | Predictable cost, easy approval, low risk | Unknown vendor, long commitments | Fixed price per report now; monthly plan with annual discount later; refundable deposit to reserve |
| **Data analyst** | Trustworthy cleaning, a record of every change, clean exports | Black-box cleaning, being replaced | Lead with the change record and "nothing changed silently"; compare with Julius at $20–$45/month |

## 3. Recommendation

### Now: concierge beta, priced per report

The beta is a person running SAINT on a CSV, so price the output, not software.

| Offer | Suggested price | Reasoning |
|---|---|---|
| First report (beta) | Free, or $99 | Removes the risk for a first agency; collects feedback and a testimonial. |
| Single report | $249–$299 | Below a freelancer's 4–8 hours ($160–$900 at the rates above) and far below a consultant audit ($1,000+), with a faster turnaround. |
| Agency bundle (5 reports) | $999 ($200 each) | Fits an agency running reports for several clients; one approval instead of five. |

### Later: self-serve SaaS, check against the PRD table

The PRD already sets Free / Starter $49 / Professional $149 / Enterprise (Amendment 7). Against this research:

- **Starter at $49** sits next to DashThis ($44) and a little above Julius for individuals ($20–$45). It reads as reasonable for a small agency.
- **Professional at $149** is within the range agencies pay AgencyAnalytics for 6–7 clients ($20–$25 each), and well below Whatagraph.
- **The gap:** every agency reporting tool above scales with clients, sources or destinations. A flat tier does not grow with an agency's book. Consider adding a per-client or per-project add-on above the included project count (the PRD already counts projects: 5 / 15 / 50). That matches how agency buyers already budget.
- **White-label reports** are a common reason agencies pay more. Consider it for Professional or as an add-on.

### Reservation deposit

The owner chose a refundable deposit (2026-11-11). Suggested amount: **$49**, one month of Starter. That is low enough to commit without approval, and high enough to signal real interest. Decide separately whether it later becomes a credit on the first bill.

## 4. What this research does not cover

- No customer interviews. Willingness to pay for this ICP is inferred from competitor prices and freelance rates.
- Prices for agencies outside the US and UK.
- Whether agencies would buy SAINT for themselves or resell it to clients. The interest list on the home page can start answering this.

**Next step:** ask the first 5–10 agencies on the interest list what they pay today for reporting and for analyst time, and what they would pay per report.

## Sources

- AgencyAnalytics: [DashThis review](https://dashthis.com/alternatives/agency-analytics/), [Databox](https://databox.com/?p=191846), [Lilach Bullock](https://www.lilachbullock.com/?p=210286), [CostBench](https://costbench.com/software/seo-tools/agencyanalytics/), [1ClickReport](https://www.1clickreport.com/blog/agencyanalytics-pricing-2026), [SocialRails](https://socialrails.com/blog/agencyanalytics-pricing)
- Swydo: [Swydo](https://www.swydo.com/pricing), [Swydo vs Databox](https://swydo.com/compare/swydo-vs-databox/), [MetricsWatch vs Swydo](https://www.metricswatch.com/blog/metricswatch-vs-swydo)
- DashThis: [DashThis 2026 change](https://dashthis.com/blog/new-pricing-2026/), [Two Minute Reports](https://twominutereports.com/blog/dashthis-pricing), [Capterra](https://www.capterra.com/p/163170/DashThis/pricing/)
- Supermetrics: [Coupler](https://blog.coupler.io/supermetrics-pricing/), [Windsor.ai](https://windsor.ai/supermetrics-pricing-overview/), [1ClickReport](https://www.1clickreport.com/blog/supermetrics-pricing-2026-real-cost), [Reporting Ninja](https://www.reportingninja.com/blog/supermetrics-pricing)
- Whatagraph: [Whatagraph](https://whatagraph.com/reviews/whatagraph), [MetricsWatch](https://www.metricswatch.com/blog/metricswatch-vs-whatagraph), [Coupler](https://blog.coupler.io/?p=86143), [Databox](https://databox.com/?p=194113)
- Julius AI: [Coefficient](https://coefficient.io/julius-ai-pricing), [eesel](https://www.eesel.ai/blog/julius-ai-pricing), [Querio](https://querio.ai/articles/julius-ai-pricing-and-limits-is-it-worth-it)
- Manual work: [Prospeo data-cleansing guide](https://prospeo.io/s/data-cleansing-service), [Webtonic audit costs](https://www.webtonic.io/blog/marketing-audit-what-it-costs-in-2026), [Lilach Bullock audit cost](https://www.lilachbullock.com/ai-marketing-audit-cost-what-it-includes/), [Tracking audit packages](https://site-freelance-3ls.pages.dev/en/consultant-analytics/audit/pricing/), [aiproposer Upwork rates](https://aiproposer.com/comparisons/fiverr-vs-upwork-data-analysts), [Fiverr data analyst costs](https://fiverr.com/resources/guides/costs/business-data-analyst), [goLance](https://golance.com/hiring/best-freelance-data-analysts-hourly-rate), [Secondtalent](https://www.secondtalent.com/cost-to-hire/data-analyst/)
- Agency software spend: [Agency software cost index](https://www.thestackinsiders.com/tools/agency-software-cost-index), [Mewayz SMB report](https://mewayz.com/en/blog/smb-software-spend-report-2026-how-much-small-businesses-actually-pay)
