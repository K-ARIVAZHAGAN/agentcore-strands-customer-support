# Results and rubric evidence

Verified in the Udacity lab on 18 October 2026 in us-east-1. Runtime
`csai_support_agent-d32rOzHB4e` is READY. The required Python Starter Toolkit
configured, deployed, and invoked the agent; the npm CLI was not installed.

| Criterion / scenario | Observed evidence |
|---|---|
| Module-level app, async entrypoint, app.run | starter/main.py |
| Cloud runtime responds to agentcore invoke | starter/evidence/01-order.txt and deployment.json |
| API-backed Gateway tool | gateway-order-final.json: order-tracker___get_order, success |
| Lambda-backed Gateway tool | gateway-refund-final.json: refund-processor___initiate_refund, success |
| Order tracking | 01-order.txt: SHIPPED, UPS, TRK987654321, estimated delivery |
| Refund | 02-refund.txt: approved $139.99 refund, actual REF ID, 3-5 business days |
| RAG / Retrieve tool | 03-rag.txt: Platinum same-day shipping, 15% discount, priority support |
| Cross-session memory | 04-memory-a.txt and 04-memory-b.txt: Jane and concise responses, same customer ID, different runtime and payload sessions |
| Code Interpreter | 05-discount.txt: real sandbox result, 4000 points redeemed, tier_discount_pct=10, tier discount $11, final_total=$99, remaining_points=349 |
| Live browser | 06-browser.txt: Learn the Latest Tech Skills; Advance Your Career | Udacity, https://www.udacity.com/ |
| Reflection | REFLECTION.md: 307 words, decision, concrete challenge, production considerations |

Evidence filenames above are relative to starter/evidence unless otherwise stated.
The raw final Gateway records contain tool names, success statuses, and nonempty
structured responses. `gateway-backend-results.json` also records independent MCP
checks; `runtime-tool-calls.json` contains real CloudWatch tool-call messages.

## Verification

Eight offline tests passed, covering money rounding and redemption caps, namespace
compatibility, actor-scoped memory retrieval, original-query persistence, exclusion
of tool-result messages from memory queries, standalone sandbox code, disclosed
fallback, Knowledge Base guard/join behavior, and the browser driver compatibility
fix. `starter/validate_evidence.py` passed all seven captured invocations across the
six scenarios. No passing test output was generated from a mock cloud response.
Offline mocks are confined to `test_main.py` and are not submitted as cloud proof.

## Iteration details and limits

- The first memory recall attempt ran before extraction completed. Actual extraction
  took about a minute; the captured successful recall uses a separate session after
  extraction. The runner now checks readiness rather than assuming 45 seconds.
- The model initially restated a correct sandbox amount incorrectly. Final discount
  replies now display the calculator's structured values directly. `remaining_points`
  includes new earned points; `points_after_redemption` is separately 250.
- Windows ZIP packaging lost the Playwright Node executable permission. The agent
  copies that bundled binary to temporary storage and restores its executable bit.
  Browser initialization then succeeded. The site's network-idle wait timed out,
  so the successful browser request explicitly read document.title and location.href
  from the loaded page despite that timeout.
- The browser capability test uses the other supplied fictional customer, CUST-456,
  to isolate it from earlier failed-browser interactions saved for CUST-123. The
  memory test still uses CUST-123 in both sessions. Historical tool failures can
  influence subsequent responses; production memory filtering needs improvement.
- Prior failed browser and calculation logs are labeled initial/before-driver-fix
  or diagnostic. They are retained for transparency; the numbered current scenario
  logs are the successful evidence.
- The Gateway is unauthenticated only as required by this educational project.
  The supplied Lambda backends are mock fixtures and remain unchanged; they are
  not a production payment or order system. Runtime tool-result traces contain
  synthetic data and should be redacted/disabled for real customers.
- Completed browser test sessions were explicitly stopped. The runtime, Gateway,
  memory, Knowledge Base, API, and Lambdas remain for review; follow cleanup steps
  after preserving evidence. Credentials are not included in the submission.
