import random
import time
import os
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import report_energy, pay_energy

load_dotenv()

ADDRESS = os.getenv("C_ADDRESS")
PRIVATE_KEY = os.getenv("C_PK")
ROLE = "PROSUMER"

try:
    while True:
        gen = random.randint(0,50)
        con = random.randint(0,50)
        net = gen - con

        print(f"\n🏠 House C → ผลิต {gen}, ใช้ {con} = Net {net} kWh")
        report_energy(ADDRESS, PRIVATE_KEY, gen, con)

        if net < 0:
            pay_energy(ADDRESS, PRIVATE_KEY, abs(net))

        time.sleep(30)

except KeyboardInterrupt:
    print("🚪 ออกจากโปรแกรมแล้ว")
