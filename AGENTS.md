# Repository instructions

## Local-first development

Read LOCAL_DEVELOPMENT.md before changing code or automation. Inspect existing tooling, detect the OS and installed dependencies, then run applicable tests and builds locally. Report commands, results and anything blocked by tools, credentials or platform compatibility; never claim an unrun check passed.

Reuse existing package managers, lockfiles and build tools. Keep secrets, signing keys, machine paths and generated build output out of git. Containers are optional unless already required.

Routine development checks should run locally; existing workflow_dispatch jobs are explicit fallback options. Do not add automatic hosted builds without explaining their necessity and resource implications. Preserve production deployments, security controls, schedules, data history, Pages and published downloads. Check branch protection and rulesets before changing triggers.

Commit and push verified task changes when authorized. Publish releases only on explicit request or under an established approved release process. Do not alter billing or account-wide Actions permissions without explicit approval. Read this repository's existing domain-specific instructions too.

Use the installed Agency HQ skill to select the relevant specialist. For substantive implementation or workflow changes, obtain an independent agent review before pushing and resolve its findings. Use the installed REA skill/tools when conclusions need packaged-app or runtime evidence; ordinary source checks use the repository tools. Report missing tool capabilities rather than claiming those checks ran.
