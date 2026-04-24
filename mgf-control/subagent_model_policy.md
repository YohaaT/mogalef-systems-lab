# Subagent model policy for mogalef-systems-lab

Updated: 2026-04-14 13:45 UTC

## Mandatory model mapping
- `BO` -> `openai/gpt-5-mini`
- `SA-BUILD` -> `openai/gpt-5.4-mini`
- `SA-QA` -> `openai/gpt-5.4-mini`
- `SA-REVIEW` -> `openai/gpt-5.4-mini`
- `SA-RESEARCH` -> `openai/gpt-5-mini`

## Escalation rule
- Only `SA-REVIEW` may escalate to `openai/gpt-5.4`.
- That escalation is allowed only when a real discrepancy remains unresolved after a first pass.
- `BO` must not use `openai/gpt-5.4`.
- `SA-RESEARCH` must not use `openai/gpt-5.4` by default.

## Fallbacks applied
- Requested `BO -> openai/gpt-5.4-nano` was not present in the locally resolved model snapshot for this node, so the applied fallback is `openai/gpt-5-mini` as the closest lower-cost OpenAI tier that still respects the rule that `BO` must not use `openai/gpt-5.4`.
- `SA-REVIEW` did not exist in the real `openclaw.json` agent list. A new `SA-REVIEW` agent entry was added using the same restrictive tool profile shape as the prior review-like guard profile.

## Enforcement choices applied in config
- `BO` now requires explicit `agentId` when spawning subagents.
- Global subagent spawning also requires explicit `agentId`.
- `BO` allowlist now includes `SA-REVIEW`.
- Default subagent model for unspecified spawns is `openai/gpt-5.4-mini`, but project policy expects named specialist agents to be targeted explicitly.
