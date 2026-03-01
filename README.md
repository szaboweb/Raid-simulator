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

Webes szerkesztő (hős adatok + csapat kijelölés)
- Indítás:
	```bash
	python -m src.webapp --heroes examples/team.yaml --boss examples/boss.yaml --abilities boss_abilities.yaml --team-out examples/team_selected.yaml --out battle_log.json --excel-out battle_log.xlsx --port 8000
	```
- Nyisd meg böngészőben: `http://localhost:8000`
- A felületen:
	- szerkeszthetők a hős statok (pl. `skill_multiplier`),
	- a stat sorrend egyszerű: `HP, ATK, Defense, Speed, Crit rate, Crit damage, RES, ACC`,
	- a képesség oszlopok egyszerűsítve: csak `A1, A2, A3, A4`,
	- checkbox-szal kijelölhetők a csapattagok,
	- menthető a teljes hőslista és külön a kijelölt csapat,
	- futtatható a szimuláció közvetlenül a kijelölt csapatból,
	- a „Körönkénti sorrend” táblában a boss akció (`AOE1/AOE2/STUN`) is látható,
	- automatikusan készül Excel (`Events`, `Timeline`, `Team` sheet), ahol a `Timeline` mutatja a körön belüli sorrendet (`R1-T1`, `R1-T2`...), a sebzést és a képesség oszlopot (`A1/A2/A3`).

Megjegyzés a boss profilhoz
- Az `examples/boss.yaml` fájlban `infinite_hp: true` van beállítva, ezért benchmark módon a boss nem hal meg, és a cél a minél nagyobb összsebzés elérése a körlimit alatt.

Beágyazott Excel nézet (opcionális, OneDrive)
- Ha OneDrive linkből iframe-ben szeretnéd látni az Excelt, indítsd így:
	```bash
	python -m src.webapp --heroes examples/team.yaml --boss examples/boss.yaml --abilities boss_abilities.yaml --team-out examples/team_selected.yaml --out battle_log.json --excel-out battle_log.xlsx --onedrive-client-id <CLIENT_ID> --onedrive-tenant <TENANT_ID> --onedrive-remote Raid/battle_log.xlsx --port 8000
	```
- Szimuláció futtatás után a weboldal megpróbálja feltölteni az Excel fájlt OneDrive-ra, majd beágyazott nézetben megjeleníteni.

OneDrive / Excel
Use `src.onedrive` to upload generated Excel files to OneDrive (the README_SIMULATOR.md contains detailed steps for registering an Azure AD app and running the uploader).

See `README_SIMULATOR.md` for additional usage notes and examples.
# Raid-simulator