import argparse
import os
from typing import Any, Dict, List

from flask import Flask, redirect, render_template, request, send_file, url_for

from .exporter import export_log_to_excel
from .io import load_data, save_data
from .onedrive import upload_file_to_onedrive
from .simulator import build_boss, build_team, run_simulation
from .web_hero import build_selected_team, ensure_min_hero_slots, normalize_heroes, parse_heroes_from_form
from .web_views import build_excel_embed_url, build_simulation_preview, build_turn_order_rows


def create_app(
    heroes_path: str,
    boss_path: str,
    abilities_path: str | None,
    team_output_path: str,
    out_path: str,
    excel_out_path: str,
    onedrive_client_id: str | None,
    onedrive_tenant: str | None,
    onedrive_remote: str | None,
    default_rounds: int,
) -> Flask:
    app = Flask(__name__)
    app.config["HEROES_PATH"] = os.path.abspath(heroes_path)
    app.config["BOSS_PATH"] = os.path.abspath(boss_path)
    app.config["ABILITIES_PATH"] = os.path.abspath(abilities_path) if abilities_path else None
    app.config["TEAM_OUTPUT_PATH"] = os.path.abspath(team_output_path)
    app.config["OUT_PATH"] = os.path.abspath(out_path)
    app.config["EXCEL_OUT_PATH"] = os.path.abspath(excel_out_path)
    app.config["ONEDRIVE_CLIENT_ID"] = onedrive_client_id
    app.config["ONEDRIVE_TENANT"] = onedrive_tenant
    app.config["ONEDRIVE_REMOTE"] = onedrive_remote
    app.config["EXCEL_WEB_URL"] = None
    app.config["EXCEL_EMBED_URL"] = None
    app.config["DEFAULT_ROUNDS"] = default_rounds

    def load_heroes() -> List[Dict[str, Any]]:
        raw = load_data(app.config["HEROES_PATH"])
        return ensure_min_hero_slots(normalize_heroes(raw))

    @app.get("/")
    def index():
        simulation_preview, simulation_error = build_simulation_preview(app.config["OUT_PATH"])
        turn_order_rows, turn_order_error = build_turn_order_rows(app.config["OUT_PATH"])
        return render_template(
            "index.html",
            heroes=load_heroes(),
            message=request.args.get("message"),
            heroes_path=app.config["HEROES_PATH"],
            boss_path=app.config["BOSS_PATH"],
            abilities_path=app.config["ABILITIES_PATH"],
            team_output_path=app.config["TEAM_OUTPUT_PATH"],
            out_path=app.config["OUT_PATH"],
            excel_out_path=app.config["EXCEL_OUT_PATH"],
            rounds_default=app.config["DEFAULT_ROUNDS"],
            simulation_preview=simulation_preview,
            simulation_error=simulation_error,
            turn_order_rows=turn_order_rows,
            turn_order_error=turn_order_error,
            excel_web_url=app.config["EXCEL_WEB_URL"],
            excel_embed_url=app.config["EXCEL_EMBED_URL"],
        )

    @app.get("/excel/download")
    def download_excel():
        excel_path = app.config["EXCEL_OUT_PATH"]
        if not os.path.exists(excel_path):
            return redirect(url_for("index", message=f"Excel fájl még nem létezik: {excel_path}"))
        return send_file(excel_path, as_attachment=True)

    @app.post("/save")
    def save():
        try:
            heroes = parse_heroes_from_form(request.form)
            save_data(heroes, app.config["HEROES_PATH"])

            selected_team = build_selected_team(heroes)
            save_data(selected_team, app.config["TEAM_OUTPUT_PATH"])

            msg = f"Mentve: {len(heroes)} hős, {len(selected_team)} kijelölt csapattag."
        except Exception as error:
            msg = f"Hiba mentés közben: {error}"

        return redirect(url_for("index", message=msg))

    @app.post("/simulate")
    def simulate():
        try:
            rounds = int(request.form.get("rounds", app.config["DEFAULT_ROUNDS"]))
            heroes = load_heroes()
            selected_team_raw = build_selected_team(heroes)

            if not selected_team_raw:
                return redirect(url_for("index", message="Nincs kijelölt csapattag a szimulációhoz."))

            boss_data = load_data(app.config["BOSS_PATH"])
            boss = build_boss(boss_data if isinstance(boss_data, dict) else boss_data[0])
            if app.config["ABILITIES_PATH"]:
                abilities = load_data(app.config["ABILITIES_PATH"])
                if isinstance(abilities, dict):
                    boss.abilities.update(abilities)

            team = build_team(selected_team_raw)
            log = run_simulation(boss, team, rounds=rounds)
            save_data(log, app.config["OUT_PATH"])
            export_log_to_excel(log, app.config["EXCEL_OUT_PATH"])

            excel_message = ""
            if app.config["ONEDRIVE_CLIENT_ID"]:
                remote_path = app.config["ONEDRIVE_REMOTE"] or os.path.basename(app.config["EXCEL_OUT_PATH"])
                web_url = upload_file_to_onedrive(
                    app.config["EXCEL_OUT_PATH"],
                    remote_path,
                    app.config["ONEDRIVE_CLIENT_ID"],
                    tenant_id=app.config["ONEDRIVE_TENANT"],
                )
                app.config["EXCEL_WEB_URL"] = web_url
                app.config["EXCEL_EMBED_URL"] = build_excel_embed_url(web_url)
                excel_message = " OneDrive feltöltés kész, beágyazás frissítve."

            msg = (
                f"Szimuláció kész ({len(log)} kör). Mentve ide: {app.config['OUT_PATH']}. "
                f"Excel mentve ide: {app.config['EXCEL_OUT_PATH']}.{excel_message}"
            )
        except Exception as error:
            msg = f"Szimuláció hiba: {error}"

        return redirect(url_for("index", message=msg))

    return app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--heroes", default="examples/team.yaml", help="Hős lista fájl (yaml/json/csv/xlsx)")
    parser.add_argument("--boss", default="examples/boss.yaml", help="Boss fájl")
    parser.add_argument("--abilities", default="boss_abilities.yaml", help="Boss képességek fájl")
    parser.add_argument("--team-out", default="examples/team_selected.yaml", help="Kijelölt csapat mentési fájl")
    parser.add_argument("--out", default="battle_log.json", help="Szimuláció log mentési fájl")
    parser.add_argument("--excel-out", default="battle_log.xlsx", help="Excel kimeneti fájl (Events/Timeline/Team)")
    parser.add_argument("--onedrive-client-id", default=None, help="Azure AD app client id (opcionális, embedhez)")
    parser.add_argument("--onedrive-tenant", default=None, help="Azure tenant id (opcionális)")
    parser.add_argument("--onedrive-remote", default=None, help="OneDrive célútvonal, pl. Raid/battle_log.xlsx")
    parser.add_argument("--rounds", type=int, default=50, help="Alapértelmezett körszám")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    app = create_app(
        heroes_path=args.heroes,
        boss_path=args.boss,
        abilities_path=args.abilities,
        team_output_path=args.team_out,
        out_path=args.out,
        excel_out_path=args.excel_out,
        onedrive_client_id=args.onedrive_client_id,
        onedrive_tenant=args.onedrive_tenant,
        onedrive_remote=args.onedrive_remote,
        default_rounds=args.rounds,
    )
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
