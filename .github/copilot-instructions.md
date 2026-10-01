# Copilot instructions for ad-growatt

## Project context
- This repository is an AppDaemon integration for Growatt inverter control in Home Assistant.
- Prefer small, surgical changes that preserve the existing AppDaemon patterns and configuration structure.
- Keep Home Assistant and AppDaemon compatibility in mind before changing entity names, secrets, or service wiring.

## Working practices
- Keep changes focused on the root cause; do not broaden the scope unless required.
- Prefer explicit validation for secrets, session state, and API responses before writing settings to the inverter.
- Preserve existing naming conventions used by the Home Assistant entities in the AppDaemon config.
- When changing user-facing behavior, update the relevant docs and release notes in the same patch.

## Repo workflow
- Maintain the active task list in `TODO.md` and keep it updated as work progresses.
- Use `CHANGELOG.md` for notable changes and release history.
- Use `tools/release.ps1` to prepare and publish tagged releases using Semantic Versioning.
- The README should include the current `Latest release:` line and the release instructions.

## Release process
1. Commit the intended changes.
2. Run the release helper:
   `pwsh -File .\tools\release.ps1 -Version 0.1.1`
3. Use `-Push` only when ready to create and push the tag.
4. The GitHub Action in `.github/workflows/release.yml` will create the GitHub Release from the tag.

## Safety notes
- This code interacts directly with inverter settings and can affect system behavior; avoid changing safety-critical defaults without explicit justification.
- Growatt API calls may be rate limited or temporarily blocked. Keep retries conservative and document the risk.

## Project Decisions
- Record any project-level decisions here.

## Commit Messages
- Write commit messages for human readers. Use a specific subject that describes the change, and add a concise body when it helps explain why or clarify scope. Use bullet lists for listing several distinct changes that need listing. use sections to separate different types of changes. Use the imperative mood in the subject line, e.g., "Add feature" instead of "Added feature" or "Adding feature".

## Release Notes
- Release notes are generated from commit messages. Use the `\.\tools\release.ps1` script to create a release commit and tag, then push both. GitHub Actions will publish a GitHub Release with generated release notes when the tag is pushed. Omit `-Push` to review the commit and tag before pushing them manually. Combine the commit messages for all changes since the previous release into a single release note. Use bullet lists for listing several distinct changes that need listing. use sections to separate different types of changes. Use meaningful icons such as ✅, ⚠️, 🛠️, and 🔧 when they improve clarity, but keep them consistent and concise so the notes remain easy to scan.

## Maintaining These Instructions
- When a lasting project preference or decision is established, add a concise, actionable rule here. Do not record secrets or temporary task details. if uncertain, ask the team for consensus before adding a rule. If a rule is later found to be unnecessary or counterproductive, remove it. ask the team for consensus before removing a rule.