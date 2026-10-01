# Todo list

- [x] Audit the repo and identify key risks
- [ ] Fix the mismatched entity names and stale cached state bug
- [ ] Implement or disable the unimplemented save actions
- [ ] Harden API/session management and retry behavior
- [ ] Add defensive validation for secrets, API responses, and entity handling
- [ ] Document the release workflow and safety guidance

## Notes
- The main risks are in the AppDaemon state management and repeated Growatt login/session logic.
- The release tooling and changelog workflow are now part of the repo process.
