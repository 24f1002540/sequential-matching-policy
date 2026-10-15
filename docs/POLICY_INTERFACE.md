# Policy interface 1.0.0

The engine owns simulator state. The policy is a separate process that reads one UTF-8 JSON request from stdin, returns exactly one JSON object on stdout, and exits with code zero. Diagnostics go to stderr. The reference runner passes `--baseline greedy` (or another baseline name) in local mode; retain the starter argument parser or accept that option in a replacement policy. Container entrypoints need no command-line arguments.

Each request contains exactly these public inputs:

```json
{"schema_version":"1.0.0","phase":"ask","state":{"schema_version":"1.0.0","synthetic":true,"day":0,"ask_budget_remaining":12,"members":[],"introductions":[],"feedback":[],"ask_log":[]},"memory":null}
```

This empty-state request is valid and executable. For a real request, `state.members` contains only arrived people; records and feedback follow DATA_CONTRACT.md. There is no world seed, future-arrival list, latent preference, response propensity, private coefficient or simulator object in the request.

## Ask phase

Return exactly `asks` and `memory`. Each ask contains exactly `member_id` and `field`:

```json
{"asks":[],"memory":{}}
```

`field` is `constraints` (3 budget units) or one named soft field (1 unit). The total daily budget is 12. Request only available observed members. Declined answers stay unknown. Use IDs copied from the input; do not generate IDs. All asks are validated before any are applied. Ask results are included in the refreshed state's cumulative `ask_log`.

## Match phase

The next request has `phase: "match"`, the same day and refreshed observations. Return exactly `pairs` and `memory`:

```json
{"pairs":[],"memory":{}}
```

Each pair is an array of two member-ID strings. It must satisfy every reciprocal hard constraint, availability, no repeated pair and no reused person in a batch. Only introductions are actions; probability estimates belong in your experiment reports. Returning an empty list waits one day. The complete batch is validated atomically.

## Memory and limits

`memory` may be any finite JSON value. The next request carries it unchanged. The policy process itself is restarted for every phase. There is no persistent filesystem between calls. Memory begins as null for each independent episode. Requests, responses, memory and diagnostic output each have a 1 MiB limit. JSON NaN and Infinity are invalid.

Each call has a 10-second limit including startup. Assessed containers have 2 CPU cores, 1 GiB RAM, 64 processes, no network, read-only image files and a fresh 64 MiB temporary directory. Inference assets must fit within a 2 GiB image. Keep input handling separate from modelling and allocation. Do not bundle organiser worlds into a policy image.

The public harness provides `episode(world, command, simulator_class=...)` so authorised organisers can supply held-back worlds or a compatible engine without exposing them to the policy. Only the JSON observations cross the process boundary. The local runner is not a sandbox; Docker mode is required for assessed submissions.
