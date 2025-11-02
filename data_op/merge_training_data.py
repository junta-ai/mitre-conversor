import json
import os
from pathlib import Path


def load_mitre_training():
    mitre_path = Path("data/raw/categories/mitre_training.json")
    with open(mitre_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_situations():
    situations_data = []
    situations_folder = Path("data/raw/situations")

    for dirpath, dirnames, filenames in os.walk(situations_folder):
        narrativa_file = None
        tabela_file = None

        for filename in filenames:
            if filename.startswith("narrativa") and filename.endswith(".txt"):
                narrativa_file = os.path.join(dirpath, filename)
            if filename.startswith("tabela") and filename.endswith(".txt"):
                tabela_file = os.path.join(dirpath, filename)

        if narrativa_file and tabela_file:
            try:

                with open(narrativa_file, "r", encoding="utf-8") as f:
                    narrative = f.read().strip()

                with open(tabela_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()

                if len(lines) > 2:

                    for line in lines[2:]:
                        line = line.strip()
                        if not line or line.startswith("|---"):
                            continue

                        parts = [p.strip() for p in line.split("|") if p.strip()]
                        if len(parts) >= 4:
                            technique_id = parts[0]
                            technique_name = parts[1]
                            description = parts[2]
                            correction = parts[3]

                            combined_input = f"{narrative}\n\n{description}"

                            situations_data.append(
                                {
                                    "input": combined_input,
                                    "output": {
                                        "technique_id": technique_id,
                                        "technique_name": technique_name,
                                        "tactic": "Mixed",
                                        "correction": correction,
                                        "source": "practical_situation",
                                    },
                                }
                            )

            except Exception as e:
                print(f"Erro em {os.path.basename(dirpath)}: {e}")

    return situations_data


def merge_data():
    mitre_data = load_mitre_training()

    situations_data = load_situations()

    merged_data = mitre_data + situations_data

    output_path = Path("data/processed/mitre_techniques_complete.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    merge_data()
