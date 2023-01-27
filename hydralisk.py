from typing import Any, List, Dict, Optional
from rich.console import Console
from datetime import datetime
import requests
import asyncio
import random
import typer
import uuid
import json
import os
from util import (
    mkdir,
    display_table,
    get_chain_by_name,
    run_async,
    is_valid_address
)
from config import (
    logger,
    CHAIN,
    BLOCK_CONFIRMATIONS,
    GAS_DEPLOYMENT_LIMIT,
    GAS_DEPLOYMENT_PRICE
)

chain_slug = CHAIN.SLUG

console = Console()

app = typer.Typer(
    rich_markup_mode='rich'
)

# =====================
# APPLICATION FUNCTIONS
# =====================

"""
---------------------------
Wrapper function to eth CLI
---------------------------
:param cmd: the command line args to pass to eth
:param stdout: the console to print to
:param json_response: whether to return the result as a json object
"""
async def call_eth(
    cmd: str = None,
    stdout: Any = None,
    json_response: bool = True
):

    # -------------------
    # Validate parameters
    # -------------------
    if not cmd:
        raise ValueError('Missing required parameter cmd')

    global console

    if stdout:
        console = stdout

    # Add prefix for eth cli and appened --json option if relevant
    cmd = f'eth {cmd} --json' if json_response else f'eth {cmd}'
    logger.debug(f'📡 {cmd}')

    result, stderr = await run_cmd(cmd)

    # Lets clean the output
    result = result.decode('utf-8').replace('\n', '').replace('\r', '')

    # If there is an error, print it and exit
    if stderr and 'Error' in stderr.decode('utf-8'):
        logger.error(f'Received error: {stderr.decode("utf-8")}')
        return False

    # If the result is a json object, parse it
    return json.loads(result) if json_response else result


"""
--------------------------
Run a command line command
--------------------------
"""
async def run_cmd(cmd: str = None):
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # -------------------------------------------------
    # Execute the command and capture stdout and stderr
    # -------------------------------------------------
    # lets wait until the process completes
    await process.wait()
    stdout, stderr = await process.communicate()
    return stdout, stderr


"""
-----------------------------------------
Retrieve ETH balance of a wallet by chain
-----------------------------------------
:param wallet_address: the wallet address to check
:param chain: the chain to check
"""
async def get_balance(
    wallet_address: str = None,
    chain: CHAIN = None
):
    if not chain or not wallet_address:
        raise ValueError('Missing required parameters wallet_address and chain')

    result = await call_eth(f'address:balance -n {chain.SLUG} {wallet_address}', json_response=False)
    logger.debug(f'📡 get_balance: {wallet_address} = {result}')
    return float(result) if result else 0


"""
-----------------------------------------
Retrieve all stored wallets in the system
-----------------------------------------
:param prefix: the prefix to filter by
:param suffix: the suffix to filter by
:param name: the name to filter by
"""
async def get_wallets(
    prefix: str = None,
    suffix: str = None,
    name: str = None
):

    wallets = list()

    # Lets fetch all the wallets available
    result = await call_eth('address:list')

    # Lets iterate through all the wallets so we can filter if needed
    for k, wallet in result.items():
        wallet_address = wallet['*']['address']
        wallet_name = k

        # Skip unnamed wallets
        if not wallet_name:
            continue

        # Filter by exact wallet name match
        if name and wallet_name != name:
            continue

        # Filter name by prefix
        if prefix and not wallet_name.startswith(prefix):
            continue

        # Filter name by suffix
        if suffix and not wallet_name.endswith(suffix):
            continue

        wallets.append({
            'name': k,
            'address': wallet_address,
            'pk': wallet['*']['privateKey']
        })

    return wallets


"""
-------------------------------------
Retrieve a master wallet with balance
-------------------------------------
:param chain: the chain to check
:param prefix: the prefix to filter by
:param name: the name of the wallet
"""
async def get_master_wallet(
    name: str = 'master',
    prefix: str = None,
    chain: CHAIN = None,
):
    # -------------------
    # Validate parameters
    # -------------------
    if not chain:
        raise ValueError('Missing required parameter chain')

    # Set the prefix if one is set. By default all master wallets end with _master
    name = f'{prefix}_{name}' if prefix else name

    # Fetch the wallet by name
    result = await call_eth(f'address:show {name}', json_response=False)

    if not result:
        raise ValueError(f'Could not find wallet "{name}"')

    result = json.loads(result)

    return {
        'name': name,
        'chain': chain.SLUG,
        'symbol': chain.SYMBOL,
        'address': result['*']['address'],
        'pk': result['*']['privateKey'],
        'balance': await get_balance(wallet_address=result['*']['address'], chain=chain),
    }


