# Vouchsafe integration boundary

The portable component is the JSON policy, not a direct database connection. The policy receives a versioned observable state and returns clarification requests or feasible pairs. It must never receive database credentials or hidden outcome state.

For an authorised later integration:

1. A server-side adapter maps production IDs to temporary opaque policy IDs and retains the reverse mapping privately.
2. Normalise authorised observations into the versioned fields. Map an unknown or declined answer explicitly; never fabricate a default preference. Reject incompatible production semantics rather than silently coercing them.
3. Apply current reciprocal constraints, availability and outstanding-introduction checks before sending the observed state.
4. Run the policy offline through the JSON boundary. Validate the returned requests or pair batch against current server-side state again.
5. Return suggestions for human review. Record the policy version, observed input time, clarification decisions and final approved allocation.
6. Translate IDs back only inside the authorised service. Record subsequent feedback with event and observation times.

The kit is a research contract. Its fictional zones, immediate clarification and whole-day timing are simplifications. No production writes, automatic introductions, commercial licence to student code or production outcome calibration are supplied by this repository. Product use requires a separate licence and validation on authorised inputs.
