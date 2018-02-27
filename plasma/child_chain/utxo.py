

class UTXO:

    def __init__(self, tx, blocknum, txindex, oindex):
        self.tx = tx
        self.blocknum = blocknum
        self.txindex = txindex
        self.oindex = oindex

    @property
    def value(self):
        if self.oindex == 0:
            return self.tx.amount1
        elif self.oindex == 1:
            return self.tx.amount2

        raise RuntimeError

    @property
    def owner(self):
        if self.oindex == 0:
            return self.tx.newowner1
        elif self.oindex == 1:
            return self.tx.newowner2

        raise RuntimeError

    def __hash__(self):
        # Expects an integer to be returned
        return hash(
            self.tx.hash +
            bytes(self.blocknum) +
            bytes(self.txindex) +
            bytes(self.oindex)
        )

    def __eq__(self, other):
        return (
            self.tx.hash == other.tx.hash and
            self.blocknum == other.blocknum and
            self.txindex == other.txindex and
            self.oindex == other.oindex
        )
