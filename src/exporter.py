import argparse
from typing import List, Dict, Any, Union

import pandas as pd

from .io import load_data
from .onedrive import upload_file_to_onedrive


def _build_event_rows(log: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for r in log:
        rd = r.get("round")
        boss_hp = r.get("boss_hp")
        events = r.get("events", [])
        if events:
            for ev in events:
                rows.append({
                    "round": rd,
                    "boss_hp": boss_hp,
                    "actor": ev.get("actor"),
                    "target": ev.get("target"),
                    "damage": ev.get("dmg"),
                })
        else:
            rows.append({"round": rd, "boss_hp": boss_hp, "actor": None, "target": None, "damage": None})
    return rows


def _build_team_rows(log: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for r in log:
        rd = r.get("round")
        for t in r.get("team", []):
            rows.append({
                "round": rd,
                "member": t.get("name"),
                "hp": t.get("hp"),
                "alive": t.get("alive"),
                "damage_done": t.get("damage_done"),
            })
    return rows


def export_log_to_excel(log_or_path: Union[str, List[Dict[str, Any]]], out_path: str):
    """Export a battle log (list or file path) into an Excel workbook with two sheets: Events and Team.

    The sheets will have bold headers and an autofilter enabled.
    """
    if isinstance(log_or_path, str):
        log = load_data(log_or_path)
    else:
        log = log_or_path

    events = _build_event_rows(log)
    team = _build_team_rows(log)

    df_events = pd.DataFrame(events)
    df_team = pd.DataFrame(team)

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df_events.to_excel(writer, sheet_name="Events", index=False)
        df_team.to_excel(writer, sheet_name="Team", index=False)

        # Access workbook and worksheets to set header formatting and filters
        wb = writer.book
        ws_events = writer.sheets["Events"]
        ws_team = writer.sheets["Team"]

        # set autofilter range (uses openpyxl indexing)
        if not df_events.empty:
            max_row = df_events.shape[0] + 1
            max_col = df_events.shape[1]
            ws_events.auto_filter.ref = ws_events.dimensions
            ws_events.freeze_panes = "A2"

        if not df_team.empty:
            ws_team.auto_filter.ref = ws_team.dimensions
            ws_team.freeze_panes = "A2"

        # Bold headers
        try:
            from openpyxl.styles import Font
        except Exception:
            Font = None

        if Font is not None:
            for cell in next(ws_events.iter_rows(min_row=1, max_row=1)):
                cell.font = Font(bold=True)
            for cell in next(ws_team.iter_rows(min_row=1, max_row=1)):
                cell.font = Font(bold=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="infile", required=True, help="Input battle log (json/yaml/csv/xlsx)")
    parser.add_argument("--out", dest="outfile", required=True, help="Output xlsx path")
    parser.add_argument("--upload", action="store_true", help="Upload the generated xlsx to OneDrive after export")
    parser.add_argument("--client-id", dest="client_id", help="Azure AD app client id (required for upload)")
    parser.add_argument("--tenant", dest="tenant", help="Azure AD tenant id (optional)")
    parser.add_argument("--remote", dest="remote", help="Remote path on OneDrive (default: basename of outfile)")
    args = parser.parse_args()

    export_log_to_excel(args.infile, args.outfile)
    print(f"Exported {args.infile} -> {args.outfile}")

    if args.upload:
        if not args.client_id:
            parser.error("--upload requires --client-id to be provided")
        remote_path = args.remote or None
        if remote_path is None:
            import os
            remote_path = os.path.basename(args.outfile)
        print("Uploading to OneDrive... follow the device-code instructions printed to complete authentication")
        try:
            url = upload_file_to_onedrive(args.outfile, remote_path, args.client_id, tenant_id=args.tenant)
            print("Upload complete. Open in Excel Online:")
            print(url)
        except Exception as e:
            print("Upload failed:", e)


if __name__ == "__main__":
    main()
