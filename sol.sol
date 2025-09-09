// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract Palm {
    string public name = "Palm Token";
    string public symbol = "PALM";
    uint8 public decimals = 18;
    uint256 public totalSupply;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);

    constructor(uint256 initialSupply) {
        totalSupply = initialSupply * 10 ** uint256(decimals);
        balanceOf[msg.sender] = totalSupply;
    }

    function transfer(address to, uint256 value) public returns (bool) {
        require(balanceOf[msg.sender] >= value, "Not enough balance");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }

    function approve(address spender, uint256 value) public returns (bool) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) public returns (bool) {
        require(balanceOf[from] >= value, "Not enough balance");
        require(allowance[from][msg.sender] >= value, "Not approved");

        balanceOf[from] -= value;
        allowance[from][msg.sender] -= value;
        balanceOf[to] += value;

        emit Transfer(from, to, value);
        return true;
    }
}

contract EnergyMarket {
    Palm public token;
    address public admin;

    enum Role { BUY_ONLY, SELL_ONLY, PROSUMER }

    struct Household {
        Role role;
        uint256 energyGenerated;
        uint256 energyConsumed;
        bool exists;
    }

    mapping(address => Household) public households;
    address[] public householdList;

    event HouseholdRegistered(address indexed user, Role role);
    event EnergyReported(address indexed user, uint256 generated, uint256 consumed);
    event EnergyReset(address indexed user);
    event EnergyPaid(address indexed buyer, uint256 kwh, uint256 pricePerKwh, uint256 totalCost);

    constructor(address tokenAddress) {
        token = Palm(tokenAddress);
        admin = msg.sender;
    }

    function registerHousehold(address user, Role role) external {
        require(msg.sender == admin, "Only admin can register");
        require(!households[user].exists, "Already registered");

        households[user] = Household(role, 0, 0, true);
        householdList.push(user);

        emit HouseholdRegistered(user, role);
    }

    function reportEnergy(uint256 generated, uint256 consumed) external {
        require(households[msg.sender].exists, "Not registered");

        households[msg.sender].energyGenerated = generated;
        households[msg.sender].energyConsumed = consumed;

        emit EnergyReported(msg.sender, generated, consumed);
    }

    function resetEnergy() external {
        require(households[msg.sender].exists, "Not registered");

        households[msg.sender].energyGenerated = 0;
        households[msg.sender].energyConsumed = 0;

        emit EnergyReset(msg.sender);
    }

    function payEnergy(address buyer, uint256 kwh, uint256 pricePerKwh) external {
    require(households[buyer].exists, "Buyer not registered");
    require(
        households[buyer].role == Role.BUY_ONLY ||
        households[buyer].role == Role.PROSUMER,
        "Not allowed to buy"
    );

    // 🔹 คำนวณรวมพลังงานที่เหลือขายก่อน
    uint256 totalSell = 0;
    for (uint i = 0; i < householdList.length; i++) {
        Household storage h = households[householdList[i]];
        if (h.energyGenerated > h.energyConsumed) {
            totalSell += (h.energyGenerated - h.energyConsumed);
        }
    }

    // ❌ ถ้าไม่มีผู้ขาย → ห้ามดึงเงิน
    require(totalSell > 0, "No sellers available");

    // 🔹 ซื้อได้แค่ตามพลังงานที่มีจริง
    uint256 actualKwh = kwh > totalSell ? totalSell : kwh;
    uint256 totalCost = actualKwh * pricePerKwh;

    require(token.transferFrom(buyer, address(this), totalCost), "Payment failed");

    // 🔹 แจกจ่ายโทเคนตามสัดส่วน
    for (uint i = 0; i < householdList.length; i++) {
        Household storage h = households[householdList[i]];
        if (h.energyGenerated > h.energyConsumed) {
            uint256 net = h.energyGenerated - h.energyConsumed;
            uint256 payout = (totalCost * net) / totalSell;
            token.transfer(householdList[i], payout);
        }
    }

    emit EnergyPaid(buyer, actualKwh, pricePerKwh, totalCost);
}

}
