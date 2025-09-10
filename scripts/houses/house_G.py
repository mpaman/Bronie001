import random
import time
import os
from dotenv import load_dotenv
from brownie import accounts, network, Contract
from eth_account import Account

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

ADDRESS = os.getenv("G_ADDRESS")
PRIVATE_KEY = os.getenv("G_PK")
TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")
MARKET_ADDRESS = os.getenv("MARKET_ADDRESS")

from brownie.project import load

load(".", raise_if_loaded=False)
from brownie import Palm, EnergyMarket

print("Address from PRIVATE_KEY:", Account.from_key(PRIVATE_KEY).address)
print("G_ADDRESS from .env:", ADDRESS)


def report_energy(address, private_key, generated, consumed):
    acct = accounts.add(private_key)
    market = Contract.from_abi("EnergyMarket", MARKET_ADDRESS, EnergyMarket.abi)
    tx = market.reportEnergy(generated, consumed, {"from": acct})
    print(f"reportEnergy: {tx.txid}")


def pay_energy(address, private_key, kwh):
    acct = accounts.add(private_key)
    market = Contract.from_abi("EnergyMarket", MARKET_ADDRESS, EnergyMarket.abi)
    tx = market.payEnergy(address, kwh, 1, {"from": acct})
    print(f"payEnergy: {tx.txid}")


def reset_energy(address, private_key):
    acct = accounts.add(private_key)
    market = Contract.from_abi("EnergyMarket", MARKET_ADDRESS, EnergyMarket.abi)
    tx = market.resetEnergy({"from": acct})
    print(f"resetEnergy: {tx.txid}")


ROLE = 0  # BUY_ONLY

import random
import time
import os
from dotenv import load_dotenv
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import report_energy, pay_energy, reset_energy

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

ADDRESS = os.getenv("G_ADDRESS")
PRIVATE_KEY = os.getenv("G_PK")
ROLE = "BUY_ONLY"


def main():
    try:
        while True:
            gen = 0
            con = random.randint(10, 50)
            net = gen - con

            print(f"\n🏠 House G (BUY_ONLY) → ผลิต {gen}, ใช้ {con} = Net {net} kWh")
            report_energy(ADDRESS, PRIVATE_KEY, gen, con)

            if net < 0:
                pay_energy(ADDRESS, PRIVATE_KEY, abs(net))

            time.sleep(300)

    except KeyboardInterrupt:
        print("🚪 ออกจากโปรแกรมแล้ว → resetEnergy()")
        reset_energy(ADDRESS, PRIVATE_KEY)
