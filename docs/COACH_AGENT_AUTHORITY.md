# Coach-agent authority

KhelSutra is an AI agent for the coach, including a person coaching themselves. It is never the AI coach.

```text
coach intent → inspectable plan → governed evidence + reversible output
             → coach interprets and decides → next instruction
```

The system may retrieve observations, filter and count them, assemble video, expose uncertainty, explain
omissions, and offer explicitly labelled hypotheses. It must not present model confidence as sporting
truth or autonomously prescribe training priorities, player selection, diagnosis, or technique changes.

Every semantic observation records one authority:

- `human_confirmed`
- `model_observation` with model identity and confidence
- `derived_calculation`
- `coach_assertion`
- `unknown`

An agent receipt records whether prescriptive advice was emitted and whether a human decision remains
required. Official KhelSutra receipts must set those values to `false` and `true`, respectively.
