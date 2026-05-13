import argparse
from ecosystems.afriride.bootstrap import build_system
from ecosystems.afriride.core.application.command_handlers.ride_handler import RideHandler

system = build_system()
handler = RideHandler(system["store"])


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("action")
    parser.add_argument("--ride_id")
    parser.add_argument("--driver_id")
    parser.add_argument("--rider_id")

    args = parser.parse_args()

    if args.action == "request":
        result = handler.request({
            "ride_id": args.ride_id,
            "rider_id": args.rider_id,
            "pickup": {"lat": 0, "lng": 0},
            "dropoff": {"lat": 1, "lng": 1},
        })

    elif args.action == "assign":
        result = handler.assign_driver({
            "ride_id": args.ride_id,
            "driver_id": args.driver_id,
        })

    else:
        result = {"error": "Unknown action"}

    print(result)


if __name__ == "__main__":
    main()
