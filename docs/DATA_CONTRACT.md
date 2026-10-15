# Participant contract 1.0.0

All record IDs are synthetic opaque strings. All day values are integers relative to episode start, not real dates. Each world is an independent population. `schema_version` must be `1.0.0`; `synthetic` must be true in dataset roots and member records. The supplied Python checks are executable reference semantics.

## Member record

| Field | Type / values | Meaning |
|---|---|---|
| member_id | string, `syn_` + 32 hexadecimal characters | Invented identifier, no link to a real user |
| pool_id | string | Independent allocation pool |
| age | integer 21–46 in generated data | Synthetic exact age for reciprocal age checks; no date of birth |
| gender | woman / man / non_binary | Explicit synthetic identity; never infer who they want to meet |
| zone | opaque zone label | Fictional geography, not a real city or distance |
| arrived_day | integer 0–20 | Day first observable |
| available | boolean | Current operational availability, including outstanding introduction and pause |
| fields | object | Observations listed below; null means unknown |
| field_status | same keys, observed / not_asked / declined | Distinguish missingness from refusal |
| field_observed_day | same keys, integer or null | When this field became visible or was reconfirmed |
| source | synthetic_questionnaire | Data provenance, not a confidence estimate |

All `fields` keys exist. Unknown numeric values are null, never zero. Known arrays are non-empty; null is unknown. `declined` must not be inferred or bypassed.

| Field inside fields | Non-null type / allowed values | Role |
|---|---|---|
| age_min, age_max | integer, 18–65, min ≤ max | Inclusive acceptable age bounds |
| who_to_meet | non-empty array of gender values | Explicit acceptable genders |
| relationship_structure | monogamous / non_monogamous | Both must agree in this simplified environment |
| smoking | no / occasionally / yes | Stated smoking behaviour |
| partner_smoking | no_smoking / any | Hard preference; occasional counts as smoking |
| has_children | boolean | Current circumstance |
| partner_children | no_children / any | Hard preference |
| wants_children | yes / no / unsure | Explicit yes/no conflict excludes; unsure alone does not |
| acceptable_zones | non-empty string array | Other member's zone must be acceptable in both directions |
| schedule | non-empty array of weekday_evening / weekend_day / weekend_evening | At least one overlap required |
| relationship_goal | long_term / exploring | Soft observation |
| relationship_pace | slow / steady / quick | Soft observation |
| lifestyle | quiet / mixed / social | Soft observation |
| conversations | ideas / stories / practical / playful | Soft observation |
| emotional_availability | ready / taking_time | Self-report, not a diagnosis |
| space_for_relationship | limited / moderate / ample | Self-report |
| relocate | yes / no / unsure | Soft observation; does not override current geography |

`eligibility(a,b)` returns `feasible`, `infeasible` or `needs_clarification`. A known hard failure takes priority over missing fields. Hard constraints are checked reciprocally. Missing hard data blocks an introduction pending clarification. No score overrides a hard failure. Availability, previous introductions, one use per person per batch and distinct identities are enforced separately by `advance`.

## Actions

`resolve_asks([{member_id, field}])` accepts `constraints` (all hard fields, cost 3) or a named soft field (cost 1). Budget is 12 units per day. This bundle is a development simplification, not twelve real questions priced as one. Results contain `member_id`, `field`, `observed_day`, `values`, and `statuses`. Answers are deterministic self-report truths when disclosed; declined answers remain unknown. There is no response delay for asks in v1.0. Unavailable members cannot be asked. Refresh the state after asks.

`advance([[id_a,id_b], ...])` validates the complete batch before applying it, creates introductions, then increments the day. Empty output is valid. Invalid actions raise `ValueError`; no partial match batch is committed. Each pair is new and belongs to one pool. Each person has at most one simultaneous introduction. Candidates remain occupied through the simulated response/date window and may pause after mutually positive feedback.

## Executable policy protocol

The authoritative JSON protocol and runnable examples are in [POLICY_INTERFACE.md](POLICY_INTERFACE.md). The engine calls the policy twice per day: first for asks, then for pairs after refreshing observations. Only observable state and policy-owned memory cross that boundary. Optional probability predictions are research-report diagnostics, not required executable output in release 1.0.

## Feedback and censoring

`introductions`: introduction_id, user_a, user_b, assigned_day, response_deadline_day, logging_policy, propensity. The `user_a` / `user_b` names mirror the live table, but values here are synthetic policy IDs, not database user IDs. Historical policy propensity is unknown (null). `logging_policy` identifies the generic harness, not a certified unbiased sampling policy.

`feedback`: introduction_id, member_id (null for pair-level events), event, value, occurred_day, observed_day, optional missing_reason.

- `introduction_response`: yes / no / null. Null at deadline means no response; before the event arrives, response is pending.
- `date_happened`: boolean, emitted only following two recorded Yes introduction responses.
- `second_meeting_intention`: yes / no / null, only after a date. Late answers are retained and do not meet the three-day outcome window.
- `pause_after_mutual_interest`: pair-level true, visible only once both positive second-meeting answers are observed.

No future event may appear in `receive_feedback()` or `observe()`. A date with no second-meeting response is not a negative preference label. A pair without a date has no second-meeting label. Right-censoring at a snapshot must remain explicit. Do not evaluate a late assignment as a failed outcome before its observation window has matured.
