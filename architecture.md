Architecture

Agent handoff and local evaluation

Observed pattern across the role configuration, project handoff, and evaluation harness. The benchmark uses a separate checkout and a local provider. Completion depends on evidence and review.

```mermaid
flowchart LR
    Owner["Project owner"] --> Brief["Bounded task brief"]
    Brief --> Gateway["OpenClaw gateway"]
    Gateway --> Profile["Role and workspace"]
    Profile --> Model["Local model in benchmark lane"]
    Profile --> Checkout["Isolated task checkout in benchmark lane"]
    Checkout --> Checks["Task-specific checks"]
    Checks --> Review["Review result and remaining work"]
    Review --> Decision["Owner acceptance or reassignment"]
```

Windows voice companion

Source-observed components are shown at a high level. The Windows desktop and speech paths were inspected separately from Android.

```mermaid
flowchart LR
    Input["Typed input or microphone"] --> Intent["Intent and request handling"]
    Input --> STT["Local transcription"]
    STT --> Intent
    Intent --> Direct["Dedicated desktop actions"]
    Intent --> LLM["Local Ollama model"]
    LLM --> Reply["Reply and action feedback"]
    Direct --> Reply
    Reply --> Output["Desktop UI and local speech"]
```

Android voice interaction

Showcase design. The Android demo models these states with generated events.

```mermaid
flowchart TD
    Idle["Idle"] --> Tap["User starts listening"]
    Tap --> Permission{"Microphone authorized?"}
    Permission -->|No| Idle
    Permission -->|Yes| Capture["Capture and transcribe"]
    Capture --> Inference["Model adapter"]
    Inference --> Speech["Play response"]
    Speech --> Idle
    Capture --> Cancel["Cancel and retire request"]
    Inference --> Cancel
    Speech --> Cancel
    Cancel --> Idle
```

Godot campaign service boundary

Observed division of responsibilities. The demo exercises the same engineering idea with independently written in-memory code and fictional offers.

```mermaid
flowchart LR
    Player["Player"] --> Menu["Shop menu"]
    Menu --> Service["Campaign service"]
    Service --> Inventory["Owned items and wallet"]
    Service --> Ledger["Persisted offer receipt"]
    Ledger --> Load["Save and restore"]
    Load --> Service
    Service --> Menu
```
