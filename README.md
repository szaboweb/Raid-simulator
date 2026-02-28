# Raid-simulator

Raid-simulator is a lightweight command-line simulator inspired by Raid: Shadow Legends clan boss fights. It lets you define a boss and a team using YAML files, simulate multiple fight rounds, and export per-round summaries and detailed logs in JSON, YAML, CSV or Excel formats.

Purpose
- Simulate clan-boss style encounters to evaluate team compositions and custom boss abilities.
- Produce reproducible battle logs for analysis, sharing, or automated processing.

How it works
- Input: provide a `boss` YAML, a `team` YAML, and an `abilities` YAML describing boss special rules.
- The simulator runs discrete rounds (configurable number) where each round applies combat rules, skills, and boss effects defined in the YAML files.
- Output: per-round summaries and detailed logs are written to `battle_log.json` (or other formats) and can be opened in Excel or uploaded to OneDrive via the included OneDrive helper.

Quickstart
1. Clone the repo:
	```bash
	git clone https://github.com/szaboweb/Raid-simulator.git
	cd Raid-simulator
	```
2. Install dependencies:
	```bash
	python3 -m venv .venv
	source .venv/bin/activate
	pip install -r requirements.txt
	```
3. Run an example simulation:
	```bash
	python -m src.simulator --boss examples/boss.yaml --team examples/team.yaml --abilities boss_abilities.yaml --out battle_log.json --rounds 50
	```

OneDrive / Excel
Use `src.onedrive` to upload generated Excel files to OneDrive (the README_SIMULATOR.md contains detailed steps for registering an Azure AD app and running the uploader).

See `README_SIMULATOR.md` for additional usage notes and examples.
# Raid-simulator