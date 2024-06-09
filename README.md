# Home Assistant TransportNSW integration

This one differs from the version in Home Assistant repo because it uses PyTransportNSWv2 that supports the new Trips API.

It supports showing `n` future trips on the route as specified in the configuration.

Follow [the official documentation steps](https://www.home-assistant.io/integrations/transport_nsw/) to get stop IDs and API key.


## Example Configuration

```
transportnsw:
  api_key: "YOUR API KEY"
  routes:
    - name: "Marrickville to Central"
      stop_id: "220410"
      destination_stop_id: "200060"
      num_trips: 3
    - name: "Marrickville to Town Hall"
      stop_id: "220410"
      destination_stop_id: "200070"
      num_trips: 3
```
