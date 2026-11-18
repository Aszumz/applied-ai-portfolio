Offline demonstrations

Run individual scenarios from the repository root with `python demos/run.py NAME`. To compare all results with the fixture expectations, run `python demos/run.py all --verify`.

| Name | Input | Expected behavior |
| --- | --- | --- |
| `workflows` | Three generated task assignments | A scoped task can reach review. Scope expansion is denied and failed checks require follow-up. |
| `models` | Three fictional benchmark rows | Eligibility requires the configured provider and passing checks. Timing is shown in the fixture as context. |
| `desktop` | Fictional accessibility matches and screenshot estimates | An estimate can support pointing. A click requires one accessible match and a clickable point. |
| `voice` | Permission and request events | Permission denial and cancellation stop the request. A stale completion is ignored while the next request remains active. |
| `game` | An earned item, a shop offer, and a starting wallet | One purchase succeeds, then a serialized and restored receipt blocks a replay without altering the wallet or inventory. |

The runner reads the fixture, prints JSON, and performs the comparison in memory. It has no service calls, device access, or account dependencies. Malformed input exits with status 2. An expected-result mismatch exits with status 1.

Run regression tests from the repository root with `python -m unittest discover -s tests -v`. They cover invalid input, scope expansion, ambiguous clicks, stale requests, and purchase rejection after reload.
