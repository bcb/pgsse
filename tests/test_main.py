from postgrestosse.main import sse


def test_sse():
    sse({"data": "foo"}) == "data: foo\nid: 1\n\n"
    sse({"event": "foo", "data": "bar"}) == "event: foo\ndata: bar\nid: 2\n\n"
    sse("This is a comment") == "This is a comment\nid: 3\n\n"
