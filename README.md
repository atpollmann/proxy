# MELI CHALLENGE

This repo implements a proxy for consumers of api.mercadolibre.com.
The requirements of the solution are:

### Highly scalable

The proxy must handle a mean of 50000 request per second

### Control

The proxy must have a way to control the amount of requests a given
combination of client ip / request path makes

### Analytics

The proxy must store analytical data about its usage

# Requirements

- Docker
- Docker compose
- Ports 8000, 8080, 8081, 27017 and 15672 free

This solution was developed and tested on a macOS 10.15.7

# System Design

![Architecture Diagram](/assets/architecture.png?raw=true)

One of the main challenges in this project is the scalability needs.
The project makes heavy use of the Event driven architectural pattern given its high scalability characteristics.

### System Components Overview

#### Request Subsystem

Its purpose is to receive and dispatch the incoming requests. Consists of an autoscaling group of workers nodes that are composed of a lightweight and fast webserver (Starlette with Uvicorn) and an in memory read only cache (Redis).

The in memory cache was chosen over a conventional database because this component must be extremely fast in order to minimize the latency.
Inside the cache, are all the ip/path pairs that must be throttled. The time complexity to determine this information is `O(1)`.

Besides checking this information, each worker dispatch the request to a message broker for later consumption.

### Broker

The broker is implemented with RabbitMQ and we use a fanout exchange to deliver each request message to two queues; control and analytics.

### Control Subsytem

Using the pub/sub pattern, each time a message arrives at the control queue, a control worker (that's inside another autoscalig group) consumes the message and takes the following steps:

1. It stores the ip, path and a counter for each request
2. Reads the [access rules](#access-rule) that contains information about the rate of delivery for every ip/path pair
3. If there isn't a rule concerning this request it only increments the counter
4. If there is a rule concerning this request and the client has exceeding the request rate, it sends a deny rule to the cache master server (Redis) that in turn will propagate it to all of its replicas allocated inside each request worker, causing the desired throttling of requests. Along with the rule, sets an expiration time with it.

The nature of this processing is OLTP and the data access patterns are known in advance, so it makes sense to use a NoSQL database (Mongo DB in this implementation)

Finnally, this subsystem has an application web server that implements the necessary REST endpoints to manage the access rules.

### Analytics Subsytem

Using the pub/sub pattern, each time a message arrives at the analytics queue, an analytics worker (that's inside another autoscalig group) consumes the message and logs the request to a database.

Since the nature of this process is OLAP and it's not very clear what the data access patterns will be, the best choice is a relational database. However, considering the amount of requests per seconds that the proxy must handle, it also makes sense to use a NoSQL database optimized for scalability once the access patterns are determined.

Finnally, this subsystem has an application web server that implements the necessary REST endpoint to read the data.

# Definitions

## Access Rules

Consist of a throttling rule for a given ip/path pair. In it, its defined an ip, a path, a rate and a unit of time (seconds or minutes). For example, the following access rule will limit the requests to 1 request per second for the ip `201.238.213.84` to the path `/categories/MLC163536`

```json
{
  "ip": "201.238.213.84",
  "path": "/categories/MLC163536",
  "rate": 1,
  "unit": "s"
}
```

# Graphical UI

There are no graphical interfaces implemented in this proxy. However, the following screens are recommended

### Live view of the traffic load

![Live View](/assets/live_view.png?raw=true)

### Logs

![Logs View](/assets/logs_view.png?raw=true)

### Logs

![Access Rules](/assets/rules_view.png?raw=true)

# How to test the proxy

Clone this repo and run `docker-compose up` from the root of the project. Once all the containers are deployed, make several requests to the local port 8000 (i.e.: `http://localhost:8000/categories/MLC4075`).

To see the logs created by the proxy, go to `http://localhost:8081/requests`

To create a throttling rule, go to `http://localhost:8080/docs` in the browser and make a post to the `/rules` route as indicated in the example, using the ip that the docker network asigned to your localhost.

To test a throttling rule you can use the test script located in the `scripts` directory as such

```text
Usage: test-proxy.sh [-p][-c]

    -p : Path to test. No leading slash. Defaults to categories/MLC1652
    -c : How many requests to make. Defaults to 10
```

# Future Improvements

Because of time constraints, a lot of assumptions were made, leaving room for the following improvements:

- Allow any content type, not only json
- Implement an authentication mechanism
- Design a better throttling algorithm
- Use a faster language
- Create formal models with a typed language
- Allow multiple verbs, not only GET
- Find a better NoSQL design, considering access patterns
- Collect more parameters from the requests
- Accept and forward all elements of a URL (query parameters and fragments)
- Handle pagination in REST endpoints
- Use of data lake formation and consumption in the analytics subsytem
