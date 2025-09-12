# Keyes

git remote set-url origin https://github.com/mpaman/Keyes.git

เปลี่ยน repo
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import os
import sys
import sqlite3
from dotenv import load_dotenv
import minimalmodbus

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import report_energy, pay_energy, reset_energy

load_dotenv()

ADDRESS = os.getenv("C_ADDRESS")
PRIVATE_KEY = os.getenv("C_PK")
ROLE = "PROSUMER"

DB_PATH = "energy_C.db"
SCALE = 1000

# -------------------------------
# Modbus SDM120 setup (2 meters)
# -------------------------------
# Meter 1: Generation (เช่น inverter)
gen_addr = 15
gen_port = "COM1"
gen_baudrate = 2400
meter_gen = minimalmodbus.Instrument(gen_port, gen_addr)
meter_gen.serial.baudrate = gen_baudrate
meter_gen.serial.bytesize = 8
meter_gen.serial.parity = minimalmodbus.serial.PARITY_NONE
meter_gen.serial.stopbits = 1
meter_gen.serial.timeout = 0.5
meter_gen.debug = False
meter_gen.mode = minimalmodbus.MODE_RTU

# Meter 2: Consumption (โหลดบ้าน)
con_addr = 25
con_port = "COM1"
con_baudrate = 2400
meter_con = minimalmodbus.Instrument(con_port, con_addr)
meter_con.serial.baudrate = con_baudrate
meter_con.serial.bytesize = 8
meter_con.serial.parity = minimalmodbus.serial.PARITY_NONE
meter_con.serial.stopbits = 1
meter_con.serial.timeout = 0.5
meter_con.debug = False
meter_con.mode = minimalmodbus.MODE_RTU


# -------------------------------
# SQLite
# -------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS energy_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_generated REAL,
            total_consumed REAL,
            delta_generated REAL,
            delta_consumed REAL,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    conn.commit()
    conn.close()


def get_last_total():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT total_generated, total_consumed FROM energy_log ORDER BY id DESC LIMIT 1"
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return 0.000, 0.000


def save_energy(total_gen, total_con, delta_gen, delta_con):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO energy_log (total_generated, total_consumed, delta_generated, delta_consumed)
        VALUES (?, ?, ?, ?)
    """,
        (total_gen, total_con, delta_gen, delta_con),
    )
    conn.commit()
    conn.close()


# -------------------------------
# Loop
# -------------------------------
init_db()

try:
    while True:
        last_gen, last_con = get_last_total()

        # อ่านค่าจาก Modbus ทั้ง 2 ตัว
        total_gen = meter_gen.read_float(0x0156, functioncode=4, number_of_registers=2)
        total_con = meter_con.read_float(0x0156, functioncode=4, number_of_registers=2)

        delta_gen = round(total_gen - last_gen, 5)
        delta_con = round(total_con - last_con, 5)

        save_energy(total_gen, total_con, delta_gen, delta_con)

        net = total_gen - total_con
        print(
            f"\n🏠 House C → ผลิตรวม {total_gen:.5f}, ใช้รวม {total_con:.5f} = Net {net:.5f} kWh"
        )

        # ส่งค่า delta เข้า contract
        gen_int = int(delta_gen * SCALE)
        con_int = int(delta_con * SCALE)
        report_energy(ADDRESS, PRIVATE_KEY, gen_int, con_int)

        if net < 0:
            pay_energy(ADDRESS, PRIVATE_KEY, int(abs(net) * SCALE))

        time.sleep(300)

except KeyboardInterrupt:
    print("🚪 ออกจากโปรแกรม → resetEnergy()")
    reset_energy(ADDRESS, PRIVATE_KEY)
finally:
    # ปิด serial ทั้ง 2 ตัว
    if meter_gen.serial:
        meter_gen.serial.close()
    if meter_con.serial:
        meter_con.serial.close()
