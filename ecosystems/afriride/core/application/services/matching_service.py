def match_driver(drivers, pickup):

    def distance(d):
        return ((d["lat"] - pickup["lat"])**2 +
                (d["lng"] - pickup["lng"])**2) ** 0.5

    sorted_drivers = sorted(drivers, key=distance)

    return sorted_drivers[0] if drivers else None