"""
--------------------------------------------
Retrieve all the master wallets and balances
--------------------------------------------
"""
async def get_master_wallets(chain: CHAIN = None):

    if not chain:
        raise ValueError('Missing required parameter chain')

    # Lets get all wallets with names ending in _master
    wallets = await get_wallets(suffix='_master')

    if not wallets:
        logger.error('No master wallets found.')
        return None

    master_wallets = list()

    for w in wallets:
        result = await get_master_wallet(name=w['name'], chain=chain)
        if result:
            master_wallets.append(result)

    return master_wallets

"""
-----------------------------------------
Generate and store a wallet in the system
-----------------------------------------
:param name: the name of the wallet if you aren't creating serialized wallets
:param prefix: the prefix of wallet for creating n > 1 wallets (serialized)
:param num_wallets: the number of wallets you wish to create
:param target_num: if set instead of num_wallets, this will create wallets until the target number is reached
"""
async def create_wallet(
    name: str = None,
    prefix: str = None,
    num_wallets: int = 1,
    target_num: int = None
):
    # -------------------
    # Validate parameters
    # -------------------
    if not name and not prefix or (name and not name.endswith('_master') and prefix):
        raise ValueError('Name or prefix is required. You must define only one.')

    # If they are specifying a name, we should only create 1 wallet
    if name and num_wallets != 1 or (name and target_num):
        raise ValueError('You can only create 1 wallet when specifying a name. Only use "num_wallets" param and not "target_num".')

    # Lets get all existing wallets
    wallets = await get_wallets(
        prefix=prefix
    )

    wallets_count = len(wallets)

    # -------------------------------
    # Check if we're at target amount
    # -------------------------------
    if target_num and wallets_count >= target_num:
        logger.info(f'Found {wallets_count} wallets. No need to generate more.')
        return wallets

    # ----------------------------------------------------
    # Generate wallets from current count up to target_num
    # ----------------------------------------------------
    if target_num and wallets_count < target_num:

        # Lets get the delta
        num_wallets = target_num - wallets_count

        logger.info(f'Found {wallets_count} wallets. Generating {num_wallets} more...')

    logger.info(f'Generating {num_wallets} wallets...')

    # -------------------------
    # Lets generate the wallets
    # -------------------------
    # This command allows us to generate multiple wallets with one call
    result = await call_eth(f'address:random {num_wallets}', json_response=False)

    # Catch any errors
    if not result:
        logger.error(f'Could not generate wallets: {result}')
        return None

    # Clean up response because it is not json-friendly
    result = f"[{result.replace('}', '},')[:-1]}]"
    wallets = json.loads(result)

    # ----------------------------------------------
    # Store generated wallets in the system w/ names
    # ----------------------------------------------
    for i, wallet in enumerate(wallets, 1):
        wallet_address = wallet["address"]
        wallet_pk = wallet["privateKey"]

        # If we are generating a single wallet, use the name
        wallet_name = f'{prefix}_{wallet_address[:6].lower()}_{wallet_address[-4:].lower()}' if not name else name

        # Create the wallet
        result = await call_eth(f'address:add {wallet_name} {wallet_pk}', json_response=False)

        if result:
            logger.info(f'🤖 Added {i}/{num_wallets}: "{wallet_name}"')
        else:
            logger.error(f'Could not add wallet: {result}')

    # Lets get the wallets from the system just to be sure they were created
    return await get_wallets(name=name) if name else await get_wallets(prefix=prefix)


"""
-----------------------------------------
Get all the available blockchain networks
-----------------------------------------
"""
async def get_networks():
    return await call_eth('network:list')


"""
-------------------------------------------
Get wallets that already finished execution
-------------------------------------------
"""
async def get_finished_wallets(
    execution_config: str = None
):
    if not execution_config:
        raise ValueError('Missing required parameter execution_config')

    log_path = execution_config['log_path']
    campaign_name = execution_config['campaign_name']
    log_file = f'{log_path}{campaign_name}-{datetime.now().strftime("%Y-%m-%d")}.log'

    # check if file exists
    if not os.path.isfile(log_file):
        logger.error(f'Log file does not exist: {log_file}')
        return []

    # open log file and read it
    with open(log_file, 'r') as f:
        log = f.read()

    wallets = list()
    for row in log.split('\n'):
        if ',' in row:
            wallets.append(row.split(',')[1])

    return wallets


"""
-------------
Add a network
-------------
"""
async def add_network(
    chain: CHAIN = None
):
    if not chain:
        raise ValueError('Missing required parameter chain')

    # Add the network
    result = await call_eth(f'network:add {chain.SLUG} --url {chain.RPC_URL} --id {chain.CHAIN_ID} --label {chain.SLUG}', json_response=False)

    if not result:
        logger.error(f'Could not add network: {result}')
        return None

    return result


