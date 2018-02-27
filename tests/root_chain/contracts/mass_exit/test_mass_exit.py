import pytest

import rlp

from plasma.child_chain.account import Account
from plasma.child_chain.mass_transaction import MassTransaction
from plasma.child_chain.root_node import RootNode


@pytest.fixture
def mass_exit(t, get_contract):
    contract = get_contract('RootChain/MassExit.sol')
    t.chain.mine()
    return contract


def test_mass_exit(t, mass_exit):
    logs = []

    # Used for debugging contracts
    t.chain.head_state.log_listeners.append(
        lambda f: logs.append(mass_exit.translator.listen(f)))

    # all accounts
    users = {
        t.a1: Account(t.a1, t.k1),
        t.a2: Account(t.a2, t.k2),
        t.a3: Account(t.a3, t.k3),
        t.a4: Account(t.a4, t.k4),
        t.a5: Account(t.a5, t.k5),
        t.a6: Account(t.a6, t.k6),
        t.a7: Account(t.a7, t.k7), # Mass Exiter
    }

    root_node = RootNode(
        Account(t.a0, t.k0),
        mass_exit,
    )

    depositors = [
        Account(t.a1, t.k1),
        Account(t.a2, t.k2),
        Account(t.a3, t.k3),
    ]

    utxos = []

    # initial accounts deposit
    for depositor in depositors:
        utxos.append(root_node.deposit(depositor.address, 200))

    recipients = [
        Account(t.a4, t.k4),
        Account(t.a5, t.k5),
        Account(t.a6, t.k6),
    ]

    # first round of sending tx to others
    # simulates gossip
    for i in range(len(recipients)):
        root_node.send(utxos[i], depositors[i], recipients[i], 100)

    # Seems like a security thing to ensure that enough time has passed
    # in the ethereum chain
    t.chain.head_state.block_number += 7

    # record these tx's in the plasma contract
    # This would be done by the authority in real life.
    root_node.submit_plasma_block()

    # Attempt mass exit now.

    mt = MassTransaction(Account(t.a7, t.k7))

    # Simulate utxo owners attempting to exit.
    for utxo in root_node.utxos:
        owner = users.get(utxo.owner)
        mt.add_transaction(utxo, owner.private_key)

    # Before we confirm all tx's
    mt.finalize()

    # Simulate input owners confirming exits
    for i in range(len(mt.transaction_set)):
        etx = mt.transaction_set[i]

        # Only look at first input for now.
        prev_tx = root_node.blockchain.get_tx(
            etx.tx.blknum1,
            etx.tx.txindex1,
        )

        # get prev owner.
        if etx.tx.oindex1 == 0:
            sender = prev_tx.newowner1
        elif etx.tx.oindex1 == 1:
            sender = prev_tx.newowner2
        else:
            raise RuntimeError

        account = users.get(sender)

        mt.confirm_sig1(i, account.private_key)

    mt.sign()

    # Now that everything is signed attempt the exit on the plasma contract
    mass_exit.startMassExit(rlp.encode(mt, mt.unsigned), mt.sig)

    # import pdb
    # pdb.set_trace()
