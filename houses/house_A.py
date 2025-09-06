import random
import time
import os
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import report_energy, pay_energy

load_dotenv()

ADDRESS = os.getenv("A_ADDRESS")
PRIVATE_KEY = os.getenv("A_PK")
ROLE = "SELL_ONLY"

try:
    while True:
        gen = random.randint(10,50)
        con = 0
        net = gen - con

        print(f"\n🏠 House A → ผลิต {gen}, ใช้ {con} = Net {net} kWh")
        report_energy(ADDRESS, PRIVATE_KEY, gen, con)

        if net < 0:
            pay_energy(ADDRESS, PRIVATE_KEY, abs(net))

        time.sleep(30)

except KeyboardInterrupt:
    print("🚪 ออกจากโปรแกรมแล้ว")
