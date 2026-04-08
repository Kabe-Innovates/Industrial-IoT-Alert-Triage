# Jury Evaluation Rubric - Industrial IoT Alert Triage

This document is a complete review sheet for judges evaluating this OpenEnv submission.
It combines mandatory eligibility gates (pass/fail) and a weighted jury scoring rubric.

## 1) Eligibility Gates (Mandatory Pass/Fail)

A submission is considered eligible only if all items below pass.

1. Real-world utility is clear and non-trivial.
2. OpenEnv interface is implemented and operational:
3. reset
4. step(action)
5. state
6. At least 3 deterministic tasks exist.
7. Grading is deterministic and scores are normalized to 0.0 to 1.0.
8. Root-level inference runner exists and executes.
9. Structured inference logs include START, STEP, and END markers.
10. Docker build succeeds.
11. Hosted endpoint responds to POST /reset with HTTP 200.
12. openenv validate succeeds.

Disqualification triggers (automatic fail):
1. Missing or broken reset endpoint.
2. Docker image fails to build.
3. openenv validate fails.
4. Inference logging format is incompatible with evaluator parsing.
5. No deterministic grader behavior.

## 2) Weighted Jury Scoring (100 points)

### A. Problem Definition and Real-World Impact (20 points)

What to check:
1. Problem statement is concrete and operationally meaningful.
2. Decision space models realistic trade-offs (safety vs uptime).
3. Motivation is well documented.

Score anchors:
1. 0-5: vague or weakly justified use case.
2. 6-12: clear use case with partial operational framing.
3. 13-17: strong real-world framing with practical consequences.
4. 18-20: compelling, production-relevant framing with clear risk modeling.

### B. Environment and Task Design Quality (20 points)

What to check:
1. Task progression from easy to hard is coherent.
2. Observations and actions are well-typed and semantically aligned.
3. Task descriptions are precise and reproducible.

Score anchors:
1. 0-5: task design unclear or inconsistent.
2. 6-12: generally coherent but with limited depth.
3. 13-17: strong multi-task structure and clear progression.
4. 18-20: excellent task design with realistic escalation and coverage.

### C. Grading Determinism and Reward Design (20 points)

What to check:
1. Expected actions are deterministic per task step.
2. Partial credit and penalties are sensible.
3. Reward and aggregate score stay within 0.0 to 1.0.
4. Loop/no-op or unsafe behavior penalties exist.

Score anchors:
1. 0-5: unstable or opaque grading behavior.
2. 6-12: deterministic core logic but weak shaping.
3. 13-17: good deterministic shaping and score normalization.
4. 18-20: robust deterministic rubric with meaningful intermediate signals.

### D. Inference Compliance and Reproducibility (15 points)

What to check:
1. Root inference script runs without manual edits.
2. Required env vars are documented and respected.
3. START/STEP/END output format is parse-safe.
4. Baseline scoring is reproducible with published commands.

Score anchors:
1. 0-4: script is fragile or non-compliant.
2. 5-9: mostly functional with minor reproducibility gaps.
3. 10-13: reliable and compliant baseline behavior.
4. 14-15: strong reproducibility and evaluator-safe logging.

### E. Engineering Quality and Documentation (15 points)

What to check:
1. Repository structure is clean and understandable.
2. README explains motivation, interface, tasks, and usage.
3. Baseline scores are documented.
4. Build and validation instructions are clear.

Score anchors:
1. 0-4: sparse or confusing documentation.
2. 5-9: adequate docs with missing reviewer details.
3. 10-13: clear, complete, and easy to evaluate.
4. 14-15: polished reviewer-friendly documentation and workflow.

### F. Deployment Reliability and Ops Readiness (10 points)

What to check:
1. Containerized deployment works in hosted environment.
2. Health and reset endpoints are responsive.
3. Pre-submit checks are automated.
4. Runtime behavior remains stable across repeated checks.

Score anchors:
1. 0-2: deployment unstable or frequently failing.
2. 3-6: deploys but with reliability concerns.
3. 7-9: stable deployment and repeatable checks.
4. 10: production-like reliability for evaluation conditions.

## 3) Reviewer Evidence Map

Primary files to inspect:
1. README.md
2. openenv.yaml
3. inference.py
4. tasks.py
5. graders.py
6. models.py
7. server/environment.py
8. scripts/pre_submit_check.sh
9. Dockerfile

Primary commands to run:
1. ./.venv/bin/openenv validate
2. ./scripts/pre_submit_check.sh
3. curl -i -X POST https://<space-url>/reset -H "Content-Type: application/json" -d '{}'
4. curl -i https://<space-url>/health

Expected signals:
1. Validation returns success.
2. Pre-submit script passes all stages.
3. Hosted health and reset endpoints return HTTP 200.
4. Inference logs emit START, STEP, END records with parse-safe formatting.

## 4) Suggested Jury Scoring Sheet (Fill-In)

1. Problem Definition and Impact (20): ____
2. Environment and Task Design (20): ____
3. Grading and Reward Determinism (20): ____
4. Inference Compliance and Reproducibility (15): ____
5. Engineering Quality and Documentation (15): ____
6. Deployment Reliability (10): ____

Total (100): ____

Eligibility Gates Passed: YES / NO

Final Recommendation:
1. Accept
2. Accept with notes
3. Reject

Reviewer Notes:
1. Strengths:
2. Risks:
3. Required fixes:
