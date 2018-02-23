import pytest


@pytest.fixture
def mass_exit(t, get_contract):
    contract = get_contract('RootChain/MassExit.sol')
    t.chain.mine()
    return contract


def test_mass_exit(t, mass_exit, assert_tx_failed):
    print(mass_exit)