"""
----------------------------------------
Add the ABI for a contract to the system
----------------------------------------
:param contract_address: the address of the contract
:param name: the name of the contract, optional
:param chain: the chain the contract is on
"""
async def add_abi(
    contract_address: str = None,
    name: str = None,
    chain: CHAIN = None
):
    # -------------------
    # Validate parameters
    # -------------------
    if not all([contract_address, chain]):
        raise ValueError(f"Valid address and chain is required {address}")

    # -----------------------------------------------
    # Check local cache in ./abi if it exists already
    # -----------------------------------------------
    abi_file = f'./abi/{contract_address}.json'
    src_file = f'./src/{contract_address}.sol'

    # If it does not exist, fetch it from the relevant block explorer
    if not os.path.exists(abi_file):

        # -----------------------------
        # Fetch ABI from block explorer
        # -----------------------------
        url = f"{chain.API_URL}module=contract&action=getsourcecode&address={contract_address}"
        res = requests.get(url)

        if res.status_code != 200 or res.json()["status"] != "1":
            logger.error(f"Error fetching contract data {res.text}")
            return None

        # -----------------------------
        # Store the ABI and source code
        # -----------------------------
        source_code = res.json()["result"][0]["SourceCode"]
        abi = res.json()["result"][0]["ABI"]

        if abi == 'Contract source code not verified':
            logger.error(f"🚨 Contract not found or is not verified in the block explorer")
            return None

        contract_name = res.json()["result"][0]["ContractName"] if not name else name

        # ---------------------------
        # Save to local disk as cache
        # ---------------------------

        # Create the directories if they don't exist
        mkdir('./abi/')
        mkdir('./src/')

        # write abi to file
        with open(abi_file, "w") as f:
            f.write(abi)

        # write source code to file
        with open(src_file, "w") as f:
            f.write(source_code)
    else:
        if not name:
            raise ValueError(f"ABI name is required")

        contract_name = name
        logger.error(f'🚨 ABI already exists {abi_file}')

    # -------------------------
    # Add the ABI to the system
    # -------------------------
    await call_eth(f"abi:add {contract_name} {abi_file}", json_response=False)
    logger.info(f"Saved ABI and contract source {contract_name} to the system")

    return True


"""
------------------------------
Get the list of available ABIs
------------------------------
"""
async def get_abi_list():
    result = await call_eth('abi:list', json_response=False)
    return result.split('\n') if result else None


"""
------------------------------------------------
Send native coin from wallet_pk to target_wallet
------------------------------------------------
:param wallet_pk: the private key of the wallet to send the coin from, normally the master wallet
:param target_wallet: the wallet address to send the coin to
:param amount: the amount of coin to send in wei
:param data: the data to send with the transaction, optional
:param chain: the chain to send the coin on
"""
async def send_coin(
    wallet_pk: str = None,
    target_wallet: str = None,
    amount: int = None,
    data: Optional[str] = None,
    chain: CHAIN = None
):
    # -------------------
    # Validate parameters
    # -------------------
    if not all([wallet_pk, target_wallet, amount, chain]):
        raise ValueError("Missing required values for wallet_pk, target_wallet, amount, chain")

    # -------------------
    # Setup CLI arguments
    # -------------------

    chain_arg = f'-n {chain.SLUG}' if chain else ''
    confirmation_blocks_arg = f'--confirmation-blocks={BLOCK_CONFIRMATIONS}'
    data_arg = f'--data="{data}"' if data else ''

    # -----------------------
    # Execute the transaction
    # -----------------------
    logger.debug(f'⛽ Sending {amount} wei to {target_wallet} from {wallet_pk} @ {chain.SLUG}')

    result = await call_eth(f"tx:send {chain_arg} --gas={GAS_DEPLOYMENT_LIMIT} --gasPrice={GAS_DEPLOYMENT_PRICE} --pk={wallet_pk} --to={target_wallet} --value={amount} {confirmation_blocks_arg} {data_arg}", json_response=False)

    if result:
        logger.info(f'⛽ Gas deployed to {target_wallet} ({amount} wei) @ tx: {result}')
        return result
    else:
        logger.error(f'❌⛽ Failed to deploy gas to {target_wallet} ({amount} wei): {result}')
        return False

