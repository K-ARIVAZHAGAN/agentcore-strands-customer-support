# Reflection

One design decision was to separate cloud runtime dependencies from the local
Bedrock AgentCore Starter Toolkit. The toolkit is needed to configure, deploy,
and invoke the agent, but the running agent only needs Strands, the AgentCore
SDK, browser support, and their dependencies. Keeping these separate reduced
the deployment package and avoided shipping development-only packages. I also
used Decimal arithmetic inside AgentCore Code Interpreter so monetary rounding
and the order of points redemption and tier discounts remain explicit.

A concrete challenge was deploying from Windows to the Linux ARM64 runtime.
The first deployment attempted to package a toolkit dependency that had no
compatible ARM64 wheel. I traced the dependency to the deployment CLI and added
a runtime-only requirements file while retaining the required Python toolkit
locally. The toolkit also checked for an external zip executable even though
its packager used Python's zipfile module. I applied a Windows-only compatibility
change in the isolated environment. A live browser test also exposed lost executable permissions in the Windows-built
ZIP. I copied the bundled Playwright driver to writable temporary storage and
restored its executable bit. Offline tests then checked redemption limits,
rounding, fallback disclosure, namespace compatibility, and memory persistence
without making model calls. A real Code Interpreter invocation independently
returned the expected $99 final total for the Gold example.

For production, I would replace the educational Gateway's NONE authorizer with
authenticated access and enforce order ownership in the backend. A customer ID
in a request is not proof of identity. Refunds would need persistent storage,
audit records, and idempotency keys to prevent duplicate payments after retries.
Memory retention would require consent and deletion controls, while tool-result
traces should be redacted or disabled for real customer data. I would monitor
model latency, tool errors, memory extraction delays, and usage costs separately
so that graceful fallback does not conceal a failing integration.
