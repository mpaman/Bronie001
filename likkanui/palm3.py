import random
import time
import os
from web3 import Web3
from dotenv import load_dotenv

# -------------------
# Blockchain Setup
# -------------------
load_dotenv()

RPC_URL = "https://ethereum-holesky-rpc.publicnode.com"
CHAIN_ID = 17000  # Holesky Testnet

web3 = Web3(Web3.HTTPProvider(RPC_URL))
if not web3.is_connected():
    raise Exception("❌ เชื่อมต่อ Holesky ไม่ได้")

TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")
MARKET_ADDRESS = os.getenv("MARKET_ADDRESS")

TOKEN_ABI = [
    {"constant": False,"inputs":[{"name":"spender","type":"address"},{"name":"value","type":"uint256"}],
     "name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},
    {"constant": True,"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],
     "name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"},
]

MARKET_ABI = [
    {"inputs":[
        {"internalType":"uint256","name":"generated","type":"uint256"},
        {"internalType":"uint256","name":"consumed","type":"uint256"}
    ],
     "name":"reportEnergy",
     "outputs":[],
     "stateMutability":"nonpayable",
     "type":"function"
    },
    {"inputs":[
        {"internalType":"address","name":"buyer","type":"address"},
        {"internalType":"uint256","name":"kwh","type":"uint256"},
        {"internalType":"uint256","name":"pricePerKwh","type":"uint256"}
    ],
     "name":"payEnergy",
     "outputs":[],
     "stateMutability":"nonpayable",
     "type":"function"
    }
]

token_contract = web3.eth.contract(address=TOKEN_ADDRESS, abi=TOKEN_ABI)
market_contract = web3.eth.contract(address=MARKET_ADDRESS, abi=MARKET_ABI)

# -------------------
# Houses Setup (แต่ละบ้านมี wallet ของตัวเอง)
# -------------------
houses = {
    "A": {"role": "SELL_ONLY", "address": os.getenv("A_ADDRESS"), "private_key": os.getenv("A_PK")},
    "B": {"role": "SELL_ONLY", "address": os.getenv("B_ADDRESS"), "private_key": os.getenv("B_PK")},
    "C": {"role": "PROSUMER", "address": os.getenv("C_ADDRESS"), "private_key": os.getenv("C_PK")},
    "D": {"role": "PROSUMER", "address": os.getenv("D_ADDRESS"), "private_key": os.getenv("D_PK")},
    "E": {"role": "PROSUMER", "address": os.getenv("E_ADDRESS"), "private_key": os.getenv("E_PK")},
    "F": {"role": "BUY_ONLY", "address": os.getenv("F_ADDRESS"), "private_key": os.getenv("F_PK")},
    "G": {"role": "BUY_ONLY", "address": os.getenv("G_ADDRESS"), "private_key": os.getenv("G_PK")},
}

# -------------------
# Simulate energy production/consumption
# -------------------
def simulate_energy():
    for h, info in houses.items():
        gen = random.randint(0, 50)
        con = random.randint(0, 50)
        if info["role"] == "SELL_ONLY":
            con = 0
        elif info["role"] == "BUY_ONLY":
            gen = 0
        net = gen - con
        houses[h].update({"gen": gen, "con": con, "net": net})

# -------------------
# Blockchain Functions
# -------------------
def approve_token_if_needed(house, amount):
    addr = house["address"]
    pk = house["private_key"]
    current_allowance = token_contract.functions.allowance(addr, MARKET_ADDRESS).call()
    if current_allowance < amount:
        print(f"🔑 {addr} approve {amount} PALM ให้ EnergyMarket")
        nonce = web3.eth.get_transaction_count(addr, "pending")
        tx = token_contract.functions.approve(MARKET_ADDRESS, 10**27).build_transaction({
            "chainId": CHAIN_ID,
            "gas": 100000,
            "gasPrice": int(web3.eth.gas_price * 1.2),
            "nonce": nonce
        })
        signed_tx = web3.eth.account.sign_transaction(tx, pk)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        web3.eth.wait_for_transaction_receipt(tx_hash)

def report_energy(house):
    addr = house["address"]
    pk = house["private_key"]
    gen = house["gen"]
    con = house["con"]

    nonce = web3.eth.get_transaction_count(addr, "pending")
    tx = market_contract.functions.reportEnergy(gen, con).build_transaction({
        "chainId": CHAIN_ID,
        "gas": 150000,
        "gasPrice": int(web3.eth.gas_price * 1.2),
        "nonce": nonce
    })
    signed_tx = web3.eth.account.sign_transaction(tx, pk)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"📡 {addr} รายงาน Energy → ผลิต {gen}, ใช้ {con}, tx={web3.to_hex(tx_hash)}")
    web3.eth.wait_for_transaction_receipt(tx_hash)

def pay_energy(house, kwh, price_per_kwh=1):
    addr = house["address"]
    pk = house["private_key"]

    # ราคาต่อหน่วยเป็น wei ของ PALM
    price_per_kwh_wei = int(price_per_kwh * 10**18)
    total_cost = kwh * price_per_kwh_wei

    # ตรวจ allowance ก่อน
    approve_token_if_needed(house, total_cost)

    nonce = web3.eth.get_transaction_count(addr, "pending")
    tx = market_contract.functions.payEnergy(
        addr,
        kwh,
        price_per_kwh_wei
    ).build_transaction({
        "chainId": CHAIN_ID,
        "gas": 200000,
        "gasPrice": int(web3.eth.gas_price * 1.2),
        "nonce": nonce
    })

    signed_tx = web3.eth.account.sign_transaction(tx, pk)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"✅ {addr} จ่าย {total_cost/1e18} PALM ({kwh} kWh @ {price_per_kwh} PALM/kWh), tx={web3.to_hex(tx_hash)}")
    web3.eth.wait_for_transaction_receipt(tx_hash)

# -------------------
# Main Loop
# -------------------
try:
    while True:
        simulate_energy()
        print("\n📊 รอบใหม่:")
        for h, v in houses.items():
            print(f"{h} ({v['role']}) → ผลิต {v['gen']} ใช้ {v['con']} = Net {v['net']} kWh")

        # ทุกบ้านต้องรายงาน energy ก่อน
        for h, v in houses.items():
            report_energy(v)

        # ส่ง transaction สำหรับผู้ใช้ไฟเกิน
        for h, v in houses.items():
            if v["net"] < 0:
                cost = abs(v["net"])
                print(f"🔴 Buyer {h} จ่าย {cost} PALM → ส่ง transaction")
                pay_energy(v, cost)

        time.sleep(30)

except KeyboardInterrupt:
    print("🚪 ออกจากโปรแกรมแล้ว")
