# Customer Support Agent with Strands and AgentCore

Implementation for the Udacity AgentCore project. The supplied Lambda functions
remain unchanged. All resources are educational mock services in us-east-1.

## Implementation

- `starter/main.py`: module-level app, async runtime entrypoint, MCP gateway,
  managed Knowledge Base retrieval, memory hooks, browser, and sandbox calculator.
- `starter/setup_infrastructure.py`: checkpointed setup with resource IDs saved
  to `project_resources.json` (resource identifiers only, no credentials).
- `starter/setup_permissions.py`: validates the runtime and adds scoped KB,
  memory, session-history, and browser permissions.
- `starter/test_main.py`: eight offline business-rule and memory checks.
- `starter/run_acceptance.py`: real `agentcore invoke` commands for six required
  scenarios, including separate sessions for memory; saves raw output under evidence.
- `REFLECTION.md`: 200-400 word reflection.

## Environment and deployment

Use the Python-based Starter Toolkit required by this course. Do not install the
npm AgentCore CLI in the same environment. Dependencies for local tools are in
`pyproject.toml`; cloud runtime-only dependencies are in `requirements.txt`.

```powershell
cd starter
$env:AWS_PROFILE = "udacity"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:AGENTCORE_SUPPRESS_RECOMMENDATION = "1"
uv sync --python 3.13
uv run python setup_infrastructure.py
uv run agentcore configure --entrypoint main.py --name csai_support_agent --deployment-type direct_code_deploy --runtime PYTHON_3_13 --disable-memory --region us-east-1 --non-interactive
uv run agentcore deploy
uv run python setup_permissions.py --profile udacity
uv run python run_acceptance.py
```

The toolkit's automatic memory is disabled because the implementation uses its
own semantic and user-preference memory resource. The Gateway uses NONE auth
only for this synthetic-data lab; runtime invocation uses IAM authorization.

## Windows compatibility

Toolkit 0.3.14 checked for an external zip executable even though the packaging
implementation used Python zipfile. In this workspace, only that prerequisite
check was adjusted in the isolated environment to permit Windows. A Linux course
workspace with zip installed needs no adjustment. UTF-8 output is enabled because
the toolkit prints Unicode characters unsupported by Windows' default cp1252.

An initial ARM64 dependency build failed because the local deployment toolkit
pulled in lazy-object-proxy without an appropriate wheel. Runtime requirements
exclude the local deployment CLI and its OpenAPI validation dependencies.

The runtime also restores executable permissions for Playwright's trusted Node
binary when a Windows-built ZIP loses POSIX file modes. It copies the packaged
binary to the runtime's temporary directory, marks only that copy executable,
and selects it through PLAYWRIGHT_NODEJS_PATH. It does not download a binary or
change the installed dependency. The browser session name uses valid hyphens.

## Calculation semantics

100 points = $1; redeem complete 500-point blocks up to 50% of the order.
Apply tier discount to the remaining subtotal, then earn points on the final
amount, rounding earned points down. `remaining_points` includes newly earned
points; `points_after_redemption` separately reports the pre-earn balance.
The Gold example returns $99.00, with 4,000 points redeemed, a 10% tier discount,
and 349 remaining points including 99 newly earned points. Monetary values are
Decimal-based strings. A disclosed tier-only fallback never claims sandbox use.

## Cleanup

After saving evidence and completing review, use `agentcore destroy` for this
runtime. Delete this project's Gateway targets and Gateway, memory, data source
and Knowledge Base, REST API, and two Lambda functions. Empty and remove only
this project's catalog bucket and deployment prefix. `project_resources.json`
lists their IDs. Avoid deleting resources from the first project or unrelated
lab work. Code Interpreter uses a context manager for cleanup. After browser tests, verify
and explicitly stop this project's remaining browser sessions; do not rely only
on SDK destructor cleanup.

## Attribution

Starter: https://github.com/udacity/cd14763-project-starter
Original license and starter instructions are retained. AI assistance was used
for implementation and debugging; review the code and course disclosure rules.
