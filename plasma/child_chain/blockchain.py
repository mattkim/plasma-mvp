

class Blockchain:

    def __init__(self):
        # The first block is none
        self.blockchain = [None]

    @property
    def current_block(self):
        return len(self.blockchain)

    def add(self, block):
        self.blockchain.append(block)

    def get(self, blocknum):
        return self.blockchain[blocknum]

    def get_tx(self, blocknum, txindex):
        return self.blockchain[blocknum].transaction_set[txindex]
