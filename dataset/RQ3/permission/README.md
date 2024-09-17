### Notice about Release of Permission Bugs

Our detected permission bugs could cause severe problems with smart contracts.
For responsible release, we only disclose two permission bug that has been fixed by developers in their latest contract versions.

### Case-1 (Used in paper):
Ethereum's [OwnedUpgradeabilityProxy](https://etherscan.io/address/0xa1e72267084192db7387c8cc1328fade470e4149#code) performed contract upgrade from its sixth contract version [0xb3c6fd9a58329172d043c987abfce211e9985613](https://etherscan.io/address/0xb3c6fd9a58329172d043c987abfce211e9985613#code) to the seventh version [0x27f461c698844ff51b33ecffa5dc2bd9721060b1](https://etherscan.io/address/0x27f461c698844ff51b33ecffa5dc2bd9721060b1#code).
However, a function ```['flush', ['uint256', 'uint256'], []]''' wrongly removed its access control protection, i.e., ```onlyOwnerOrManager''' in new contract version 0x27f461c6, which has been fixed by the developers in the latest contract version

### Case-2:

Polygon's [TetuStrategyUSDTProxy](https://polygonscan.com/address/0xc87a68d140dba5bef1b4fa1acdb89fd4c2547d40#code) performed contract upgrade from its seventh contract version [0xdc7cfd7cd391c6ce32aca2558684286bc8688765](https://polygonscan.com/address/0xdc7cfd7cd391c6ce32aca2558684286bc8688765#code) to the seventh version [0x9f5f8b0862cd10d4a588888b141bac296347748a](https://polygonscan.com/address/0x9f5f8b0862cd10d4a588888b141bac296347748a#code).
However, a function ```['withdraw', ['address', 'address', 'uint256'], []]''' wrongly removed its access control protection, i.e., ```onlyVault''' in new contract version 0x9f5f8b08, which has been fixed by the developers in the latest contract version


