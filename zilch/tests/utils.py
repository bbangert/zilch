from contextlib import contextmanager

@contextmanager
def client_recorder(host):
    import zilch.client
    prior = zilch.client.recorder_host
    zilch.client.recorder_host = host
    try:
        yield
    finally:
        zilch.client.recorder_host = prior
