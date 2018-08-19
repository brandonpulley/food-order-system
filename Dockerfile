FROM python:3.6

RUN mkdir -p /srv/food_order
WORKDIR /srv/food_order

COPY . .
RUN apt-get -y update
RUN pip install -r requirements.txt
CMD ./start_server.sh