"""
------------------------------------------------
Core wallet task that executes a contract method
------------------------------------------------
:param wallet: dictionary containing information about the wallet from get_wallet()
:param execution_config: dictionary containing information about the execution
"""
async def execute_contract_call(
    wallet: dict = None,
    execution_config: dict = None
):
    # -------------------
    # Validate parameters
    # -------------------
    if not all([wallet, execution_config]):
        raise ValueError("Wallet and execution config are required")

    # -----------------------------------------------------
    # Get the wallet and execution configuration parameters
    # -----------------------------------------------------

    # Wallet specific parameters
    wallet_address = wallet['address'] if 'address' in wallet else None
    wallet_name = wallet['name'] if 'name' in wallet else None
    wallet_pk = wallet['pk'] if 'pk' in wallet else None

    # Execution specific parameters
    campaign_name = execution_config['campaign_name'] if 'campaign_name' in execution_config else None
    chain = execution_config["chain"] if "chain" in execution_config else None
    gas = execution_config["gas"] if "gas" in execution_config else None
    gas_price = execution_config["gas_price"] if "gas_price" in execution_config else None
    master_pk = execution_config['master_pk'] if 'master_pk' in execution_config else None

    # Contract specific parameters
    abi_name = execution_config['abi_name'] if 'abi_name' in execution_config else None
    contract_address = execution_config['contract_address'] if 'contract_address' in execution_config else None
    method = execution_config['method'] if 'method' in execution_config else None

    # --------------------
    # Execution validation
    # --------------------
    if not all([wallet_pk, wallet_address, abi_name, contract_address, method, gas, gas_price]):
        raise ValueError(f"Missing required values for contract call {wallet_pk, wallet_address, abi_name, contract_address, method}")

    # ---------------------------------------
    # Make sure this is not the master wallet
    # ---------------------------------------
    if wallet_name == 'master' or wallet_name.endswith('_master'):
        logger.error("🚨 Master wallet can't be used for execution, skipping..")
        return

    # -------------------
    # Setup CLI arguments
    # -------------------
    gas_arg = f'--gas={execution_config["gas"]}' if 'gas' in execution_config else ''
    gas_price_arg = f'--gasPrice={execution_config["gas_price"]}' if 'gas_price' in execution_config else ''
    chain_arg = f'-n {execution_config["chain"].SLUG}' if 'chain' in execution_config and execution_config['chain'] else ''
    confirmation_blocks_arg = f'--confirmation-blocks={execution_config["confirmation_blocks"]}' if 'confirmation_blocks' in execution_config else f'--confirmation-blocks={BLOCK_CONFIRMATIONS}'

    # -----------------------------------------------------
    # Check if the executing wallet has a suffcient balance
    # -----------------------------------------------------
    transaction_cost = gas * gas_price
    wallet_balance = await get_balance(wallet_address=wallet_address, chain=chain)

    # --------------------------------------------------
    # Fund the wallet with master wallet if insufficient
    # --------------------------------------------------
    if wallet_balance < gas * gas_price:
        logger.info(f'Wallet "{wallet_name}" has insufficient balance of {wallet_balance}. {transaction_cost} wei is required, sending funds..')

        tx_data = f"0x{'🍄💵'.encode('utf-8').hex()}"
        tx_hash = await send_coin(
            wallet_pk=master_pk,
            target_wallet=wallet_address,
            amount=transaction_cost,
            data=tx_data,
            chain=chain
        )
        if not tx_hash:
            logger.error(f"❌ Failed to fund {wallet_name}")
            return False
        logger.info(f"💸 {wallet_name} funded w/ {transaction_cost} wei ({transaction_cost / 10 ** 18:.8f} {chain.SYMBOL}) @ tx {tx_hash}")

    # ---------------------------------
    # Swap any dynamic macros if needed
    # ---------------------------------
    if '{uuid}' in method:
        _uuid = str(uuid.uuid4())
        method = method.replace('{uuid}', _uuid)

    if '{rnd}' in method:
        method = method.replace('{rnd}', str(random.randint(0, 10000)))

    # ----------------------------
    # Call the contract method now
    # ----------------------------
    tx_hash = await call_eth(f"contract:send {chain_arg} --pk={wallet_pk} {confirmation_blocks_arg} {gas_arg} {gas_price_arg} {abi_name}@{contract_address} '{method}'", json_response=False)

    if not tx_hash:
        logger.error(f"❌ Failed to call {abi_name} contract method")
        return False

    # get timestamp
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ----------------------------
    # Write the transaction to log
    # ----------------------------
    log_path = execution_config['log_path']
    log_file = f'{log_path}{campaign_name}-{datetime.now().strftime("%Y-%m-%d")}.log'

    with open(f'{log_file}', "a") as f:
        f.write(f",{wallet_address},{tx_hash},{ts}\n")

    logger.info(f"✅ Successful call to {abi_name} contract sent: {tx_hash}")


