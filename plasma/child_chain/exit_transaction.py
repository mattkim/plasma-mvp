import rlp
from rlp.sedes import big_endian_int, binary
from .transaction import Transaction


# Adds extra metadata on top of transactions for convenience
class ExitTransaction(rlp.Serializable):

    fields = [
        ('tx', Transaction),
        ('sig1', binary),
        ('sig2', binary),
        ('exit_blknum', big_endian_int),
        ('exit_txindex', big_endian_int),
        ('exit_oindex', big_endian_int),
        ('confirm_sig1', binary),
        ('confirm_sig2', binary),
        # TODO: we need to add proofs here to prove that transaction exits
    ]

    def __init__(
        self, blknum1, txindex1, oindex1,
        blknum2, txindex2, oindex2,
        newowner1, amount1,
        newowner2, amount2,
        fee,
        sig1=b'\x00' * 65,
        sig2=b'\x00' * 65,
        exit_blknum=0,
        exit_txindex=0,
        exit_oindex=0,
        confirm_sig1=b'\x00' * 65,
        confirm_sig2=b'\x00' * 65,
    ):
        self.tx = Transaction(
            blknum1, txindex1, oindex1,
            blknum2, txindex2, oindex2,
            newowner1, amount1,
            newowner2, amount2,
            fee,
            sig1,
            sig2
        )

        # It's duplicated but it will be useful later when doing sig validation.
        self.sig1 = sig1
        self.sig2 = sig2

        self.confirm_sig1 = confirm_sig1
        self.confirm_sig2 = confirm_sig2
        self.exit_blknum = exit_blknum
        self.exit_txindex = exit_txindex
        self.exit_oindex = exit_oindex

    @property
    def unsigned(self):
        return UnsignedTransaction


UnsignedTransaction = ExitTransaction.exclude([
    'sig1',
    'sig2',
    'exit_blknum',
    'exit_txindex',
    'exit_oindex',
    'confirm_sig1',
    'confirm_sig2',
])
