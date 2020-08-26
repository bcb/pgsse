# PostgresEvents

Listens for Postgres NOTIFY notifications, broadcasting them as Server-Sent Events.

## Usage

Bring up the Docker image, serving events on port 4000:
```sh
docker run --rm -e POSTGRES_DB='postgresql://user:pass@localhost:5432/db' --port 4000:3000 liveteams/postgresevents
```

Send a notification in Postgres:
```psql
psql -U user -d db -c "select pg_notify('channel', json_build_array('event', 'data')::text)"
```

Listen to SSE events with an HTTP GET request:
```sh
curl http://localhost:4000
event: event
data: data
id: 0


```
