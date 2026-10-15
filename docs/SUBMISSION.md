# Submission instructions

| Milestone | Date and time (IST) |
|---|---|
| Round 1 research submission closes | 9 October 2026, 23:59 |
| Round 1 results announced by | 11 October 2026, 22:00 |
| Round 2 build starts | 12 October 2026 |
| Final build submission closes | 18 October 2026, 23:59 |

All times are IST (UTC+05:30). Teams have one to four participants. Round 1 research submissions use a Google Form that the organisers will release soon. Round 2 final build submissions use the Final submission issue form in this repository.

## Research submission

The Google Form link is not yet available. It will be released through [the official Discord server](https://discord.gg/GwZdY54Gq) and added to this guide. GitHub Issues are not an accepted research submission route.

Prepare a PDF or Markdown approach note covering the problem interpretation, hypothesis, reciprocal feasibility and any optional probability analysis, allocation method, clarification policy, handling of missing and delayed data, planned baselines, ablations and failure cases. Follow the form's upload or document-link instructions once it is released.

Submit by **9 October 2026, 23:59 IST**. The Google Form receipt timestamp determines whether an entry or revision arrived before the deadline; retain its submission confirmation. If submitting a document link, identify a fixed version and do not change that version after the deadline. Revisions received before the deadline replace the team's earlier entry.

Round 1 results will be announced by **11 October 2026, 22:00 IST**. Round 2 starts **12 October 2026**.

## Final submission

Your project must include:

- Policy source implementing POLICY_INTERFACE.md and a Dockerfile with all required inference assets.
- A README with exact setup and evaluation commands, Python/dependency versions, declared training seeds and inference random seed.
- Machine-readable full-episode results for greedy, no-clarification, random-feasible and your method on the same seeds and scenarios.
- A report with scenario-level outcomes, coverage, waiting times, clarification costs, missing feedback, runtime, at least one hypothesis-driven ablation and limitations.
- Model/data/tool provenance, dependency licences and any training-compute requirements.

Run from your project root:

```bash
python -m unittest -v
python verify_data.py
python evaluate.py --seeds 101,102,103 --variants all --output results/final.json
docker build -t sequential-policy:submission .
python evaluate.py --image sequential-policy:submission --seeds 101 --output results/container_check.json
```

For a project copied from this starter, commit the report and experiment JSON explicitly, since `results/` is ignored by default. Do not commit private organiser data, personal records, secrets or development caches. The test suite checks the kit; add meaningful checks for your method where needed.

Open a Final submission issue with a public source URL, report URL and results URL. Pin the source using either a repository URL and full 40-character commit SHA, or an immutable publicly downloadable archive URL and full SHA-256 checksum of its exact bytes. Use a version-specific archive, not a latest-branch ZIP URL, editable shared-drive file or mutable download link. A changed archive or checksum mismatch is invalid. The report, results and required inference assets must be included in the pinned submitted version. Declare external assets and their licences. The latest commit or archive pinned in the issue before the final deadline is the assessed build version; an earlier issue creation time does not make a later revision timely. Amend the issue before the deadline to replace it. After the deadline, fixes cannot change that version.

## Validation and execution failures

For Round 2, teams can obtain validation results before the final deadline by running the published tests, data verification and local/container evaluation commands in this guide. A successful public run checks the interface and tested episodes; it does not guarantee that every private episode will be valid. Organiser validation feedback, if received before the deadline, may be used to revise and resubmit before it. Individual pre-deadline organiser feedback and early private assessment are not guaranteed.

The Round 1 research note is frozen at the Google Form deadline. The Round 2 submitted commit or archive is frozen at the final build deadline. Private assessment may take place afterwards. Failures first discovered during that assessment do not permit post-deadline code, dependency, asset or packaging fixes, and an invalid assessed episode makes the entry ineligible. Organiser errors or defects in the common kit must be handled through the public corrections policy for all affected teams, without silently replacing a team's submitted version.

A container build must succeed without credentials. Evaluation itself has no network or GPU. All assessed episodes must be valid. Runtime failures, malformed output, invalid asks or introductions and resource overruns make the submission ineligible for ranking. No interface or presentation replaces the executable policy.

Participants retain ownership of their submissions. A public submission does not itself license commercial product use. Put your chosen licence in your own project and discuss any later Vouchsafe agreement separately.
