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

# System Design

The following is a diagram of the proxy
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
2. Reads the access rules that contains information about the rate of delivery for every ip/path pair
3. If there isn't a rule concerning this request it only increments the counter
4. If there is a rule concerning this request and the client has exceeding the request rate, it sends a deny rule to the cache master server (Redis) that in turn will propagate it to all of its replicas allocated inside each request worker, causing the desired throttling of requests. Along with the rule, sets an expiration time with it.

The nature of this processing is OLTP and the data access patterns are known in advance, so it makes sense to use a NoSQL database (Mongo DB in this implementation)

Finnally, this subsystem has an application web server that implements the necessary REST endpoint to manage the access rules.

The access rule
Consist of a throttling rule for a given ip/path pair

```json
{}
```
