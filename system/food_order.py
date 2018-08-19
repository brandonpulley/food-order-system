from datetime import datetime

NAME = 'name'
TEMP = 'temp'
SHELF_LIFE = 'shelfLife'
DECAY_RATE = 'decayRate'


TIME_ENTERED = 'time_entered'


class FoodOrder:

    def __init__(self, **kwargs):
        self.name = kwargs.get(NAME)
        self.temp = kwargs.get(TEMP)
        self.shelf_life = kwargs.get(SHELF_LIFE)
        self.decay_rate = kwargs.get(DECAY_RATE)
        self.order_entered_time = kwargs.get(TIME_ENTERED, datetime.now())

    def current_value(self, is_overflow=False):
        current_time_millis = datetime.now()
        seconds_since_ordered = (current_time_millis -
                                 self.order_entered_time).total_seconds()
        if is_overflow:
            current_value = (self.shelf_life - seconds_since_ordered) - \
                            (self.decay_rate * seconds_since_ordered * 2)
        else:
            current_value = (self.shelf_life - seconds_since_ordered) - \
                            (self.decay_rate * seconds_since_ordered)
        return current_value

    def to_json(self):
        return {
            NAME: self.name,
            TEMP: self.temp,
            SHELF_LIFE: self.shelf_life,
            DECAY_RATE: self.decay_rate,
            TIME_ENTERED: self.order_entered_time
        }

