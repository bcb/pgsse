from postgrestosse.main import sse


def test_sse():
    sse({"data": "foo"}) == "data: foo\n\n"
    sse({"event": "foo", "data": "bar"}) == "event: foo\ndata: bar\n\n"
    sse("This is a comment") == "This is a comment\n\n"
