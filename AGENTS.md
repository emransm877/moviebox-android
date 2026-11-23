# Repository instructions

## Local-first development

Read LOCAL_DEVELOPMENT.md before changing code or automation. Inspect existing tooling, detect the OS and installed dependencies, then run applicable tests and builds locally. Report commands, results and anything blocked by tools, credentials or platform compatibility; never claim an unrun check passed.

Reuse existing package managers, lockfiles and build tools. Keep secrets, signing keys, machine paths and generated build output out of git. Containers are optional unless already required.

Routine development checks should run locally; existing workflow_dispatch jobs are explicit fallback options. Do not add automatic hosted builds without explaining their necessity and resource implications. Preserve production deployments, security controls, schedules, data history, Pages and published downloads. Check branch protection and rulesets before changing triggers.

Commit and push verified task changes when authorized. Publish releases only on explicit request or under an established approved release process. Do not alter billing or account-wide Actions permissions without explicit approval. Read this repository's existing domain-specific instructions too.

Use the installed Agency HQ skill to select the relevant specialist. For substantive implementation or workflow changes, obtain an independent agent review before pushing and resolve its findings. Use the installed REA skill/tools when conclusions need packaged-app or runtime evidence; ordinary source checks use the repository tools. Report missing tool capabilities rather than claiming those checks ran.

## Owner rules (apply on every machine, for Claude and Codex)

These are standing instructions from the maintainer. They override convenience.

1. **Never start GitHub Actions without explicit confirmation.** Do not enable,
   trigger, dispatch, re-run or schedule any workflow, change workflow triggers or
   Actions settings, or push anything whose purpose or side effect is to start a
   workflow, unless the maintainer has explicitly said yes for that specific run.
   A previous yes never carries over. Before pushing, check `.github/workflows/*`
   push/path triggers and say whether the push would start anything.
2. **Websites are built and tested locally, then published from `gh-pages`.**
   For GitHub Pages sites, run the repository's own build and tests on the local
   machine, then commit only the finished static files plus an empty `.nojekyll`
   to the `gh-pages` branch, with Pages set to "Deploy from a branch: gh-pages /
   (root)". This keeps the same site address and does not depend on Actions.
   Switching a repository's Pages source the first time needs the maintainer's OK.
3. **Review before pushing.** Use the installed Agency HQ skill to pick the
   specialist for the work. Substantive code changes get an independent Agency HQ
   engineering review (code-reviewer + reality-checker, plus frontend/performance
   where relevant) and every blocking finding is fixed before pushing.
4. **Always sync first.** Work happens on more than one PC. `git fetch` and check
   the current branch and other branches before assuming the local copy is current.
   Never discard someone else's uncommitted work; save it on a side branch.
5. **Report honestly.** State exactly which checks ran and their results; never
   claim an unrun check passed. Publishing releases, website updates and social
   posts happens only when the maintainer asks for it.
