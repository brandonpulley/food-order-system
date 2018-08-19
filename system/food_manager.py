import sys
import threading
from time import sleep
from system.food_order import FoodOrder

HOT_MAX_COUNT = 15
COLD_MAX_COUNT = 15
FROZEN_MAX_COUNT = 15
OVERFLOW_MAX_COUNT = 20

VALUE = 'value'
TYPE = 'type'
INDEX = 'index'
MAX = 'max'
ORDERS = 'orders'
OVERFLOW = 'overflow'
TEMP_HOT = 'hot'
TEMP_COLD = 'cold'
TEMP_FROZEN = 'frozen'

FOOD_ORDER_TIME_DIFF = 0.25

_shelves = {
    TEMP_HOT: {
        ORDERS: [],
        MAX: HOT_MAX_COUNT
    },
    TEMP_COLD: {
        ORDERS: [],
        MAX: COLD_MAX_COUNT
    },
    TEMP_FROZEN: {
        ORDERS: [],
        MAX: FROZEN_MAX_COUNT
    }
}


def add_orders(orders_json_array: []):
    for order_dict in orders_json_array:
        sleep(FOOD_ORDER_TIME_DIFF)
        _add_order(order_dict)

        sys.stdout.flush()
    return {'shelves': _food_holder.shelves,
            'waste_bucket': _food_holder.waste_bucket}


def _add_order(order: dict):

    food_order = FoodOrder(**order)
    _food_holder.add_food_order(food_order)
    print('adding order:: ', food_order.to_json())


class FoodHolder:

    # locks for multithreading
    add_lock = threading.Lock()
    get_lock = threading.Lock()
    # default overflow shelf
    _overflow_shelf = {
        OVERFLOW: {
                ORDERS: [],
                MAX: OVERFLOW_MAX_COUNT
            }
    }

    def __init__(self, shelves):
        self.shelves = shelves
        self.waste_bucket = []
        self.shelves[OVERFLOW] = self._overflow_shelf[OVERFLOW]

    def add_food_order(self, food_order: FoodOrder):
        self.add_lock.acquire()
        try:
            self._add_food_order(food_order)
        finally:
            self.add_lock.release()

    def _remove_zero_value_orders(self):
        for key, shelf in self.shelves.items():
            for idx, item in enumerate(shelf[ORDERS]):
                food_item = FoodOrder(**item)
                if food_item.current_value() <= 0:
                    shelf[ORDERS].pop(idx)



    def _add_food_order(self, food_order):
        self._remove_zero_value_orders()

        shelf_type = food_order.temp

        if shelf_type not in self.shelves:
            # TODO: Error!!
            pass
        else:
            shelf = self.shelves[shelf_type]
            if len(shelf[ORDERS]) >= shelf[MAX]:
                self._add_order_to_overflow(food_order)
            else:
                shelf[ORDERS].append(food_order.to_json())
                self.shelves[shelf_type] = shelf

    def _add_order_to_overflow(self, order):

        order_type = order.temp

        if len(self.shelves[OVERFLOW][ORDERS]) >= \
                self.shelves[OVERFLOW][MAX]:
            add_shelf_type = self._remove_decayed_order(order_type)
        else:
            add_shelf_type = OVERFLOW

        shelf = self.shelves[add_shelf_type]
        shelf[ORDERS].append(order.to_json())
        self.shelves[order_type][ORDERS] = shelf[ORDERS]

    def _find_least_valued_item(self, shelf_type):
        """
        Finds the order with the least value from either the given shelf type
        or from the overflow shelf, whichever contains the least-valued item
        :param shelf_type: the shelf type to include in the search
        :return: the item with the least value
        """

        least_valued = {}

        for idx, item in enumerate(self.shelves[shelf_type][ORDERS]):

            food_item = FoodOrder(**item)

            if not least_valued or \
                    least_valued[VALUE] > food_item.current_value():
                least_valued[TYPE] = shelf_type
                least_valued[VALUE] = food_item.current_value()
                least_valued[INDEX] = idx
        for idx, item in enumerate(self.shelves[OVERFLOW][ORDERS]):

            food_item = FoodOrder(**item)

            if not least_valued or \
                    least_valued[VALUE] > \
                    food_item.current_value(is_overflow=True):
                least_valued[TYPE] = OVERFLOW
                least_valued[VALUE] = food_item.current_value()
                least_valued[INDEX] = idx
        return least_valued

    def _remove_decayed_order(self, order_type):
        least_valued_item = self._find_least_valued_item(order_type)

        print('removing this item:: ', least_valued_item)

        waste_item = self.shelves[least_valued_item[TYPE]][ORDERS]\
            .pop(least_valued_item[INDEX])

        self.waste_bucket.append(waste_item)

        return least_valued_item[TYPE]


_food_holder = FoodHolder(_shelves)
