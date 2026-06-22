from graph.provider import GraphDataProvider
from tests.conftest import StubGraphDataProvider


def test_stub_satisfies_protocol():
    stub = StubGraphDataProvider()
    assert isinstance(stub, GraphDataProvider)