"""
-----------------------------------------------------------
Distribute the calls to execute_contract_call() in parallel
-----------------------------------------------------------
:param wallets: list of dictionaries containing information about the wallets from get_wallets()
:param execution_config: dictionary containing information about the execution
:param time_period: the time period in seconds to evenly distribute the calls over
"""
async def distribute_calls(
    wallets: List[dict] = None,
    execution_config: dict = None,
    time_period: int = None
):
    # -------------------
    # Validate parameters
    # -------------------
    if not all([wallets, execution_config, time_period]):
        raise ValueError(f"Missing required values for contract call wallets, execution_config, time_period")

    # --------------------------------------------------
    # Calculate the delay between each command execution
    # --------------------------------------------------
    delay = time_period / len(wallets)

    # --------------
    # Queue of tasks
    # --------------
    tasks = list()

    # -----------------------------------------------
    # Create the task queue for each wallet execution
    # -----------------------------------------------
    for wallet in wallets:

        tasks.append(asyncio.create_task(execute_contract_call(wallet=wallet, execution_config=execution_config)))

        # ---------------
        # Execution delay
        # ---------------
        await asyncio.sleep(delay)

    # -----------------------------------------------
    # Use asyncio.gather to run the tasks in parallel
    # -----------------------------------------------
    await asyncio.gather(*tasks)


"""
-----------------------------------
Start the execution of the campaign
-----------------------------------
:param execution_config: dictionary containing information about the execution
"""
async def init_hydralisk(
    execution_config: dict = None
):
    # -------------------
    # Validate parameters
    # -------------------
    if not execution_config:
        raise ValueError("Missing required execution_config")

    prefix = execution_config['prefix'] if 'prefix' in execution_config else None
    chain = execution_config['chain'] if 'chain' in execution_config else None
    wallet_limit = execution_config['wallet_limit'] if 'wallet_limit' in execution_config else None
    master_wallet_name = f'{prefix}_master' if prefix else None
    abi_name = execution_config['abi_name'] if 'abi_name' in execution_config else None
    contract_address = execution_config['contract_address'] if 'contract_address' in execution_config else None
    contract_method = execution_config['method'] if 'method' in execution_config else None
    gas = execution_config['gas'] if 'gas' in execution_config else None
    gas_price = execution_config['gas_price'] if 'gas_price' in execution_config else None
    time_period = execution_config['duration'] if 'duration' in execution_config else None

    if not all([chain, master_wallet_name, prefix, abi_name, contract_address, contract_method, gas, gas_price, time_period]):
        raise ValueError(f"Missing required values for execution_config: chain, time_period, master_wallet_name, prefix, abi_name, contract_address, contract_method, gas, gas_price")

    # ----------------------------------------------
    # Lets filter execution wallets vs master wallet
    # ----------------------------------------------
    execution_wallets = list()
    master_wallet = None
    wallets = await get_wallets(prefix=prefix)

    # -------------------------------------------
    # Lets get wallets that have executed already
    # -------------------------------------------
    executed_wallets = await get_finished_wallets(execution_config=execution_config)

    # Lets filter out the master wallet
    for w in wallets:
        if w['name'] == master_wallet_name:
            master_wallet = w
        elif w['address'] in executed_wallets:
            console.print(f'[red]Wallet {w["name"]} has already executed. Skipping...[/red]')
            continue
        else:
            execution_wallets.append(w)

    # --------------------------
    # Validate the master wallet
    # --------------------------
    if not master_wallet:
        logger.error(f"Missing master wallet: {master_wallet_name}. Creating it for you")
        master_wallet = await create_wallet(name=master_wallet_name, prefix=prefix)
        master_wallet_address = master_wallet[0]['address']
        execution_cost_wei = int(wallet_limit) * int(gas) * int(gas_price)
        execution_cost_eth = execution_cost_wei / 10 ** chain.DECIMALS
        logger.error(f"Master wallet {master_wallet_name} - {master_wallet_address}.\n💸 Please fund it with {execution_cost_eth} {chain.SYMBOL} or {execution_cost_wei} wei.")
        return False

    # ----------------------------------------------
    # Make sure master wallet has sufficient balance
    # ----------------------------------------------
    # Some of the wallets may have a balance so we can't
    # assume they are empty, lets at least check the master
    # wallet for a balance

    master_wallet_address = master_wallet['address']

    # Set the master wallet private key for execution
    execution_config['master_pk'] = master_wallet['pk']

    master_wallet_balance = await get_balance(wallet_address=master_wallet_address, chain=chain)
    if not master_wallet_balance:
        logger.error(f'Master wallet: "{master_wallet_name}" has a balance of 0. Please fund is at: {master_wallet_address} on "{chain.NAME}"')
        return False

    # ------------------------------
    # Validate the execution wallets
    # ------------------------------
    if not execution_wallets or len(execution_wallets) < int(wallet_limit):

        # The number of wallets to create to sufficiently cover the wallet limit target
        wallet_create_count = int(wallet_limit) - len(execution_wallets) if execution_wallets else 1

        logger.error(f"Missing execution wallets w/ prefix: {prefix}. Automatically creating {wallet_create_count} wallet(s)")

        # ----------------------------
        # Create the execution wallets
        # ----------------------------
        result = await create_wallet(prefix=prefix, target_num=int(wallet_limit))

        if not result:
            logger.error(f"Failed to create wallets for prefix {prefix}")
            return False

        logger.info(f'✅ Successfully created {len(result)} wallets for prefix {prefix}')

        # ----------------------------------------------
        # Merge new wallets with existing wallets if any
        # ----------------------------------------------
        execution_wallets.extend(result)

    # Lets randomize the wallets
    random.shuffle(execution_wallets)

    # --------------------------------
    # Lets limit the number of wallets
    # --------------------------------
    execution_wallets = execution_wallets[:wallet_limit] if wallet_limit else wallets

    # Total number of wallets to execute the contract call on over the time period
    execution_wallets_num = len(execution_wallets)

    # ------------------
    # Determine duration
    # ------------------

    logger.info(f'🍄 Summoning {execution_wallets_num} wallets...')

    days = time_period / (60 * 60 * 24)
    hours = (time_period % (60 * 60 * 24)) / (60 * 60)
    minutes = (time_period % (60 * 60)) / 60

    duration_display = '⌛ Execution duration: '
    duration_display += f'{days:.2f} days' if days > 0 else ''
    duration_display += f', {hours:.2f} hours' if hours > 0 else ''
    duration_display += f', {minutes:.2f} minutes' if minutes > 0 else ''

    logger.info(duration_display)

    rate_seconds = execution_wallets_num / time_period
    rate_minutes = execution_wallets_num / (time_period / 60)
    rate_hours = execution_wallets_num / (time_period / (60 * 60))
    rate_days = execution_wallets_num / (time_period / (60 * 60 * 24))

    rate_display = '📈 Execution flow: '
    rate_display += f'{rate_seconds:.2f} UAW per second' if rate_seconds > 0 else ''
    rate_display += f', {rate_minutes:.2f} UAW per minute' if rate_minutes > 0 else ''
    rate_display += f', {rate_hours:.2f} UAW per hour' if rate_hours > 0 else ''
    rate_display += f', {rate_days:.2f} UAW per day' if rate_days > 0 else ''
    rate_display += f', {execution_wallets_num} UAW total'

    logger.info(rate_display)

    # ------------------------
    # Create the log directory
    # ------------------------
    if not os.path.exists('./log'):
        mkdir('./log')
        console.log('Log directory not found, creating')
        return None

    execution_config['log_path'] = mkdir(f'./log/')

    # -----------------------
    # 🚀 LFG, execution time!
    # -----------------------
    await distribute_calls(execution_wallets, execution_config, time_period)


