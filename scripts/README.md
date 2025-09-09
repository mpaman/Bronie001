## วิธีใช้งานระบบ Blockchain Energy Market (Brownie)

### 1. เตรียมไฟล์ .env
ใส่ address และ private key ของแต่ละบ้าน, contract address ใน `scripts/.env`

### 2. Deploy Smart Contract (Palm & EnergyMarket)
```sh
brownie run scripts/deploy.py --network holesky
```
จะได้ contract address สำหรับ Palm และ EnergyMarket (นำไปใส่ใน .env)

### 3. Register บ้านแต่ละหลัง + โอนเหรียญ
```sh
brownie run scripts/register_and_fund.py --network holesky
```
จะ register บ้านและโอน Palm Token ให้แต่ละบ้าน

### 4. รันบ้านแต่ละหลัง (จำลองการผลิต/ใช้ไฟ)
แต่ละบ้านให้เปิด terminal ใหม่ แล้วรัน เช่น
```sh
brownie run scripts/houses/house_A.py --network holesky
brownie run scripts/houses/house_B.py --network holesky
brownie run scripts/houses/house_C.py --network holesky
# ...
```
แต่ละบ้านจะทำงานตาม role:
- SELL_ONLY: ผลิตไฟฟ้าเท่านั้น (A, B)
- PROSUMER: ผลิตและใช้ไฟฟ้า, ซื้อไฟถ้าขาด (C, D, E)
- BUY_ONLY: ใช้ไฟฟ้าเท่านั้น, ซื้อไฟเสมอ (F, G)

### หมายเหตุ
- ตรวจสอบ address ที่ derive จาก private key ว่าตรงกับ .env ทุกครั้ง
- หาก deploy contract ใหม่ ต้อง register บ้านใหม่ด้วย
