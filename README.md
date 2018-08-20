## Dependencies

[Docker](https://www.docker.com/get-docker)

[docker-compose](https://docs.docker.com/compose/install/)

## Start the server

First build your image locally
```
$ docker-compose build
```

Then run your container
```
$ docker-compose up
```

## Query

### input
When running locally you can POST to /query endpoint of localhost on port 8080
```
http://localhost:8080/query
```
body
```
{
  "orders": [
      {
        "name": "Banana Split",
        "temp": "frozen",
        "shelfLife": 20,
        "decayRate": 0.63
      },
      {
        "name": "McFlury",
        "temp": "frozen",
        "shelfLife": 375,
        "decayRate": 0.4
      }
  ]
}
```

### output

After the calculations have been done for the provided input, the response
will contain how the items left the shelf. These are grouped into 3 different
groups: delivered items, overflow waste, and no-value items
```
{
    "delivered_items": [ ... ],
    "overflow_waste": [ ... ],
    "no_value_items" [ ... ]
}
```

The progress of the calculations are also present in the standard output.

This output is sent to the docker container that is running this application.

It will tell you when an order is added, when the order is removed because it
has no value, when the order is removed because of too much food overflow, and
when an item is delivered.

Each statement will also display the order that has been added or removed

When an order has been either added or delivered the contents of all of the
shelves are printed out as well


## Related Reading

Check out the [algorithm README](README_algo.md) for information on how the
items are discarded when the shelves are at capacity
