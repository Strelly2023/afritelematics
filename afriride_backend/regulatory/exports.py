import csv
import json


def export_report_csv(payload, file_path):
    rows = payload.get("completed_rides", [])

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "ride_id",
                "rider_id",
                "driver_id",
                "completed",
                "replay_receipt_id",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return file_path


def export_report_json(payload, file_path):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, sort_keys=True, indent=2)

    return file_path
