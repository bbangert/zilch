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

@contextmanager
def client_store(obj):
    import zilch.client
    prior = zilch.client.store
    zilch.client.store = obj
    try:
        yield
    finally:
        zilch.client.store = prior
