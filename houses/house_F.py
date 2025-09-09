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

ADDRESS = os.getenv("F_ADDRESS")
PRIVATE_KEY = os.getenv("F_PK")
ROLE = "BUY_ONLY"

try:
    while True:
        gen = 0
        con = random.randint(10,50)
        net = gen - con

        print(f"\n🏠 House F → ผลิต {gen}, ใช้ {con} = Net {net} kWh")
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
