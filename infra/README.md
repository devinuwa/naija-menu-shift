# Bedrock sandbox IAM policy — how to use

`bedrock-sandbox-iam-policy.json` is a least-privilege policy for the event
sandbox. It allows invoking **one** Bedrock model and nothing else: no other
AWS services, no other models, no data access.

## Before pasting it into IAM

1. In the Bedrock console (region **us-east-1** → Model access), confirm the
   exact model ID or inference profile ID the organisers enabled.
2. In the JSON, replace `REPLACE_WITH_ENABLED_MODEL_ID` with that ID:
   - Foundation model ID (e.g. `amazon.nova-micro-v1:0`): keep the
     `foundation-model/...` line and **delete** the `inference-profile/...` line.
   - Inference profile ID (e.g. `us.amazon.nova-micro-v1:0`): keep the
     `inference-profile/...` line and **delete** the `foundation-model/...` line.
     The `*` in that ARN is the account segment; you may replace it with the
     sandbox account ID if you know it.
3. Paste the edited JSON as an inline policy on the workshop role/user. This
   file intentionally contains **no JSON comments** (IAM rejects them), which
   is why the instructions live here instead.

## Why both actions

- `bedrock:InvokeModel` — required by the Converse call the adapter makes.
- `bedrock:InvokeModelWithResponseStream` — the streaming variant of the same
  call (ConverseStream). Included, scoped to the same single model, so that
  enabling streamed responses at the event is also a config-only change. If
  your team prefers the absolute minimum, delete this line; the current
  adapter does not stream.

## Notes

- The workshop sandbox is temporary and usually pre-configured by the
  organisers; you may not need to attach this policy at all. It exists so the
  team's permission footprint is explicit and reviewable, and so a judge can
  see the model can do nothing beyond proposing formulations.
- Never widen the Resource to `*` "to make it work". If invocation is denied,
  the model ID is wrong or not enabled — fix the ID (config), not the policy.
