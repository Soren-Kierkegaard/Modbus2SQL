# Modbus2SQL

![Résultats](https://github.com/Soren-Kierkegaard/Modbus2SQL/blob/main/img/modbus1.png)

A programm that can read outputs of a programmable logic controller (PLC) via modbus communication protocol through a modbus client/server architectur

# More on Modbus and PLC
* https://en.wikipedia.org/wiki/Modbus
* https://en.wikipedia.org/wiki/Programmable_logic_controller

# Repository Files:
```
├── REAMDE.md
├── modbus2SQL.py
└── img
    ├── // for read me
    ├── ....
    └── ....
└── utils
    └── outils.py
└── config
    ├── config_modbus.json
    └── config_datase.json
```

# Architecture

- ![Résultats](https://github.com/Soren-Kierkegaard/Modbus2SQL/blob/main/img/modbus4.png)

# Configuration

There are 2 configuration files :
  * config_modbus.json :: Ip adresse and credentials for modbus connection server, it also list the register to read or write and the type of value in it -- boolean, float or int doesn't take the same space so it is necessary to precise it when reading (see : Modbus Registers for more).
  * config_datase.json :: That is the configuration file for the database connection, it also precise the tables in the database and the mapping between Modbus Registers and column name in the tables.

# Modbus Connection

  * If you use a different protocol that TCP/IP, please change the Trasport Classes : https://pymodbus.readthedocs.io/en/latest/source/library/client.html#transport-classes 
# Modbus Registers

- ![Résultats](https://github.com/Soren-Kierkegaard/Modbus2SQL/blob/main/img/modbus2.png)

As an example value by default in the config_modbus.json are for Holding Registers that start at offset 40001
if you used different registers, you will need :

  *1 To change the config file as needed by specifiying the register id + type
  *2 To change the reading function in the code for the "" client "" object, look at the SERIAL section for more in https://pymodbus.readthedocs.io/en/latest/source/library/REPL.html

# The Time Problem

Time is coded a bit differently in registers and neda bit of extra works to be process properly

- ![Résultats](https://github.com/Soren-Kierkegaard/Modbus2SQL/blob/main/img/modbus3.png)

# Requirements

You will need pymodbus : https://pypi.org/project/pymodbus/

# Acknowledge

@Coded in 2022 
