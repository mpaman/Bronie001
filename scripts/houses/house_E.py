import random
import time
import os
from dotenv import load_dotenv
from brownie import accounts, network, Contract
from eth_account import Account

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

ADDRESS = os.getenv("E_ADDRESS")
PRIVATE_KEY = os.getenv("E_PK")
TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")
MARKET_ADDRESS = os.getenv("MARKET_ADDRESS")

from brownie.project import load

load(".", raise_if_loaded=False)
from brownie import Palm, EnergyMarket

print("Address from PRIVATE_KEY:", Account.from_key(PRIVATE_KEY).address)
print("E_ADDRESS from .env:", ADDRESS)


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


ROLE = 2  # PROSUMER


def main():
    try:
        while True:
            gen = random.randint(10, 50)
            con = random.randint(10, 50)
            net = gen - con

            print(f"\n🏠 House E (PROSUMER) → ผลิต {gen}, ใช้ {con} = Net {net} kWh")
            report_energy(ADDRESS, PRIVATE_KEY, gen, con)

            if net < 0:
                pay_energy(ADDRESS, PRIVATE_KEY, abs(net))

            time.sleep(300)

    except KeyboardInterrupt:
        print("🚪 ออกจากโปรแกรมแล้ว → resetEnergy()")
        reset_energy(ADDRESS, PRIVATE_KEY)


main()
import random
import time
import os
from dotenv import load_dotenv
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import report_energy, pay_energy, reset_energy
from web3.exceptions import ContractLogicError

load_dotenv()

ADDRESS = os.getenv("E_ADDRESS")
PRIVATE_KEY = os.getenv("E_PK")
ROLE = "PROSUMER"

try:
    while True:
        gen = random.randint(0, 50)
        con = random.randint(0, 50)
        net = gen - con

        print(f"\n🏠 House E → ผลิต {gen}, ใช้ {con} = Net {net} kWh")
        report_energy(ADDRESS, PRIVATE_KEY, gen, con)

        if net < 0:
            try:
                pay_energy(ADDRESS, PRIVATE_KEY, abs(net))
            except ContractLogicError as e:
                print(f"⚠️ จ่ายเงินไม่สำเร็จ (ไม่มีผู้ขายพลังงาน) → {e}")

        time.sleep(300)

except KeyboardInterrupt:
    print("🚪 ออกจากโปรแกรมแล้ว → resetEnergy()")
    reset_energy(ADDRESS, PRIVATE_KEY)
