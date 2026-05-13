"""
Consumes events from event bus (future async system).
"""

def handle_event(event, projection_bus):
    """
    Receives events from stream and updates projections.
    """
    projection_bus.publish(event)