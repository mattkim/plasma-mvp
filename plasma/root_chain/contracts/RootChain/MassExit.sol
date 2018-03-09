pragma solidity 0.4.18;

import 'RootChain.sol';
import 'RLP.sol';
import 'Validate.sol';
import './ByteUtils.sol';


contract MassExit is RootChain {
    using SafeMath for uint256;
    using RLP for bytes;
    using RLP for RLP.RLPItem;
    using RLP for RLP.Iterator;
    using Merkle for bytes32;

    event LogBytes(bytes item);
    event LogBytes32(bytes32 item);
    event LogAddress(address addr);

    function MassExit() public {}

    function startMassExit(bytes massExitBytes, bytes32 rootHash, bytes sig) public {
        var massExit = massExitBytes.toRLPItem().toList();

        require(massExit.length == 1);

        // Validate transactions
        var txList = massExit[0].toList();

        for (var j = 0; j < txList.length; j++) {
            var exitTx = txList[j].toList();
            var tx = exitTx[0].toBytes();
            var sig1 = exitTx[1].toData();
            var sig2 = exitTx[2].toData();
            var confirm_sig1 = exitTx[6].toData();

            var txHash = keccak256(tx);

            var combinedSigs = ByteUtils.concat(ByteUtils.concat(sig1, sig2), confirm_sig1);

            require(Validate.checkSigsWithConfSig1(txHash, rootHash, combinedSigs));
        }
    }
}
