from mos.mobility_graph.models import MobilityNode
from mos.scheduling.models import Journey


def mobility_command_center():
    active_journeys = Journey.objects.filter(status="active")
    vehicles = MobilityNode.objects.filter(node_type="vehicle", active=True)
    drivers = MobilityNode.objects.filter(node_type="driver", active=True)
    fleet_assets = MobilityNode.objects.filter(node_type="fleet", active=True)
    public_transport_links = MobilityNode.objects.filter(
        node_type__in=["bus", "train", "station"],
        active=True,
    )

    return {
        "authority": "mobility_command_projection",
        "journeys_active": active_journeys.count(),
        "vehicles": vehicles.count(),
        "drivers": drivers.count(),
        "fleet_assets": fleet_assets.count(),
        "public_transport_links": public_transport_links.count(),
        "replay_integrity": None,
    }
