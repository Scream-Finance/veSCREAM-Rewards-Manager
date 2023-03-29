import brownie
from brownie import Contract, chain

# test all of our functions
def test_operation(gov, scream, management, user, rewards_manager, fee_distribution):
    # transfer gov to v2 MS
    rewards_manager.transferOwnership(gov, {"from": management})

    # only owner can call
    with brownie.reverts():
        rewards_manager.setAuthorized(gov, True, {"from": user})

    # give gov manager powers
    rewards_manager.setAuthorized(gov, True, {"from": gov})

    # v2 ms transfers ownership of fee distro to this contract
    fee_distribution.commit_admin(rewards_manager, {"from": gov})
    assert fee_distribution.admin() == gov.address
    fee_distribution.apply_admin({"from": gov})
    assert fee_distribution.admin() == rewards_manager.address

    # transfer tokens to our contract
    scream.transfer(rewards_manager, 11_760e18, {"from": gov})

    # only managers can call
    with brownie.reverts():
        rewards_manager.weeklyPayoutAndCheckpoint({"from": user})

    # confirm that we update our payout time
    before_time = rewards_manager.lastPayoutTime()
    before_amount = rewards_manager.lastPayoutAmount()
    rewards_manager.weeklyPayoutAndCheckpoint({"from": management})
    assert rewards_manager.lastPayoutTime() > before_time
    assert rewards_manager.lastPayoutAmount() < before_amount

    # we shouldn't be able to call it again until the next epoch
    with brownie.reverts():
        rewards_manager.weeklyPayoutAndCheckpoint({"from": management})

    # sleep for a day
    chain.sleep(86400)

    # checkpoint our new week
    rewards_manager.weeklyPayoutAndCheckpoint({"from": management})

    # get to the end
    for i in range(47):
        # sleep, queue our profits
        chain.sleep(5 * 86400)
        rewards_manager.weeklyPayoutAndCheckpoint({"from": management})
        print("\nTook profits for week", int(i + 1))
        print("Payout of:", int(rewards_manager.lastPayoutAmount() / 1e18), "SCREAM")

        # sleep, checkpoint our new week
        chain.sleep(2 * 86400)
        rewards_manager.weeklyPayoutAndCheckpoint({"from": management})
        print("Checkpoint for week", int(i + 2))

    # make sure we are at the end
    lastPayout = rewards_manager.lastPayoutAmount()
    assert lastPayout == 10e18

    # we shouldn't be able to call it again, and contract should be empty
    with brownie.reverts():
        rewards_manager.weeklyPayoutAndCheckpoint({"from": management})
    assert scream.balanceOf(rewards_manager) == 0

    # send in some more scream to test our sweep
    scream.transfer(rewards_manager, 11_760e18, {"from": gov})
    assert scream.balanceOf(rewards_manager) > 0

    # only gov can sweep
    with brownie.reverts():
        rewards_manager.sweep(scream, 11_760e18, {"from": management})

    # sweep it out
    rewards_manager.sweep(scream, 11_760e18, {"from": gov})
    assert scream.balanceOf(rewards_manager) == 0

    # make sure we can transfer ownership back
    rewards_manager.commitSafeFeeDistributionOwner({"from": gov})
    assert fee_distribution.admin() == rewards_manager.address
    rewards_manager.applyFeeDistributionOwner({"from": gov})
    assert fee_distribution.admin() == gov.address
