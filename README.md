# postgrestosse

Relay Postgres notifications as Server-Sent Events.

## Usage

Bring up the Docker image.
```sh
docker run --rm -e POSTGRES_URI='postgresql://user:pass@localhost:5432/db' --port 8000:8000 liveteams/postgrestosse
```

Send a Postgres notification - the payload should be a JSON object with a
"data" key.
```sql
pg_notify('my-channel', '{"data": 1}')
```

For named events, include an "event" key.
```sql
pg_notify('my-channel', '{"event": "my-event", "data": 1}')
```

You can also use `json_build_array`.
```sql
pg_notify('my-channel', json_build_array('event', 'my-event', 'data', 1)::text)
```

For a comment, simply pass a string.
```sql
pg_notify('my-channel', 'This is a comment')
```

Listen to the event stream with an HTTP GET request.
```sh
$ curl http://localhost:8000/my-channel
event: my-event
data: 1
id: 1


```

## Development
```sh
POSTGRES_URI="postgresql://user:pass@localhost:5432/db" uvicorn postgrestosse.main:app --reload
```
