from evidence.models import EventLog

from .models import Fleet, FleetDriverAssignment, Vehicle


def create_fleet(owner, name, country):
    fleet = Fleet.objects.create(owner=owner, name=name, country=country)

    EventLog.objects.create(
        event_type="fleet_created",
        actor=owner,
        metadata={
            "fleet_id": fleet.id,
            "country": country,
        },
    )

    return fleet


def register_vehicle(fleet, plate_number, make, model, year, actor=None):
    vehicle = Vehicle.objects.create(
        fleet=fleet,
        plate_number=plate_number,
        make=make,
        model=model,
        year=year,
    )

    EventLog.objects.create(
        event_type="fleet_vehicle_registered",
        actor=actor or fleet.owner,
        metadata={
            "fleet_id": fleet.id,
            "vehicle_id": vehicle.id,
            "plate_number": plate_number,
        },
    )

    return vehicle


def assign_driver_to_vehicle(fleet, vehicle, driver, actor=None):
    assignment = FleetDriverAssignment.objects.create(
        fleet=fleet,
        vehicle=vehicle,
        driver=driver,
    )

    EventLog.objects.create(
        event_type="fleet_driver_assigned",
        actor=actor or fleet.owner,
        metadata={
            "fleet_id": fleet.id,
            "vehicle_id": vehicle.id,
            "driver_id": driver.id,
            "assignment_id": assignment.id,
        },
    )

    return assignment


def get_active_driver_assignment(driver):
    return FleetDriverAssignment.objects.filter(driver=driver, active=True).first()
