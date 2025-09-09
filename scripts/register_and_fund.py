import os
from brownie import EnergyMarket, Palm, accounts, Contract
from dotenv import load_dotenv

def main():
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
    acct = accounts.load('holesky_deployer')

    palm_addr = os.getenv('TOKEN_ADDRESS')
    market_addr = os.getenv('MARKET_ADDRESS')

    palm = Contract.from_abi('Palm', palm_addr, Palm.abi)
    market = Contract.from_abi('EnergyMarket', market_addr, EnergyMarket.abi)

    house_keys = [
        os.getenv('HOUSE1_KEY'),
        os.getenv('HOUSE2_KEY'),
        os.getenv('HOUSE3_KEY'),
        os.getenv('HOUSE4_KEY'),
        os.getenv('HOUSE5_KEY'),
        os.getenv('HOUSE6_KEY'),
        os.getenv('HOUSE7_KEY'),
    ]

    # สร้าง address จาก private key
    from eth_account import Account
    house_addrs = [Account.from_key(k).address for k in house_keys]
    roles = [0, 1, 2, 0, 1, 2, 2]  # BUY_ONLY, SELL_ONLY, PROSUMER, ...

    # Register houses
    for addr, role in zip(house_addrs, roles):
        if market.households(addr)[3]:  # .exists == True
            print(f"{addr} already registered, skipping.")
            continue
        tx = market.registerHousehold(addr, role, {'from': acct})
        print(f"Registered {addr} as role {role}, tx: {tx.txid}")

    # โอน Palm Token ให้แต่ละบ้าน (ตัวอย่าง 10,000 PALM)
    for addr in house_addrs:
        tx = palm.transfer(addr, 10_000 * 10**18, {'from': acct})
        print(f"Transferred 10,000 PALM to {addr}, tx: {tx.txid}")
