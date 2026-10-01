# Todo list

- [x] Audit the repo and identify key risks
- [x] Define the release scope as `appdaemon/` and `packages/` only
- [ ] Fix the mismatched entity names and stale cached state bug
- [ ] Implement or disable the unimplemented save actions
- [ ] Harden API/session management and retry behavior
- [ ] Add defensive validation for secrets, API responses, and entity handling
- [ ] Document the release workflow and safety guidance

## Notes
- The main risks are in the AppDaemon state management and repeated Growatt login/session logic.
- The deployable release payload is limited to the `appdaemon/` and `packages/` directories.
- Repo maintenance files such as `README.md`, `CHANGELOG.md`, and tooling remain part of the repository workflow but are not part of the deployment payload.
