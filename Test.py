
import time
import os
import sys
import sqlite3
from dotenv import load_dotenv
import minimalmodbus
from flask import Flask, render_template_string, request
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import report_energy, pay_energy, reset_energy

load_dotenv()

ADDRESS = os.getenv("A_ADDRESS")
PRIVATE_KEY = os.getenv("A_PK")
ROLE = "SELL_ONLY"

DB_PATH = "energy_A.db"
SCALE = 1000  # แปลง float → int (milli-kWh)

# -------------------------------
# Modbus SDM120 setup
# -------------------------------
dev_addr = 11
serial_port = 'COM1'
baudrate = 2400

rs485 = minimalmodbus.Instrument(serial_port, dev_addr)
rs485.serial.baudrate = baudrate
rs485.serial.bytesize = 8
rs485.serial.parity   = minimalmodbus.serial.PARITY_NONE
rs485.serial.stopbits = 1
rs485.serial.timeout  = 0.5
rs485.debug = False
rs485.mode = minimalmodbus.MODE_RTU

# -------------------------------
# SQLite
# -------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS energy_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_generated REAL,
            total_consumed REAL,
            delta_generated REAL,
            delta_consumed REAL,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def get_last_total():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT total_generated, total_consumed FROM energy_log ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return 0.000, 0.000

def save_energy(total_gen, total_con, delta_gen, delta_con):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO energy_log (total_generated, total_consumed, delta_generated, delta_consumed)
        VALUES (?, ?, ?, ?)
    """, (total_gen, total_con, delta_gen, delta_con))
    conn.commit()
    conn.close()

# -------------------------------
# Loop
# -------------------------------

# -------------------------------
# Flask Dashboard
# -------------------------------
app = Flask(__name__)

DASHBOARD_TEMPLATE = '''
<html>
<head>
    <title>House A Dashboard</title>
    <style>
        body { font-family: Arial; margin: 40px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: right; }
        th { background: #eee; }
        h2 { margin-top: 2em; }
    </style>
</head>
<body>
    <h1>🏠 House A Dashboard</h1>
    <h2>Current Status</h2>
    <ul>
        <li><b>Total Generated:</b> {{ current.total_generated }} kWh</li>
        <li><b>Total Consumed:</b> {{ current.total_consumed }} kWh</li>
        <li><b>Net:</b> {{ current.net }} kWh</li>
    </ul>
    <h2>History (latest 50)</h2>
    <table>
        <tr>
            <th>ID</th>
            <th>Generated</th>
            <th>Consumed</th>
            <th>Δ Generated</th>
            <th>Δ Consumed</th>
            <th>Timestamp</th>
        </tr>
        {% for row in history %}
        <tr>
            <td>{{ row['id'] }}</td>
            <td>{{ row['total_generated'] }}</td>
            <td>{{ row['total_consumed'] }}</td>
            <td>{{ row['delta_generated'] }}</td>
            <td>{{ row['delta_consumed'] }}</td>
            <td>{{ row['ts'] }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
'''

def get_dashboard_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM energy_log ORDER BY id DESC LIMIT 50")
    rows = cur.fetchall()
    cur.execute("SELECT total_generated, total_consumed FROM energy_log ORDER BY id DESC LIMIT 1")
    last = cur.fetchone()
    conn.close()
    if last:
        total_generated = round(last[0], 5)
        total_consumed = round(last[1], 5)
    else:
        total_generated = 0.0
        total_consumed = 0.0
    return {
        'current': {
            'total_generated': total_generated,
            'total_consumed': total_consumed,
            'net': round(total_generated - total_consumed, 5)
        },
        'history': rows
    }

@app.route("/")
def dashboard():
    data = get_dashboard_data()
    return render_template_string(DASHBOARD_TEMPLATE, **data)

def run_dashboard():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

def start_dashboard_thread():
    t = threading.Thread(target=run_dashboard, daemon=True)
    t.start()

init_db()
start_dashboard_thread()

try:
    while True:
        last_gen, last_con = get_last_total()

        # อ่านไฟจาก Modbus
        total_gen = rs485.read_float(0x0156, functioncode=4, number_of_registers=2)
        total_con = 0.0  # บ้านนี้ยังไม่ใช้ไฟ

        delta_gen = round(total_gen - last_gen, 5)
        delta_con = round(total_con - last_con, 5)

        save_energy(total_gen, total_con, delta_gen, delta_con)

        net = total_gen - total_con
        print(f"\n🏠 House A → ผลิตรวม {total_gen:.5f}, ใช้รวม {total_con:.5f} = Net {net:.5f} kWh")

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
    if rs485.serial:
        rs485.serial.close()
