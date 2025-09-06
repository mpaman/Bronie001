from config import web3, CHAIN_ID, MARKET_ADDRESS, token_contract, market_contract

def approve_token_if_needed(addr, pk, amount):
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

def report_energy(addr, pk, gen, con):
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

def pay_energy(addr, pk, kwh, price_per_kwh=1):
    price_per_kwh_wei = int(price_per_kwh * 10**18)
    total_cost = kwh * price_per_kwh_wei
    approve_token_if_needed(addr, pk, total_cost)

    nonce = web3.eth.get_transaction_count(addr, "pending")
    tx = market_contract.functions.payEnergy(addr, kwh, price_per_kwh_wei).build_transaction({
        "chainId": CHAIN_ID,
        "gas": 200000,
        "gasPrice": int(web3.eth.gas_price * 1.2),
        "nonce": nonce
    })
    signed_tx = web3.eth.account.sign_transaction(tx, pk)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"✅ {addr} จ่าย {total_cost/1e18} PALM ({kwh} kWh @ {price_per_kwh} PALM/kWh), tx={web3.to_hex(tx_hash)}")
    web3.eth.wait_for_transaction_receipt(tx_hash)
