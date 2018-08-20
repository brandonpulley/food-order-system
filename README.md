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

## Tests
To run unit tests run the following command
```
docker-compose run web pytest
```