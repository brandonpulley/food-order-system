import sys
import threading
from datetime import datetime, timedelta
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

FOOD_ORDER_TIME_DELAY = 0.25

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

_threads = []


def add_orders(orders_json_array: []):

    dispatch_thread = threading.Thread(target=_dispatch_drivers)
    _threads.append(dispatch_thread)
    dispatch_thread.start()

    for order_dict in orders_json_array:

        sleep(FOOD_ORDER_TIME_DELAY)

        order_thread = threading.Thread(target=_add_order, args=(order_dict, ))
        _threads.append(order_thread)
        order_thread.start()

        sys.stdout.flush()

    # TODO: While loop to clean up running threads. print for now
    for thread in _threads:
        print('thread thingy::: ', str(thread))

    while _food_holder.has_food():
        print('still need to deliver some food.... just waiting here')

    return {'shelves': _food_holder.shelves,
            'waste_bucket': _food_holder.waste_bucket,
            'delivered': _food_holder.delivered_bucket}


def _add_order(order: dict):

    food_order = FoodOrder(**order)
    _food_holder.add_food_order(food_order)
    print('adding order:: ', food_order.to_json())


def _deliver_order():
    print('this is where a driver would normally be dispatched...')
    # remove the least-valued item from the stack
    _food_holder.remove_least_valued_order(is_delivery=True)


def _dispatch_drivers():
    # TODO: make sure this starts after orders have already started coming in
    # AND Thread each dispatch
    food_check_expiration = datetime.now() + timedelta(seconds=3)
    while datetime.now() < food_check_expiration:

        sleep(float(1.0)/float(3.0))

        driver_thread = threading.Thread(target=_deliver_order)
        _threads.append(driver_thread)
        driver_thread.start()

        if _food_holder.has_food():
            food_check_expiration = datetime.now() + timedelta(seconds=1)


class FoodHolder:

    # locks for multithreading
    _add_lock = threading.Lock()
    _get_lock = threading.Lock()
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
        self.delivered_bucket = []
        self.shelves[OVERFLOW] = self._overflow_shelf[OVERFLOW]

    def add_food_order(self, food_order: FoodOrder):
        self._add_lock.acquire()
        try:
            self._add_food_order(food_order)
        finally:
            self._add_lock.release()

    def has_food(self):
        for key in self.shelves:
            shelf = self.shelves[key]
            if len(shelf[ORDERS]) > 0:
                return True
        return False

    def remove_least_valued_order(self, shelf_types: [] = None,
                                  is_delivery=False):
        least_valued_item = self._find_least_valued_item(shelf_types)

        if is_delivery:
            self.delivered_bucket.append(
                self.shelves[least_valued_item[TYPE]][ORDERS]
                    .pop(least_valued_item[INDEX])
            )
        else:
            self.waste_bucket.append(
                self.shelves[least_valued_item[TYPE]][ORDERS]
                    .pop(least_valued_item[INDEX])
            )

        return least_valued_item[TYPE]

    def _remove_zero_value_orders(self):
        for key, shelf in self.shelves.items():
            for idx, item in enumerate(shelf[ORDERS]):
                food_item = FoodOrder(**item)
                if food_item.current_value() <= 0:
                    self.waste_bucket.append(
                        shelf[ORDERS].pop(idx))

    def _add_food_order(self, food_order):
        self._remove_zero_value_orders()

        shelf_type = food_order.temp

        if shelf_type not in self.shelves:
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
            add_shelf_type = self.remove_least_valued_order([order_type,
                                                             OVERFLOW])
        else:
            add_shelf_type = OVERFLOW

        shelf = self.shelves[add_shelf_type]
        shelf[ORDERS].append(order.to_json())
        self.shelves[order_type][ORDERS] = shelf[ORDERS]

    def _find_least_valued_item(self, shelf_types: [] = None):
        """
        Finds the order with the least value from either the given shelf type
        or from the overflow shelf, whichever contains the least-valued item
        :param shelf_type: the shelf type to include in the search
        :return: the item with the least value
        """

        if not shelf_types:
            shelf_types = [key for key in self.shelves.keys()]

        least_valued = {}
        for shelf_type in shelf_types:
            for idx, item in enumerate(self.shelves[shelf_type][ORDERS]):

                food_item = FoodOrder(**item)

                if not least_valued or \
                        least_valued[VALUE] > food_item.current_value():
                    least_valued[TYPE] = shelf_type
                    least_valued[VALUE] = food_item.current_value()
                    least_valued[INDEX] = idx
        return least_valued


_food_holder = FoodHolder(_shelves)
