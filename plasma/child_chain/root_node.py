import rlp

from plasma.child_chain.utxo import UTXO

from .transaction import Transaction, UnsignedTransaction
from .block import Block
from .blockchain import Blockchain


class RootNode:

    def __init__(self, authority, plasma_contract):
        self.utxos = set()
        self.pending_utxos = []
        self.blockchain = Blockchain()
        self.authority = authority # creator of the plasma contract
        self.plasma_contract = plasma_contract

    def deposit(self, owner, value):
        null_address = b'\x00' * 20
        tx = Transaction(0, 0, 0, 0, 0, 0,
                        owner, value, null_address, 0, 0)

        # Add this deposit as a block on our local chain
        self.blockchain.add(Block([tx]))

        # Add deposit to plasma contract
        tx_bytes = rlp.encode(tx, UnsignedTransaction)
        self.plasma_contract.deposit(tx_bytes, value=value)

        # Note this block_id must be mirrored on the plasma chain and local chain
        block_id = self.plasma_contract.currentChildBlock() - 1
        utxo = UTXO(tx, block_id, 0, 0)

        self.utxos.add(utxo)
        return utxo

    def send(self, prev_utxo, sender, recipient, amount):
        remainder = prev_utxo.value - amount

        if prev_utxo not in self.utxos:
            raise RuntimeError

        # Note this won't work if the utxo isn't already in the current set
        tx = Transaction(
            prev_utxo.blocknum, prev_utxo.txindex, prev_utxo.oindex,
            0, 0, 0,
            recipient.address, amount,
            sender.address, remainder,
            0,
        )

        # Sender will sign this right away.
        tx.sign1(sender.private_key)

        # These utxos don't exist inside the plasma chain yet.
        self.pending_utxos.append(UTXO(tx, None, None, 0))
        self.pending_utxos.append(UTXO(tx, None, None, 1))

    def submit_plasma_block(self):
        tx_indexes = {} # reverse lookup tx id by hash.
        block_txs = []
        txindex = 0

        for i in range(len(self.pending_utxos)):
            pending_utxo = self.pending_utxos[i]
            pending_utxo.blocknum = self.blockchain.current_block
            pending_tx = pending_utxo.tx

            if tx_indexes.get(pending_tx.hash):
                pending_utxo.txindex = tx_indexes.get(pending_tx.hash)
            else:
                pending_utxo.txindex = txindex

                tx_indexes[pending_tx.hash] = txindex
                block_txs.append(pending_tx) # this needs to be in sync with txindex

                txindex += 1

        # Add block to chains
        block = Block(block_txs)
        self.blockchain.add(block)
        # must use merkilized hash, for fraud proofs during exits
        self.plasma_contract.submitBlock(
            block.merkilize_transaction_set,
            sender=self.authority.private_key,
        )

        # Update the current utxo set.
        prev_utxos = set()

        for pending_utxo in self.pending_utxos:
            prev_utxos.add(self._get_prev_utxo(pending_utxo))

        # Remove if it exists.
        for prev_utxo in prev_utxos:
            if prev_utxo in self.utxos:
                self.utxos.remove(prev_utxo)
            else:
                raise RuntimeError

        # Add pending utxos to utxo set.
        self.utxos.update(self.pending_utxos)
        self.pending_utxos = []

    def _get_prev_utxo(self, utxo):
        # Get input's tx
        prev_tx = self.blockchain.get_tx(
            utxo.tx.blknum1,
            utxo.tx.txindex1,
        )

        prev_utxo = UTXO(
            prev_tx,
            utxo.tx.blknum1,
            utxo.tx.txindex1,
            utxo.tx.oindex1,
        )

        return prev_utxo
