Simple Raid Shadow-style Clan Boss simulator

Usage:

- Install dependencies:

```bash
pip install -r requirements.txt
```

- Run an example:

```bash
python -m src.simulator --boss examples/boss.yaml --team examples/team.yaml --abilities boss_abilities.yaml --out battle_log.json --rounds 50
```

Outputs:
- `battle_log.json` (or .yaml/.csv/.xlsx) contains per-round summaries for up to 50 rounds.

You can edit `boss_abilities.yaml` to add or change boss special effects used by the simulator.

**OneDrive / Excel Online integration**

You can upload the generated Excel file to OneDrive and open it in Excel Online. Steps:

- Register an Azure AD app (App registrations) and note the `Application (client) ID`.
- Add delegated permission `Files.ReadWrite.All` and `offline_access` and grant admin consent.
- Install extra dependencies:

```bash
pip install msal requests
```

- Upload file (device-code flow will prompt you to authenticate):

```bash
python -m src.onedrive --client-id <YOUR_CLIENT_ID> --file battle_log.xlsx --remote Raid/battle_log.xlsx
```

The CLI prints a URL you can open directly in Excel Online.

