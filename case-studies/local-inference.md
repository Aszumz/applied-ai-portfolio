Local language model evaluation

An interactive desktop companion and an agent performing repository tasks place different demands on local inference. The project explored two provider integrations and recorded performance and task completion separately.

My contributions

I used my development machine as the target environment for local model evaluation. The available records tie the evaluation setup to my projects. My individual authorship of the provider configuration, benchmark harness changes, and measured runs remains unverified.

AI-agent contributions

The evaluation harness used an OpenClaw agent to attempt scoped game-development tasks in a separate working copy. Another human contributor is credited with the original harness. The available records are too limited to attribute individual harness changes to an assistant.

Verified results

The audit inspected LM Studio and Ollama provider configurations. The benchmark profile explicitly selected local inference and cleared model fallbacks. One task produced a nonempty output artifact. A separate warm-inference baseline recorded generation rate, time to first token, and memory measurements for two input groups, with three measured runs per group. The desktop companion source also contains an Ollama-backed request path.

The [model demo](../demos/README.md) verifies that a run qualifies only when both the provider and the task checks match expectations. Its timings are synthetic.

Remaining limitations

The artifacts support an incomplete evaluation round. The baseline runs all reached the output cap, which limits interpretation to bounded generation under the recorded setup. Current provider availability, comparative model rankings, and completed-answer latency remain unverified.
