Security and safe sharing

What is public

This portfolio uses independently written explanations, synthetic data, and small demonstrations built for review. The example policies describe ideas for agent boundaries and voice behavior. They have no credentials or usable service configuration. The offline Python programs require no accounts, API calls, or access to a device.

What stays private

Production configurations, API credentials, OAuth material, private paths, private conversations, workspace exports, logs, source histories, and proprietary code and assets stay outside this repository. The examples use invented project data, workspaces, and offer names. Evidence descriptions are scoped to the capability that was inspected, with limitations listed in each case study.

Reviewing future changes

Check the tracked file list and staged diff before sharing a revision. Review documentation, configuration, commit metadata, and media for identifiers and confidential information in addition to scanning for credential patterns. Record application surfaces with disposable test data, then review the frames, filename, and file metadata. The case studies identify how their clips were captured. Keep raw recordings and security reports outside the public repository.

Run a secret scanner on the whole working tree and all refs before publishing. Review any findings before proceeding. If a real credential has been committed or publicly shared, revoke or rotate it and review the affected history.

GitHub Actions uses a read-only repository token, pinned official actions, and synthetic inputs. It runs the demonstrations and unit tests without repository secrets.