# =============
# CLI FUNCTIONS
# =============

"""
------------------------------
Get existing wallets by prefix
------------------------------
:param prefix: Prefix for the wallet name
:return: List of wallets
"""
@app.command('wallets')
@run_async
async def display_wallets(
    ctx: typer.Context,
    prefix: str = typer.Argument(None, help='Prefix for the wallet name')
):
    """
    Display all wallets by prefix. Wallets are grouped by prefixes for tracking and segregation purposes.
    """

    if not prefix:
        ctx.get_help()
        raise typer.Exit()

    wallets = await get_wallets(prefix=prefix)

    if not wallets:
        console.print(f'No wallets found for prefix: "{prefix}"')
        raise typer.Exit()

    display_table(wallets, '🏦 Wallets')

    raise typer.Exit()


"""
-------------------------------
Add an ABI by chain and address
-------------------------------
:param contract_address: Contract address
:param chain: The chains slug name. Use "chain" command to find a list.
"""
@app.command('abi')
@run_async
async def add_abi_by_chain_and_address(
    ctx: typer.Context,
    contract_address: str = typer.Argument(None, help='Contract address'),
    chain: str = typer.Argument(None, help='The chains slug name. Use "chain" command to find a list.'),
    abi_name: str = typer.Argument(None, help='The name of the ABI you wish to provide (optional)')
):
    """
    Add an ABI by chain and address. This is required to execute a contract call.
    """

    if not all([contract_address, chain]):
        ctx.get_help()
        raise typer.Exit()
    
    if not is_valid_address(contract_address):
        console.print(f'Invalid contract address: "{contract_address}"')
        raise typer.Exit()
    
    chain = get_chain_by_name(chain)

    if not chain:
        console.print(f'Invalid chain. Please run the "chain" command to see a list of valid chains')
        raise typer.Exit()

    result = await add_abi(contract_address=contract_address, chain=chain, name=abi_name)

    if not result:
        console.print(f'Unable to add ABI for contract address: "{contract_address}"')
        raise typer.Exit()

    console.print(f'ABI added for contract address: "{contract_address}"')
    raise typer.Exit()


