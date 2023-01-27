# 🐙 hydralisk.py
Hydralisk - scale and fund millions of EVM-chain wallets via CLI

![Hydralisk](https://github.com/paulpierre/hydralisk/blob/main/github/cli.png?raw=true)

# 🔍 Overview
Ever wanted to spin up a million wallets on Ethereum or Polygon? Or maybe you want to schedule a transaction to be sent out every 5 minutes for a year? Or maybe you want an army of wallets to trigger a smart contract function with a single command? Hydralisk is a CLI wrapper around [eth-cli](https://github.com/protofire/eth-cli) that accomplishes that and more.

Simply configure a file with the target # of wallets you want, contract address, ABI, method, params , and Hydralisk will create the wallets, fund them via master wallet, and execute the transaction. You can also configure the duration and wallet limit to spread the transactions out over a period of time. Give it a try on Goerli testnet!

# 😎 Features
- 🗂️ Campaign management - Segregate all wallts via prefix, each campaign gets 1 master wallet to fund
- 🧠 Smart execution - Wallet balances are checked, funded and spreads transactions out over a duration all in parallel
- 📝 Smart contracts - Trigger smart contract functions which custom inputs and macros like random numbers and UUIDs. Supply custom ABIs or automatically download them via block explorer
- ⛽ Gas management - Set seperate gas limits and prices at a campaign level and a separate gas price for funding children wallets
- 🗃️ Wallet management - View all wallets and export their private keys for separate use
- 🧩 - Customize settings seperately via JSON

# 🤔 Use cases
- Smart contract testing - Load test your smart contract on testnet with method input macros.
- Speed mint NFTs - Generate all your wallets. Import them into [Puppeteer + Metamask](https://github.com/decentraland/dappeteer), get them whitelisted. Then unleash the kraken on mint day.
- Gas trolling - If you can afford it
- 🙌 This was built for a very specific use-case while still attempting to be generic. If you have a use-case that you think would be useful, please open an issue and let me know!

# 💻 Installing
Getting started is simple, first create an environment
```
python3 -m venv venv
```
Then activate it
```
source venv/bin/activate
```
Next install the required dependencies:
```
pip3 install -r requirements.txt
```
Then create a .env file in the same directory by copying `.env-example` and renaming it as `.env`
```
cp .env-example .env
```

Next you will need to add the `eth-cli` package via npm. Make sure you have [node installed](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm). 

To install `eth-cli` run:
```
python3 hydralisk.py init
```

This will install the required dependencies. `eth-cli` will be installed globally, so you will need to have `npm` installed. If you don't have `npm` installed, you can install it via [Homebrew](https://brew.sh/) on MacOS or [Chocolatey](https://chocolatey.org/) on Windows.


# ⚙️ Setup
You will first need to setup a configuration file that contains the details of the transaction you wish to execute. Go ahead edit or copy the `example.json` file. It will contain the following contents:

```
{
    "chain": "mumbai",
    "duration": 3600,
    "wallet_limit": 600,
    "prefix": "spore",
    "confirmation_blocks": 3,
    "abi_name": "tower",
    "contract_address": "0x9C0dCFb08d63011c047C32F92B8Cb40baa969b1b",
    "method": "dailyLog(\"{uuid}\")",
    "gas": 73109,
    "gas_price": 1500000000,
    "data": "🍄"
}
```
* `chain` - The slug from `eth-cli` for the chain you want to use. For example `mumbai` for Polygon Mumbai testnet. To view all available chains run `eth network`.
* `duration` - Integer representing the number of seconds you would like to spread the transactions out over. For example, if you set this to 3600 and `wallet_limit` to 600, then each wallet will be funded and have a transaction sent out every 6 minutes.
* `wallet_limit` - Integer representing the number of wallets you would like to create. For example, if you set this to 600, then 600 wallets will be created and funded when you run hydralisk.
* `prefix` - String representing the prefix you would like to use for the wallets. For example, if you set this to `hydralisk`, then the wallets will be named `hydralisk_0x0b4a_4299` etc. The suffix is the wallet address concatented
* `confirmation_blocks` - Integer representing the number of blocks you would like to wait for a transaction to be confirmed. For example, if you set this to 3, then the wallet will wait for 3 blocks to be mined before moving on to the next transaction.
* `abi_name` - This is the `eth-cli` name of the ABI. To see a list of available ABIs run `eth abi:list` if you have it locally, you can run `eth abi:add erc777 ./path/to/erc777.json` to add it. `erc777` is the name of the ABI.
* `contract_address` - The address of the smart contract you would like to interact with.
* `method` - this is the smart contract method you wish to call. It must be in `functionName("string", int)` format. Quotes should be escaped with `\"`. Macros can only be used with string inputs. Only two macros are supported:
  * `{uuid}` - generates a random UUID string
  * `{rnd}` - generates a random number between 0 and 10000
* `gas` - the gas limit to use for the smart contract transaction
* `gas` - price to use for the smart contract transaction
* `data` - any data you would like to add to the transactions "data" field.

# 🌲 Environment Vars
Make sure you copy the `.env-example` file and rename it to `.env`. Here is an example of the contents:

```
ETHERSCAN_API_KEY=
POLYGONSCAN_API_KEY=
BSCSCAN_API_KEY=
BLOCK_CONFIRMATIONS=5

ETHEREUM_RPC_URL=https://rpc.ankr.com/eth
POLYGON_RPC_URL=https://rpc-mainnet.maticvigil.com
BSC_RPC_URL=https://rpc.ankr.com/bsc
MUMBAI_RPC_URL=https://rpc-mumbai.maticvigil.com
GOERLI_RPC_URL=https://goerli-light.eth.linkpool.io/
BSC_TESTNET_RPC_URL=https://testnet.bscscan.com

GAS_DEPLOYMENT_LIMIT=25000
GAS_DEPLOYMENT_PRICE=5000000000

DEBUG=1
```

This file contains the following variables:

### 🌎 Global configuration
`BLOCK_CONFIRMATIONS` - The number of blocks to wait for a transaction to be confirmed. This is the same as `confirmation_blocks` in the config file and overrides it.
`GAS_DEPLOYMENT_LIMIT` - The gas limit to use for the master wallet when deploying gas to fund the children wallets
`GAS_DEPLOYMENT_PRICE` - The gas price to use for the master wallet when deploying gas to fund the children wallets
`DEBUG` - Enable viewing debug messages in the CLI

### 🔑 Block explorer API keys
This is optional, but useful because if you do not know the ABI of the contract you wish to interact with, Hydralisk will automatically download it for you. You can get an API key from the following block explorers:

* `ETHERSCAN_API_KEY` - Your Etherscan API key. This is used to automatically download ABIs from Etherscan. You can get one [here](https://etherscan.io/register)
* `POLYGONSCAN_API_KEY` - Your Polygonscan API key. This is used to automatically download ABIs from Polygonscan. You can get one [here](https://polygonscan.com/register)
* `BSCSCAN_API_KEY` - Your Bscscan API key. This is used to automatically download ABIs from Bscscan. You can get one [here](https://bscscan.com/register)
* `BLOCK_CONFIRMATIONS` - The number of blocks to wait for a transaction to be confirmed. This is the same as `confirmation_blocks` in the config file and overrides it.

### 🌐 RPC nodes
You will need to provide the RPC URLs for the chains you wish to use and submit transactions to.

* `ETHEREUM_RPC_URL` - The RPC URL for Ethereum mainnet
* `POLYGON_RPC_URL` - The RPC URL for Polygon mainnet
* `BSC_RPC_URL` - The RPC URL for Binance Smart Chain mainnet
* `MUMBAI_RPC_URL` - The RPC URL for Polygon Mumbai testnet
* `GOERLI_RPC_URL` - The RPC URL for Goerli testnet
* `BSC_TESTNET_RPC_URL` - The RPC URL for Binance Smart Chain testnet

# 🏁 Getting started
Once you have your campaign setup, you can run the following command to start the campaign:
```
python3 hydralisk.py -f ./<your config file>.json
```

You can additionally manually include the configuration via CLI flags. To see all available flags, run `python3 hydralisk.py --help`
![Hydralisk](https://github.com/paulpierre/hydralisk/blob/main/github/help.png?raw=true)


# ⭐ How it works

This is what it looks like when you execute Hydralisk

![Hydralisk](https://github.com/paulpierre/hydralisk/blob/main/github/execution.png?raw=true)


1. Hydralisk generates a master wallet if it doesn't exist
2. The coin balance is checked based on the required gas and count of wallets
3. Children wallets are generated if they don't exist
4. Wallets are scheduled to run at a specific time based on the `duration` and `wallet_limit` parameters via Asyncio
5. When a wallet is ready to run `execute_contract_call()` will check the current wallets gas
6. Hydralisk will check `./log` to see if the wallet has already executed the contract call, if it has it skips
7. If funds are insufficient, the master wallet will fund it based on the config
8. The wallet will execute the contract's method replacing macros with the appropriate values
9. The wallet will wait for the transaction to be confirmed per configuration
10. Success or failure is logged to `./log` directory containing the wallet address and transaction hash

# 🤔 Troubleshooting

### Insufficient gas
Sometimes you may get an error that says `Transaction has been reverted by the EVM`. Each call to a smart contract costs gas. If you do not have enough gas, the transaction will fail. Chances are you need to increase your gas limit. Check similar contract transactions in the block explorer to understand the type of cost you will incur executing a contract method.

![Hydralisk](https://github.com/paulpierre/hydralisk/blob/main/github/bad_gas.png?raw=true)

You can [learn more about gas here](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm).

### Insufficient funds

You may also run into an error that states `Error: Returned error: insufficient funds for gas * price + value`

![Hydralisk](https://github.com/paulpierre/hydralisk/blob/main/github/bad_funds.png?raw=true)

It could either mean:

1. You did not configure the gas limit and price in the `.json` configuration file resulting in the master wallet not sending enough gas to the child wallet to execute the contract method

2. You might be specifying a below-market rate for gas price and so the miners will not include your transaction in the block. You can [learn more about gas market prices here](https://ethgasstation.info/).


### Successful contract execution

For reference, this is what a successful contract execution looks like:

![Hydralisk](https://github.com/paulpierre/hydralisk/blob/main/github/success.png?raw=true)


https://ethereum.org/en/developers/docs/gas/


# 🛣️ Roadmap
🚨 This was built as a proof-of-concept and is not intended for production 🚨. Open an issue or submit a PR if you have ideas.

I will port `eth-cli` to Golang and create python bindings. The eventual goal is to create a performant framework for executing complex transactions with a focus on scale and shareability.

The general vision is to treat python as the glue code and port the core functionality to Golang, creating bindings. This will allow for a more robust and performant CLI. In no particular order, a backlog of features to add:

# 📝 Backlog

### Feature backlog
- [ ] Enhance retries for failed txs based on the error
- [ ] Gas oracle integration for all chains
- [ ] Fund sweeping command for projects
- [ ] Add support for parallel cross-chain execution
- [ ] Add support for detecting proxy contracts and fetch destination contract ABI
- [ ] Enhanced logging
- [ ] Master wallet fund obfuscation for privacy

### Infra backlog
- [ ] Dockerize and integrate w/ Hashicorp Vault
- [ ] Refactor Asyncio to use external task queue for distributed execution (Rabbit MQ?)
- [ ] Add Kubernetes support (or Nomad?)
- [ ] Local Postgres DB for state management / logging / reporting

### Core backlog
- [ ] Remove dependency on `eth-cli` and port to Golang (or find lib that likely exists)
- [ ] Add golang bindings
- [ ] API support via FastAPI
- [ ] Add support for container-based wallet scripts w/ bi-directional communication (Red Panda? Redis?)
  - [ ] Add example scripts: [front-run](https://consensys.net/diligence/blog/2019/02/taxonomy-of-front-running-attacks-on-blockchain/), mint
- [ ] Add support for event-based triggers via containers (contract events, webhook, etc.)
  - [ ] Address monitor: ERC20, ERC721, ERC1155 transfer, mint, swap
  - [ ] Mem pool monitor
  - [ ] Webhook trigger
  - [ ] Asset price monitor (Coinparika)


## 🚗 Open Source License
----
Copyright (c) 2023 Paul Pierre
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in allcopies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.