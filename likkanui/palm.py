import random
import time
import os
from web3 import Web3
from dotenv import load_dotenv

# -------------------
# Blockchain Setup
# -------------------
load_dotenv()
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
BUYER_ADDRESS = os.getenv("BUYER_ADDRESS")

RPC_URL = "https://ethereum-holesky-rpc.publicnode.com"
CHAIN_ID = 17000  # Holesky Testnet

web3 = Web3(Web3.HTTPProvider(RPC_URL))
if not web3.is_connected():
    raise Exception("❌ เชื่อมต่อ Holesky ไม่ได้")

TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")
MARKET_ADDRESS = os.getenv("MARKET_ADDRESS")

TOKEN_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
]

MARKET_ABI = [
    {
        "inputs": [
            {"internalType": "address","name": "buyer","type": "address"},
            {"internalType": "uint256","name": "kwh","type": "uint256"},
            {"internalType": "uint256","name": "pricePerKwh","type": "uint256"}
        ],
        "name": "payEnergy",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

token_contract = web3.eth.contract(address=TOKEN_ADDRESS, abi=TOKEN_ABI)
market_contract = web3.eth.contract(address=MARKET_ADDRESS, abi=MARKET_ABI)

# -------------------
# Houses Setup
# -------------------
houses = {
    "A": {"role": "SELL_ONLY"},
    "B": {"role": "SELL_ONLY"},
    "C": {"role": "PROSUMER"},
    "D": {"role": "PROSUMER"},
    "E": {"role": "PROSUMER"},
    "F": {"role": "BUY_ONLY"},
    "G": {"role": "BUY_ONLY"},
}

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
def approve_token_if_needed(spender, amount):
    current_allowance = token_contract.functions.allowance(BUYER_ADDRESS, spender).call()
    if current_allowance < amount:
        print(f"🔑 ยังไม่ได้ approve หรือ allowance ไม่พอ ({current_allowance}), กำลัง approve...")
        nonce = web3.eth.get_transaction_count(BUYER_ADDRESS, "pending")
        tx = token_contract.functions.approve(
            spender, web3.to_wei(10**9, "ether")
        ).build_transaction({
            "chainId": CHAIN_ID,
            "gas": 200000,
            "gasPrice": web3.eth.gas_price * 2,  # เพิ่มเผื่อหน่อย
            "nonce": nonce
        })
        signed_tx = web3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"✅ Approve ส่งแล้ว: {web3.to_hex(tx_hash)}")
        web3.eth.wait_for_transaction_receipt(tx_hash)
    else:
        print(f"✅ allowance เพียงพอแล้ว ({current_allowance})")

def pay_energy(buyer, kwh, price_per_kwh=1):
    total_cost = int(kwh * (10**18))
    approve_token_if_needed(MARKET_ADDRESS, total_cost)

    # ใช้ nonce ของ pending transactions เพื่อลดโอกาสซ้ำ
    nonce = web3.eth.get_transaction_count(buyer, "pending")
    tx = market_contract.functions.payEnergy(
        buyer,
        total_cost,
        int(price_per_kwh * (10**18))
    ).build_transaction({
        "chainId": CHAIN_ID,
        "gas": 200000,
        "gasPrice": int(web3.eth.gas_price * 1.2),  # เพิ่ม gasPrice เล็กน้อย
        "nonce": nonce
    })

    signed_tx = web3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"✅ payEnergy ส่งแล้ว: {web3.to_hex(tx_hash)}")
    web3.eth.wait_for_transaction_receipt(tx_hash)  # รอ confirmation ก่อนส่ง transaction ถัดไป

# -------------------
# Main Loop
# -------------------
try:
    while True:
        simulate_energy()

        print("\n📊 รอบใหม่:")
        for h, v in houses.items():
            print(f"{h} ({v['role']}) → ผลิต {v['gen']} ใช้ {v['con']} = Net {v['net']} kWh")

        for h, v in houses.items():
            if v["net"] < 0:
                cost = abs(v["net"])
                print(f"🔴 Buyer {h} จ่าย {cost} PALM → ส่ง transaction")
                pay_energy(BUYER_ADDRESS, cost)

        time.sleep(30)

except KeyboardInterrupt:
    print("🚪 ออกจากโปรแกรมแล้ว")
