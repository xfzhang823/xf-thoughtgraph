# Excluded components

- **Frontend:** `my-react-app/`, `index.js`, and web assets remain application code and are not imported by the package.
- **VoiceAssist:** The former `VoiceAssist/` prototype was extracted to the separate `voice-assist` repository. It remains unsupported application/reference code, is not imported by or included in this package, and future voice work belongs in separate projects such as `voice-tools` and `bot0-voice-assistant`.
- **Runtime/generated data:** `input_output/`, thought-generation outputs, session state, memory, and checked-in artifacts remain data/application fixtures, not package code.
- **Experiments:** evaluation/comparison scripts, sandboxes, demos, and manual runners remain unvalidated experiments.
- **Backup files:** `*_backup.py`, `*_SAVED.py`, and `*_GOLD.py` remain historical copies.
- **Deployment-specific code:** root services, FastAPI/TTS entry points, startup scripts, authentication, terminal loops, and machine-specific configuration remain application concerns.
- **Retired legacy code:** the former `src/agents/`, `src/pipelines/`, `src/utils/`, `src/project_config.py`, and legacy interview services were removed from this repository. They were application behavior, provider construction, or filesystem-oriented support rather than canonical graph functionality.

No excluded surface is imported by `src/xf_thoughtgraph/`. The former VoiceAssist prototype is maintained separately; no broad migration or redesign is performed here.