"""
--------------------
Setup Hydralisk CLI
--------------------
• Checks if "eth-cli" tool is installed ..
• Check if "npm" is installed, if so install "eth-cli"
• Setup our list of chains
"""
@app.command('init')
@run_async
async def setup_hydralisk(
    ctx: typer.Context
):
    """
    Setup the Hydralisk CLI
    """

    console.print('🔥 Initializing Hydralisk CLI')

    console.print('🔎 Checking to see if you have eth-cli installed...')

    # -------------------------------
    # Check if "eth-cli" is installed
    # -------------------------------
    result = await call_eth('version', json_response=False)

    if not result or 'eth-cli' not in result:
        console.print('eth-cli not found')

        # -------------------------
        # Check if NPM is installed
        # -------------------------
        console.print('checking if npm is installed')
        result = await run_cmd('npm version')

        if not result or 'npm:' not in result:
            console.print('🚨npm not found, please install and try again via "brew install node"')
            raise typer.Exit()

        # -------------------------
        # Install "eth-cli" via NPM
        # -------------------------
        result = await run_cmd('npm install -g eth-cli')

        if not result:
            console.print('🚨Failed to install eth-cli, please try again')
            raise typer.Exit()

    console.print('✅ eth-cli installed')

    # -------------------------------
    # Sync any missing chain networks
    # -------------------------------
    cli_chains = await get_networks()
    cli_set = cli_chains.keys()

    missing_chains = list()

    for chain in CHAIN:
        if chain.SLUG not in cli_set:
            missing_chains.append(chain)

    if missing_chains:
        console.print(f'Adding chains: {", ".join([c.SLUG for c in missing_chains])}')

        for chain in missing_chains:
            await add_network(chain)

    console.print('✅ Hydralisk CLI initialized')

    raise typer.Exit


"""
----------------------------------
Show the list and status of chains
----------------------------------
"""
@app.command('chain')
@run_async
async def display_chains(
    ctx: typer.Context
):
    """
    Display a list of valid chains
    """

    cli_chains = await get_networks()
    cli_set = cli_chains.keys()

    display_chains = list()

    for chain in CHAIN:
        c = chain.value
        c['is available'] = '✅' if chain.SLUG in cli_set else '-'
        display_chains.append(c)

    display_table(display_chains, header='📝 Chains')

    raise typer.Exit


"""
----------------------------
Display the list of prefixes
----------------------------
"""
@app.command('prefix')
@run_async
async def display_prefixes(
    ctx: typer.Context
):
    """
    Display all available prefixes
    """
    wallets = await get_wallets()

    if not wallets:
        console.print(f'No wallets found.')
        raise typer.Exit()

    prefixes = [{'name': o} for o in set([w['name'].split('_')[0] for w in wallets])]

    display_table(prefixes, header='📝 Prefixes')

    raise typer.Exit()


"""
----------------------------------
Display the list of master wallets
----------------------------------
:param chain: Chain to check balances on
"""
@app.command('master')
@run_async
async def display_master_wallets(
    ctx: typer.Context,
    chain: str = typer.Option(None, '--chain', '-c', help='Chain to execute on')
):
    """
    Display master wallets
    """
    if not chain:
        ctx.get_help()
        raise typer.Exit()

    chain = get_chain_by_name(chain)

    if not chain:
        console.print(f'Invalid chain. Please run the "chain" command to see a list of valid chains')
        raise typer.Exit()

    wallets = await get_master_wallets(chain=chain)
    if not wallets:
        console.print(f'No master wallets found for chain {chain.SLUG}')
        raise typer.Exit()

    display_table(wallets, '🏦 Master Wallets')
    raise typer.Exit()


