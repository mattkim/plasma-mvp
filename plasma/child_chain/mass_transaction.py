import rlp

from rlp.sedes import binary, CountableList
from .exit_transaction import ExitTransaction
from ethereum import utils
from plasma.utils import utils as plasma_utils


class MassTransaction(rlp.Serializable):

    fields = [
        ('transaction_set', CountableList(ExitTransaction)),
        ('sig', binary),
    ]

    def __init__(self, authority):
        self.transaction_set = []
        self.transaction_indexes = {}
        self.authority = authority
        self.sig = b'\x00'
        self.finished = False

    @property
    def unsigned(self):
        return MassTransaction.exclude([
            'sig',
        ])

    @classmethod
    def hashable_sedes(cls):
        """Create a new sedes considering only fields for hashing."""
        class SerializableExcluded(cls):
            fields = [
                ('transaction_set', CountableList(
                    ExitTransaction.exclude([
                        'confirm_sig1',
                        'confirm_sig2',
                    ]))),
            ]

        return SerializableExcluded

    @property
    def hash(self):
        return utils.sha3(rlp.encode(self, MassTransaction.hashable_sedes()))

    # The owner of the utxo wants to exit,
    # The owner of the utxo theorhetically already
    # received the signed inputs on the side chain.
    def add_transaction(self, utxo, private):
        tx = utxo.tx
        pub = utils.privtoaddr(private)

        # Verify that owner of the utxo is requesting an exit.
        if utxo.owner != pub:
            raise RuntimeError

        etx = ExitTransaction(
            tx.blknum1, tx.txindex1, tx.oindex1,
            tx.blknum2, tx.txindex2, tx.oindex2,
            tx.newowner1, tx.amount1,
            tx.newowner2, tx.amount2,
            tx.fee,
            # We can't really validate here because we don't have a ref to the plasma chain
            tx.sig1,
            tx.sig2,
            exit_blknum=utxo.blocknum,
            exit_txindex=utxo.txindex,
            exit_oindex=utxo.oindex,
        )

        self.transaction_indexes[etx.tx.hash] = len(self.transaction_set)
        self.transaction_set.append(etx)

    def sign(self):
        self.sig = plasma_utils.sign(self.hash, self.authority.private_key)

    def finalize(self):
        self.finished = True
