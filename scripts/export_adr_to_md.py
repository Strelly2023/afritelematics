import os
import yaml

SOURCE_DIR = "afritech/governance/adr"
OUTPUT_DIR = "afritech/adr"


def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)


def load_yaml(file_path):
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def format_markdown(data):
    adr = data["adr"]

    md = []
    md.append(f"# {adr['id']} — {adr['title']}\n")

    md.append(f"**Status:** {adr['status']}")
    md.append(f"**Type:** {adr['type']}")
    md.append(f"**Epoch:** {adr['epoch']}")
    md.append(f"**Approved At:** {adr['approved_at']}\n")

    md.append("## Context\n")
    md.append(adr.get("context", "") + "\n")

    md.append("## Decision\n")
    md.append(adr.get("decision", "") + "\n")

    md.append("## Model\n")
    md.append("**Inputs:**")
    for i in adr.get("model", {}).get("inputs", []):
        md.append(f"- {i}")

    md.append("\n**Outputs:**")
    for o in adr.get("model", {}).get("output", []):
        md.append(f"- {o}")

    md.append("\n## Invariants")
    for inv in adr.get("invariants", []):
        md.append(f"- {inv}")

    md.append("\n## Validation Pipeline")
    for v in adr.get("validation_pipeline", []):
        md.append(f"- {v}")

    md.append("\n## Implementation Notes\n")
    md.append(adr.get("implementation_notes", "") + "\n")

    md.append("\n## Consequences")

    md.append("\n### Positive")
    for p in adr.get("consequences", {}).get("positive", []):
        md.append(f"- {p}")

    md.append("\n### Negative")
    for n in adr.get("consequences", {}).get("negative", []):
        md.append(f"- {n}")

    return "\n".join(md)


def export_all():
    ensure_output_dir()

    for file in os.listdir(SOURCE_DIR):
        if not file.endswith(".yaml"):
            continue

        path = os.path.join(SOURCE_DIR, file)
        data = load_yaml(path)

        if "adr" not in data:
            continue

        md_content = format_markdown(data)

        output_file = os.path.join(
            OUTPUT_DIR,
            file.replace(".yaml", ".md")
        )

        with open(output_file, "w") as f:
            f.write(md_content)

        print(f"✅ Exported: {output_file}")


if __name__ == "__main__":
    export_all()