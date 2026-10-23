import os
import sys
import json
import shutil
import secrets
import subprocess

NUM_TEAMS = int(sys.argv[2]) if len(sys.argv) > 2 else 2


def update_ctf_json(num_teams):
    ctf_config = {
        "title": "HAM-DEFCON 2.0",
        "flagValidityInRounds": 2,
        "checkedRoundsPerRound": 3,
        "roundLengthInSeconds": 60,
        "dnsSuffix": "ctf.local",
        "teamSubnetBytesLength": 15,
        "flagSigningKey": "ir7PRm0SzqzA0lmFyBfUv68E6Yb7cjbJDp6dummqwr0Od70Sar7P27HVY6oc8PuW",
        "teams": [],
        "services": [
            {
                "id": 1,
                "name": "DocuVault",
                "flagsPerRoundMultiplier": 1,
                "noisesPerRoundMultiplier": 0,
                "havocsPerRoundMultiplier": 0,
                "weightFactor": 1,
                "checkers": ["http://127.0.0.1:18000"]
            },
            {
                "id": 2,
                "name": "PulseChat",
                "flagsPerRoundMultiplier": 1,
                "noisesPerRoundMultiplier": 0,
                "havocsPerRoundMultiplier": 0,
                "weightFactor": 1,
                "checkers": ["http://127.0.0.1:18001"]
            },
            {
                "id": 3,
                "name": "SwiftShop",
                "flagsPerRoundMultiplier": 1,
                "noisesPerRoundMultiplier": 0,
                "havocsPerRoundMultiplier": 0,
                "weightFactor": 1,
                "checkers": ["http://127.0.0.1:18003"]
            }
        ]
    }

    for team_id in range(1, num_teams + 1):
        ctf_config["teams"].append({
            "id": team_id,
            "name": f"Team {team_id}",
            "teamSubnet": f"::ffff:127.0.0.{team_id}",
            "address": "127.0.0.1"
        })

    with open("ctf.json", "w") as f:
        json.dump(ctf_config, f, indent=2)

    print(f"[+] ctf.json successfully synchronized with {num_teams} teams!")


def setup_team_directories():
    print(f"[*] Provisioning {NUM_TEAMS} teams and credentials...")
    creds = []

    for team_id in range(1, NUM_TEAMS + 1):
        team_user = f"team{team_id}"
        team_pass = secrets.token_hex(4)
        port_ttyd = 7600 + team_id
        port_docuvault = 10000 + (team_id * 10) + 0
        port_pulsechat = 10000 + (team_id * 10) + 1
        port_swiftshop = 10000 + (team_id * 10) + 3

        team_dir = f"./data/team{team_id}"
        os.makedirs(f"{team_dir}/docuvault_data", exist_ok=True)
        os.makedirs(f"{team_dir}/pulsechat_data", exist_ok=True)
        os.makedirs(f"{team_dir}/swiftshop_data", exist_ok=True)

        if not os.path.exists(f"{team_dir}/docuvault"):
            if os.path.exists("./HAM-DEFCON/service-docuvault/service/app"):
                shutil.copytree("./HAM-DEFCON/service-docuvault/service/app", f"{team_dir}/docuvault")
        if not os.path.exists(f"{team_dir}/pulsechat"):
            if os.path.exists("./HAM-DEFCON/service-pulsechat/service/app"):
                shutil.copytree("./HAM-DEFCON/service-pulsechat/service/app", f"{team_dir}/pulsechat")
        if not os.path.exists(f"{team_dir}/swiftshop"):
            if os.path.exists("./HAM-DEFCON/service-swiftshop/service/app"):
                shutil.copytree("./HAM-DEFCON/service-swiftshop/service/app", f"{team_dir}/swiftshop")

        env_content = f"""TEAM_ID={team_id}
                    TEAM_USER={team_user}
                    TEAM_PASS={team_pass}
                    PORT_TTYD={port_ttyd}
                    PORT_DOCUVAULT={port_docuvault}
                    PORT_PULSECHAT={port_pulsechat}
                    PORT_SWIFTSHOP={port_swiftshop}
                    """
        with open(f"{team_dir}/.env", "w") as f:
            f.write(env_content)

        creds.append({
            "id": team_id,
            "user": team_user,
            "pass": team_pass,
            "ttyd": port_ttyd,
            "docuvault": port_docuvault,
            "pulsechat": port_pulsechat,
            "swiftshop": port_swiftshop
        })

    with open("teams_credentials.txt", "w") as f:
        f.write(f"{'Team':<7} | {'User':<8} | {'Password':<10} | {'WebTTY URL':<24} | {'DocuVault':<10} | {'PulseChat':<10} | {'SwiftShop':<10}\n")
        f.write("-" * 92 + "\n")
        for c in creds:
            f.write(f"Team {c['id']:<2} | {c['user']:<8} | {c['pass']:<10} | http://<IP>:{c['ttyd']:<12} | Port {c['docuvault']:<5} | Port {c['pulsechat']:<5} | Port {c['swiftshop']:<5}\n")

    print(open("teams_credentials.txt").read())
    print("[+] Master credentials saved to teams_credentials.txt")

    update_ctf_json(NUM_TEAMS)


def start_teams():
    setup_team_directories()
    for team_id in range(1, NUM_TEAMS + 1):
        print(f"[*] Starting containers for Team {team_id}...")
        cmd = [
            "docker", "compose",
            "-p", f"team{team_id}",
            "--env-file", f"./data/team{team_id}/.env",
            "-f", "template.compose.yml",
            "up", "-d"
        ]
        subprocess.run(cmd, check=True)
    print(f"\n[SUCCESS] All {NUM_TEAMS} teams deployed, ctf.json synced, and containers live!")


def stop_teams():
    print(f"[*] Stopping all {NUM_TEAMS} teams...")
    for team_id in range(1, NUM_TEAMS + 1):
        cmd = [
            "docker", "compose",
            "-p", f"team{team_id}",
            "--env-file", f"./data/team{team_id}/.env",
            "-f", "template.compose.yml",
            "down"
        ]
        subprocess.run(cmd)
    print(f"\n[+] All {NUM_TEAMS} team containers stopped.")


if __name__ == "__main__":
    action = sys.argv[1].lower() if len(sys.argv) > 1 else "help"
    if action == "start":
        start_teams()
    elif action == "stop":
        stop_teams()
    else:
        print("Usage:")
        print("  python3 manage.py start [NUM_TEAMS]   # e.g. start 2 (testing) or start 20 (event)")
        print("  python3 manage.py stop  [NUM_TEAMS]   # stops and tears down team containers")