# BN-APD observable-trigger Phase 0 audit

- Frozen parent: `cef9af309a379b2e2ac339ed15752afc0b97b9db`.
- Branch: `exp/icba_bn_apd_observable_trigger_gate` in the existing ANNS main worktree.
- Evidence level: `EXPLORATORY_DEVELOPMENT_OBSERVABLE_TRIGGER_GATE`.
- Historical query IDs 0--499 are relabelled `bn_apd_replay_development`; IDs 0--199 were portal-selection data and 200--499 were attainability holdout data. Neither partition is independent confirmation in this stage.
- Sealed certification, evaluation, future-confirm, validation-dev, and formal-test roles remain inaccessible.
- Existing untracked directories were recorded and are outside the write scope.
- Resource audit at start: approximately 18 GiB free on `/`; 238 GiB RAM available; no active relevant experiment process.
- System CMake 3.16.3 was below the repository requirement. The repository `.venv/bin/cmake` was used without changing the environment.
- Project-side tracer source is isolated from third-party hnswlib. It records only deployment-visible search state. Truth is absent from its interface.
- Initial native-equivalence smoke: SIFT build b7, 200 development queries x 4 fixed ef values = 800 rows; top-10 mismatch count 0.

The instrumentation smoke is infrastructure evidence only. It is not evidence that an observable trigger exists.
