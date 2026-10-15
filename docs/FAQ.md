# Frequently asked questions

**Is this real Supabase data?** No. All records and outcomes are invented. Schema patterns informed the design, but no real rows or conversations are included. The generation assumptions are not a validated model of real relationships.

**Do I need a Supabase account or API key?** No. The complete static dataset is committed in `data/`, and simulator worlds can be generated locally. No production database is part of this challenge.

**What does an empty CSV cell mean?** Unknown. Use JSON to distinguish not-asked from declined and to enforce reciprocal constraints.

**Can I match someone with missing hard preferences?** No. Clarify disclosed information first. A declined answer stays unavailable; do not reconstruct it or override it.

**Can I ask nothing or match nobody?** Yes. Empty ask and pair lists are valid. Serving few people does not change the fixed primary-score denominator.

**Is missing feedback a rejection?** No. It is a missing observation. For an explicitly defined recorded-Yes target, no response means that event did not occur; it does not establish dislike.

**Must I use an LLM or train a neural network?** No. Rules, optimisation, statistical models, bandits and other methods are allowed. Offline CPU inference is required. The supplied baselines need no installed packages.

**Can I use external APIs?** Not during evaluated inference. Training tools and coding assistants may be used with declared provenance. Package inference assets and licences. Do not use unconsented sensitive personal data.

**Can I inspect simulator source?** Yes, for reproducibility and experiments. Reconstructing hidden state or random outcomes inside a policy is prohibited. Only observable JSON is valid episode input.

**Is local subprocess mode secure for untrusted submissions?** No. It is a development convenience. Assessed policies run in the offline container configuration with no host files mounted.

**Why separate pools?** Splitting rows from the same people or pairs leaks identity and history. Use the manifest's disjoint population splits and independent episode seeds.

**Why can my score be zero?** The qualifying outcome is deliberately downstream: mutual acceptance, a date and two timely second-meeting Yes answers. Small episodes can have very few such events. Compare multiple seeds and report the entire outcome funnel.

**Who owns our code?** You do. Participation does not grant a commercial licence. Supplied starter materials have their own permissions; a later product licence is a separate agreement.

**Where should we communicate?** Ask technical questions through the Question issue form. Public answers give everyone the same information. Use [the IITM Discord server](https://discord.gg/GwZdY54Gq) for event announcements and reminders. The repository contains authoritative technical rules and files.

**Where are private seeds and outcomes?** They are held by organisers and are deliberately absent from this public repository. Public development data is not a private leaderboard.

**Are prizes or institutional affiliations promised here?** No. This is the complete technical challenge release, not an institutional endorsement or employment offer.

**Are probability estimates required?** No. They are optional report diagnostics and do not affect ranking. If reported, distinguish directional acceptance from mutual acceptance and define the target and observation window.

**Can we fix a failure discovered after the deadline?** No. Self-validate using the published tests and public/container evaluator before the deadline. Early organiser/private validation is not guaranteed; later private assessment uses the frozen commit or checksum-pinned archive. See SUBMISSION.md for the full policy.

**Where are event announcements?** Join [the official Discord server](https://discord.gg/GwZdY54Gq). Technical questions and corrections remain public in this repository. Joining Discord does not complete event registration.

**How do we submit Round 1?** Use the Google Form the organisers will release soon through [Discord](https://discord.gg/GwZdY54Gq) and [the submission guide](SUBMISSION.md#research-submission). Research submissions close 9 October 2026 at 23:59 IST. GitHub Issues are not the research submission route.

**When are results and Round 2?** Round 1 results will be announced by 11 October 2026 at 22:00 IST. Round 2 starts 12 October. Final builds remain due 18 October 2026 at 23:59 IST through the Final submission issue form.
