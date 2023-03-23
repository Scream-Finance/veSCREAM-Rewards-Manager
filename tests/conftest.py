import pytest
from brownie import Contract, interface, chain, accounts


# Function scoped isolation fixture to enable xdist.
# Snapshots the chain before each test and reverts after test completion.
@pytest.fixture(scope="function", autouse=True)
def shared_setup(fn_isolation):
    pass


# scream v2 multisig
@pytest.fixture(scope="session")
def gov():
    yield accounts.at("0x63A03871141D88cB5417f18DD5b782F9C2118b5B", force=True)


@pytest.fixture(scope="session")
def management():
    yield accounts.at("0xC6387E937Bcef8De3334f80EDC623275d42457ff", force=True)


@pytest.fixture
def user():
    yield accounts[0]


@pytest.fixture
def scream():
    scream = interface.IERC20("0xe0654C8e6fd4D733349ac7E09f6f23DA256bF475")
    yield scream


@pytest.fixture
def rewards_manager(management, RewardsManager, gov):
    # deploy
    rewards_manager = management.deploy(RewardsManager)
    yield rewards_manager
