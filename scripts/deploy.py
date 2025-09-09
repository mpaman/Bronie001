
from brownie import Palm, EnergyMarket, accounts

def main():
    acct = accounts.load('holesky_deployer')
    # Deploy Palm token with initial supply (e.g., 1,000,000 tokens)
    palm = Palm.deploy(1_000_000, {'from': acct})
    print(f"Palm Token deployed at: {palm.address}")
    # Deploy EnergyMarket contract with Palm token address
    market = EnergyMarket.deploy(palm.address, {'from': acct})
    print(f"EnergyMarket deployed at: {market.address}")
