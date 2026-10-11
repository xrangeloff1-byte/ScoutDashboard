# Scout — Running Development Outline (V4+)

**Permanent constraints:** Scout remains on free infrastructure without paid APIs, subscriptions, trials, or credit-card dependencies. GitHub Actions free-tier eligibility and usage limits must be monitored; zero cost cannot be guaranteed for arbitrary usage. Scout is separate from Beatrice: do not edit or re-enable Beatrice. Never send client outreach without separate user approval. John Laering is the **Virtual Client Relations Agent**, Cairnflow Private.

## Goal
Transform Scout from basic homepage checks into a useful **website diagnostics and sales-intelligence engine**. Find high-confidence, customer-relevant improvement opportunities, including complete website makeovers for content-poor sites. Generate review-only outreach with verifiable evidence and appropriate caveats.

## Modes
1. **Prospect Research:** bounded, respectful inspection of publicly available pages; obey site restrictions, no authentication, form submissions, fuzzing, exploit attempts, intrusive scans or vulnerability claims.
2. **Authorized Client Audit:** deeper crawling and security checks only after explicit documented scope and permission from the site owner.

## Tool integration roadmap
- **Playwright** (https://github.com/microsoft/playwright): rendered desktop/mobile view, screenshots, visible navigation and content; cap pages, time, bandwidth.
- **Lighthouse CI** (https://github.com/GoogleChrome/lighthouse-ci): performance, mobile, accessibility, SEO indicators. Avoid overclaiming from a single run.
- **axe-core** (https://github.com/dequelabs/axe-core): automated accessibility checks with manual confirmation.
- **MDN HTTP Observatory** (https://github.com/mdn/mdn-http-observatory): optional passive HTTP configuration assessment; not proof of security vulnerabilities.
- **lychee** (https://github.com/lycheeverse/lychee): bounded, non-intrusive public link checks.
- **OWASP ZAP** (https://github.com/zaproxy/zaproxy): *authorized client mode only*, including its baseline crawler; not part of unsolicited prospect scanning.

## Execution phases
1. Persist this outline, set clear cost/scope boundaries, and build deterministic diagnostics schema.
2. Add bounded public-page checks with evidence, confidence, and recommended fix; avoid costly browser dependencies until resource/cost limits are tested.
3. Pilot Playwright mobile rendering + screenshots with strict run limits and robots considerations.
4. Pilot Lighthouse + axe-core, evaluate GitHub Actions runtime and free-tier consumption.
5. Integrate ranked findings into Cairnflow Command Center and John Laering's review-only drafts. Keep replies/clients/tasks honest: no Gmail sync unless actually implemented.
6. Offer owner-authorized deeper audit separately.

## Acceptance checks
Syntax/tests green, workflow artifact contains updated offline dashboard, observed evidence is reproducible, no fabricated vulnerabilities, no emails sent, no paid services enabled, no Beatrice changes. Manual merge and workflow test before calling each phase deployed.
