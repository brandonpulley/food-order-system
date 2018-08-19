import sys
import threading
from datetime import datetime
from time import sleep

NAME = 'name'
TEMP = 'temp'
SHELF_LIFE = 'shelfLife'
DECAY_RATE = 'decayRate'

HOT_MAX_COUNT = 15
COLD_MAX_COUNT = 15
FROZEN_MAX_COUNT = 15
OVERFLOW_MAX_COUNT = 20

TEMP_HOT = 'hot'
TEMP_COLD = 'cold'
TEMP_FROZEN = 'frozen'


FOOD_ORDER_TIME_DIFF = 0.05

def add_orders(orders_json_array: []):
    for order_dict in orders_json_array:
        sleep(FOOD_ORDER_TIME_DIFF)
        _add_order(order_dict)

        sys.stdout.flush()
    return {'shelves': _food_holder.shelves,
            'overflow': _food_holder.overflow_shelf}


def _add_order(order: dict):

    food_order = FoodOrder(**order)
    _food_holder.add_food_order(food_order)
    print('adding order:: ', food_order.to_json())


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
        seconds_since_ordered = (self.order_entered_time -
                                 current_time_millis).total_seconds()
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



MAX = 'max'
ORDERS = 'orders'
OVERFLOW = 'overflow'

_shelves = {
    'hot': {
        ORDERS: [],
        MAX: HOT_MAX_COUNT
    },
    'cold': {
        ORDERS: [],
        MAX: COLD_MAX_COUNT
    },
    'frozen': {
        ORDERS: [],
        MAX: FROZEN_MAX_COUNT
    }
}


class FoodHolder:

    add_lock = threading.Lock()
    get_lock = threading.Lock()
    overflow_shelf = {
        OVERFLOW: {
                ORDERS: [],
                MAX: OVERFLOW_MAX_COUNT
            }
    }

    def __init__(self, shelves):
        self.shelves = shelves
        self.waste_bucket = []

    def add_food_order(self, food_order: FoodOrder):
        self.add_lock.acquire()
        try:
            self._add_food_order(food_order)
        finally:
            self.add_lock.release()

    def _add_food_order(self, food_order):
        shelf_type = food_order.temp

        if shelf_type not in self.shelves:
            # TODO: Error!!
            pass
        else:
            shelf = self.shelves[shelf_type]
            if len(shelf[ORDERS]) >= shelf[MAX]:
                self._add_order_to_overflow(food_order)
            else:
                print('not overflow yet......')
                shelf[ORDERS].append(food_order.to_json())
                self.shelves[shelf_type] = shelf

    def _add_order_to_overflow(self, order):
        # TODO add to overflow shelf
        print('adding this to overflow')
        order_type = order.temp
        if len(self.overflow_shelf[OVERFLOW][ORDERS]) >= \
                self.overflow_shelf[OVERFLOW][MAX]:
            removed_type = self._remove_decayed_order(order_type)

            if removed_type == OVERFLOW:
                shelf = self.overflow_shelf[OVERFLOW]
                shelf[ORDERS].append(order.to_json())
                self.overflow_shelf[OVERFLOW][ORDERS] = shelf[ORDERS]
            else:
                shelf = self.shelves[order_type]
                shelf[ORDERS].append(order.to_json())
                self.shelves[order_type][ORDERS] = shelf[ORDERS]
        else:
            shelf = self.overflow_shelf[OVERFLOW]
            shelf[ORDERS].append(order.to_json())
            self.overflow_shelf[OVERFLOW][ORDERS] = shelf[ORDERS]



    def _get_least_valued_item_from_shelf(self, shelf_type):
        least_valued = {}

        for idx, item_thing in enumerate(self.shelves[shelf_type][ORDERS]):

            item = FoodOrder(**item_thing)

            if not least_valued or \
                    least_valued['value'] > item.current_value():
                least_valued['type'] = shelf_type
                least_valued['value'] = item.current_value()
                least_valued['index'] = idx
        for idx, item_thing in enumerate(self.overflow_shelf[OVERFLOW][ORDERS]):

            item = FoodOrder(**item_thing)

            if not least_valued or \
                    least_valued['value'] > \
                    item.current_value(is_overflow=True):
                least_valued['type'] = OVERFLOW
                least_valued['value'] = item.current_value()
                least_valued['index'] = idx
        return least_valued

    def _remove_decayed_order(self, order_type):
        # TODO: remove the least-valued item in the order_type / overflow shelf
        # find least-valued item in order_type and overflow, remove it
        least_valued_item = self._get_least_valued_item_from_shelf(order_type)

        print('removing this order:: ', least_valued_item)

        if least_valued_item['type'] == OVERFLOW:
            waste_item = self.overflow_shelf[OVERFLOW][ORDERS]\
                .pop(least_valued_item['index'])
        else:
            waste_item = self.shelves[least_valued_item['type']][ORDERS]\
                .pop(least_valued_item['index'])

        self.waste_bucket.append(waste_item)

        return least_valued_item['type']


_food_holder = FoodHolder(_shelves)
