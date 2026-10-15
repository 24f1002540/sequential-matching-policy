# Run the assessed evaluation

The public repository contains the complete participant kit and a private-evaluation tool. It does not contain private worlds or real-member records. The private workspace is created outside this repository and must never be shared with submissions or committed.

## Prepare once, before assessed submissions

From this repository root:

```bash
python organise.py prepare --workspace ../sequential-private-evaluation
```

This creates 120 cryptographically seeded worlds: 20 per scenario family, each with 200 synthetic adults. The script refuses a workspace inside the repository and refuses to overwrite an existing workspace. Retain the generated manifest and world checksums unchanged so every team sees identical worlds. Back up the private workspace in organiser-controlled storage. No production data or credentials are needed.

## Build and grade a submitted version

Check out the exact submitted commit in a separate project folder. Build that project's Dockerfile into a uniquely named local image. In the public kit folder, run:

```bash
python organise.py grade --workspace ../sequential-private-evaluation --image team-policy:submission --output ../sequential-private-evaluation/team_results.json
```

`team-policy:submission` is the local image name chosen when building that submission. The grader pins its image ID, checks the 2 GiB image limit, verifies every private-world checksum and uses offline container execution with no host directories mounted. Container limits are 2 CPU cores, 1 GiB RAM and 64 processes; every invocation is limited to 10 seconds. The private engine and worlds remain in the host process. Policies receive only observable JSON and their own carried memory.

A full run has 14,400 short policy invocations and can take substantial time because each invocation starts a fresh container. Run teams on the same host configuration without competing grading jobs so the final runtime tie-break is comparable. The grader prints progress and saves every episode metric. An invalid episode makes the technical submission ineligible.

## Rank and publish

Use each result's `summary.ranking_key_descending`, sorted descending. This implements primary score, coverage, mutual acceptance, lower clarification cost and lower inference time. A remaining exact tie shares rank. Keep full private outputs organiser-controlled until assessment ends; publish only agreed aggregate results, not private seeds, hidden member fields or world files.

Round 1 research submissions are collected through the forthcoming Google Form and close 9 October 2026 at 23:59 IST. Use form receipt timestamps for research submissions and revisions, and retain the submitted documents or fixed versions. Announce Round 1 results by 11 October at 22:00 IST. Round 2 starts 12 October, with final builds due 18 October at 23:59 IST through GitHub's Final submission issue form. The final build's latest immutable version pinned before that deadline is assessed; issue creation before the deadline does not validate a late revision. Research assessment does not add an undisclosed weight to the final technical score. Record technical corrections publicly in CHANGELOG.md and a repository issue.

## Submission validation and frozen versions

Verify the full commit SHA or immutable archive URL and SHA-256 before building. Reject changed archives and checksum mismatches. Assessment may run after the submission deadline; do not accept a replacement version to fix a failure discovered then. Teams can self-validate before the deadline, but an early organiser/private validation result is not guaranteed. Publish any common-kit correction for all affected teams and assess their frozen submissions under the same protocol.
