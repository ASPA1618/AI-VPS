def create_car_card(vin=None, info=None):
    car = {"vin": vin}
    if info:
        car.update(info)
    return car
