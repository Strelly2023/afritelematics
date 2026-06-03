from .models import MobilityEdge, MobilityNode


def create_mobility_node(node_type, label, metadata=None):
    return MobilityNode.objects.create(
        node_type=node_type,
        label=label,
        metadata=metadata or {},
    )


def connect_mobility_nodes(source, destination, edge_type, metadata=None):
    return MobilityEdge.objects.create(
        source=source,
        destination=destination,
        edge_type=edge_type,
        metadata=metadata or {},
    )


def node_connections(node, edge_type=None):
    edges = MobilityEdge.objects.filter(source=node, active=True)
    if edge_type:
        edges = edges.filter(edge_type=edge_type)
    return edges.select_related("destination")
