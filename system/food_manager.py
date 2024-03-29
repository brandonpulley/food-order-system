import json
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

OVERFLOW = 'overflow'
HOT = 'hot'
COLD = 'cold'
FROZEN = 'frozen'

ORDERS = 'orders'
SHELVES = 'shelves'
WASTE_BUCKET = 'overflow_waste'
ZERO_VALUE_BUCKET = 'no_value_items'
DELIVERED = 'delivered_items'


FOOD_ORDER_INPUT_DELAY = 0.25
DISPATCH_DRIVER_DELAY = float(1.0)/float(3.0)

_shelves = {
    HOT: {
        ORDERS: [],
        MAX: HOT_MAX_COUNT
    },
    COLD: {
        ORDERS: [],
        MAX: COLD_MAX_COUNT
    },
    FROZEN: {
        ORDERS: [],
        MAX: FROZEN_MAX_COUNT
    }
}

_threads = []


def request_orders(orders_json_array: []):

    for order_dict in orders_json_array:

        sleep(FOOD_ORDER_INPUT_DELAY)

        order_thread = threading.Thread(target=_add_order, args=(order_dict, ))
        _threads.append(order_thread)
        order_thread.start()

        sys.stdout.flush()

    _dispatch_drivers()

    return {WASTE_BUCKET: _food_holder.waste_bucket,
            ZERO_VALUE_BUCKET: _food_holder.zero_value_bucket,
            DELIVERED: _food_holder.delivered_bucket}


def _add_order(order: dict):

    food_order = FoodOrder(**order)
    _food_holder.add_food_order(food_order)
    print('adding order. Current state of shelves::\n',
          json.dumps(_food_holder.shelves, sort_keys=True, indent=4))


def _deliver_order():
    # remove the least-valued item from the stack
    delivered_item, from_shelf = _food_holder.remove_highest_lowest_order(
        is_delivery=True, is_highest=False)
    print('from this shelf: ', from_shelf,
          ', this item was delivered: ', delivered_item)
    print('current state of shelves::\n',
          json.dumps(_food_holder.shelves, sort_keys=True, indent=4))


def _dispatch_drivers():
    food_check_expiration = datetime.now() + timedelta(seconds=3)
    while datetime.now() < food_check_expiration:

        sleep(DISPATCH_DRIVER_DELAY)

        driver_thread = threading.Thread(target=_deliver_order)
        _threads.append(driver_thread)
        driver_thread.start()

        if _food_holder.has_food():
            food_check_expiration = datetime.now() + timedelta(seconds=1)

        sys.stdout.flush()


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
        self.zero_value_bucket = []
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

    def remove_highest_lowest_order(self, shelf_types: [] = None,
                                    is_delivery=False, is_highest=False):
        """
        Remove the either the highest-valued item or the lowest-value item
        :param shelf_types: The shelf types to search for the items in.
        Default includes all available shelves
        :param is_delivery: False for waste, True for delivery
        :param is_highest: False for removing the lowest-priced item, True
        for removing the highest-priced item
        :return: The shelf-type of the item that was removed
        """
        self._get_lock.acquire()
        removed_item = None
        from_shelf = None
        try:
            removed_item, from_shelf = self._remove_highest_lowest_order(
                shelf_types=shelf_types,
                is_delivery=is_delivery,
                is_highest=is_highest
            )
        finally:
            self._get_lock.release()
            return removed_item, from_shelf

    def _remove_highest_lowest_order(self, shelf_types: [] = None,
                                     is_delivery=False, is_highest=False):
        self._remove_zero_value_orders()
        if is_highest:
            item_to_remove = self._find_most_valued_item(shelf_types)
        else:
            item_to_remove = self._find_least_valued_item(shelf_types)

        if is_delivery:
            self.delivered_bucket.append(
                self.shelves[item_to_remove[TYPE]][ORDERS]
                    .pop(item_to_remove[INDEX])
            )

            return self.delivered_bucket[-1], item_to_remove[TYPE]
        else:
            self.waste_bucket.append(
                self.shelves[item_to_remove[TYPE]][ORDERS]
                    .pop(item_to_remove[INDEX])
            )
            print('out of space, removing this order: ', self.waste_bucket[-1])

            return self.waste_bucket[-1], item_to_remove[TYPE]

    def _remove_zero_value_orders(self):
        for key, shelf in self.shelves.items():
            for idx, item in enumerate(shelf[ORDERS]):
                food_item = FoodOrder(**item)
                if food_item.current_value() <= 0:
                    self.zero_value_bucket.append(
                        shelf[ORDERS].pop(idx))
                    self.shelves[key] = shelf
                    print('this item has no value and is now removed: ',
                          self.zero_value_bucket[-1])

    def _add_food_order(self, food_order):
        self._remove_zero_value_orders()

        shelf_type = food_order.temp

        if shelf_type not in self.shelves:
            pass

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
            removed_item, add_shelf_type = \
                self.remove_highest_lowest_order([order_type,
                                                  OVERFLOW])
        else:
            add_shelf_type = OVERFLOW

        shelf = self.shelves[add_shelf_type]
        shelf[ORDERS].append(order.to_json())
        self.shelves[add_shelf_type][ORDERS] = shelf[ORDERS]

    def _find_least_valued_item(self, shelf_types: [] = None):
        """
        Finds the order with the most value from either the given shelf type
        or from the overflow shelf, whichever contains the least-valued item
        :param shelf_types: the shelf types to include in the search
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

    def _find_most_valued_item(self, shelf_types: [] = None):
        """
        Finds the order with the least value from either the given shelf type
        or from the overflow shelf, whichever contains the most-valued item
        :param shelf_types: the shelf types to include in the search
        :return: the item with the most value
        """

        if not shelf_types:
            shelf_types = [key for key in self.shelves.keys()]

        most_valued = {}
        for shelf_type in shelf_types:

            for idx, item in enumerate(self.shelves[shelf_type][ORDERS]):

                food_item = FoodOrder(**item)
                if not most_valued or \
                        most_valued[VALUE] < food_item.current_value():
                    most_valued[TYPE] = shelf_type
                    most_valued[VALUE] = food_item.current_value()
                    most_valued[INDEX] = idx
        return most_valued


_food_holder = FoodHolder(_shelves)
