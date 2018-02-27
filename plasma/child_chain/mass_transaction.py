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

    @property
    def hash(self):
        return utils.sha3(rlp.encode(self, self.unsigned))

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

    # The owner of the inputs says it's okay to exit
    # Just use txindex for now as a convenience
    def confirm_sig1(self, txindex, private):
        etx = self.transaction_set[txindex]
        etx.confirm_sig1 = self.confirm_sig(etx, private)

    def confirm_sig2(self, txindex, private):
        etx = self.transaction_set[txindex]
        etx.confirm_sig2 = self.confirm_sig(etx, private)

    def confirm_sig(self, etx, private):
        if not self.finished:
            # The mass transaction needs to be in a state where we are not accepting
            # any more transactions.
            raise RuntimeError

        # At this point we don't really know if this confirmation is legit,
        # meaning that it is the owner of the input, but we will send it
        # to the contract, which will validate this.
        # Also note that the tx hash is unsigned
        # The mass transaction root hash will include the signatures.
        return plasma_utils.confirm_tx(etx.tx, self.hash, private)

    def sign(self):
        self.sig = plasma_utils.sign(self.hash, self.authority.private_key)

    def finalize(self):
        self.finished = True