"""
-------------------------------
Begins the configured execution
-------------------------------
:param chain: Chain to execute on
:param duration: Duration in seconds to execute the contract call on
:param wallet_limit: Number of wallets to execute the contract call on
:param prefix: Prefix for the wallet name
:param confirmation_blocks: Number of blocks to wait for confirmation
:param abi_name: Name of the ABI file
:param contract_address: Address of the contract to call
:param method: Method to call on the contract
:param gas: Gas to use for the contract call
:param gas_price: Gas price to use for the contract call
:param data: Data to use for the contract call
:param file: File to use for the contract call
"""
@app.command('start')
@run_async
async def start_execution(
    ctx: typer.Context,
    chain: str = typer.Option(None, '--chain', '-c', help='Chain to execute on'),
    duration: int = typer.Option(60 * 60, '--duration', '-d', help='Duration in seconds to execute the contract call on'),
    wallet_limit: int = typer.Option(600, '--limit', '-l', help='Number of wallets to execute the contract call on'),
    prefix: str = typer.Option(None, '--prefix', '-p', help='Prefix for the wallet name'),
    confirmation_blocks: int = typer.Option(BLOCK_CONFIRMATIONS, '--confirmations', '-b', help='Number of blocks to wait for confirmation'),
    abi_name: str = typer.Option(None, '--abi', help='Name of the ABI file'),
    contract_address: str = typer.Option(None, '--contract', help='Contract address'),
    method: str = typer.Option(None, '--method', help='Contract method to execute'),
    gas: int = typer.Option(None, '--gas', help='Gas to execute the contract call'),
    gas_price: int = typer.Option(None, '--gas-price', help='Gas price to execute the contract call'),
    data: str = typer.Option('🍄', '--data', help='Data to execute the contract call with'),
    file: str = typer.Option(None, '--file', '-f', help='JSON file to load execution configuration from'),
):
    """
    Start Hydralisk execution
    """


    if file:
        # check if file exists
        if not os.path.exists(file):
            console.print(f'File not found: "{file}"')
            raise typer.Exit()

        # load file
        with open(file, 'r') as f:
            execution_config = json.load(f)

        # check if all required keys are present
        if not all([k in execution_config.keys() for k in ['chain', 'duration', 'wallet_limit', 'prefix', 'confirmation_blocks', 'abi_name', 'contract_address', 'method', 'gas', 'gas_price', 'data']]):
            console.print(f'Invalid file. Please check the documentation for the correct format')
            raise typer.Exit()

        chain = execution_config['chain'] 
        duration = execution_config['duration']
        wallet_limit = execution_config['wallet_limit']
        prefix = execution_config['prefix']
        confirmation_blocks = execution_config['confirmation_blocks']
        abi_name = execution_config['abi_name']
        contract_address = execution_config['contract_address']
        method = execution_config['method']
        gas = execution_config['gas']
        gas_price = execution_config['gas_price']
        data = execution_config['data']
        campaign_name = execution_config['campaign_name']

    if not all([chain, duration, wallet_limit, prefix, confirmation_blocks, abi_name, contract_address, method, gas, gas_price, data]):
        ctx.get_help()
        raise typer.Exit()

    chain = get_chain_by_name(chain)

    if not chain:
        ctx.get_help()
        console.print(f'Invalid chain. Please use "-c <chain slug>" Valid slugs: {[c.lower() for c in CHAIN.__members__.keys()]}')
        raise typer.Exit()

    execution_config = {
        'chain': chain,
        'duration': duration,
        'wallet_limit': wallet_limit,
        'prefix': prefix,
        'confirmation_blocks': confirmation_blocks,
        'abi_name': abi_name,
        'contract_address': contract_address,
        'method': method,
        'gas': gas,
        'gas_price': gas_price,
        'data': data,
        'campaign_name': campaign_name,
        'log_path': './log/'
    }

    await init_hydralisk(execution_config)
    #asyncio.run(await init_hydralisk(execution_config))

@app.callback(invoke_without_command=True)
@run_async
async def callback(ctx: typer.Context):
    if not ctx.invoked_subcommand:
        ctx.get_help()
        raise typer.Exit()


if __name__ == '__main__':
    app()



    # execution_config = {
    #     'chain': CHAIN.MUMBAI,
    #     'duration': 60 * 60,
    #     'wallet_limit': 600,
    #     'prefix': 'spore',
    #     'confirmation_blocks': BLOCK_CONFIRMATIONS,
    #     'abi_name': 'tower',
    #     'contract_address': '0x9C0dCFb08d63011c047C32F92B8Cb40baa969b1b',
    #     'method': 'dailyLog("{uuid}")',
    #     'gas': 73109,  # This includes transaction fees and gas price * wei to run contract
    #     'gas_price': 1500000000,
    #     'data': '🍄'
    # }

    # -------------
    # Deploy spores
    # -------------
    #asyncio.run(start_execution(execution_config))

    
    # --------------------
    # Generate 600 wallets
    # --------------------
    # create_wallet(target_num=600)

    # ------------------------------------
    # Create 3 wallets with prefix "spore"
    # ------------------------------------
    # result = create_wallet('spore', 3)
    # console.print(json.dumps(get_wallets(), indent=4))

    # --------------------------------------
    # Display the list of supported networks
    # --------------------------------------
    # console.print(json.dumps(get_networks(), indent=4))

    # ---------------------------------
    # Retrieve master wallet w/ balance
    # ---------------------------------
    # w = get_master_wallet(chain=CHAIN.MUMBAI)
    # console.print(json.dumps(w, indent=4))

    # ----------------------------------------
    # Add an ABI by contract address and chain
    # ----------------------------------------
    # add_abi('0xe57dad9c809c5FF0162b17d220917089D4cC7075', chain=CHAIN.POLYGON)
    # result = get_abi_list()
    # console.print(result)