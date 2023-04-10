from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadBuilder, BinaryPayloadDecoder
from pymodbus.exceptions import *
import argparse

from datetime import datetime

import time, os, json, sys
import psycopg

from utils.outils import hexaTodate

# ---------------------------------------------------------------------------------------------------------------------
def help():
    
    print("888    888          888")        
    print("888    888          888")          
    print("888    888          888")         
    print("8888888888  .d88b.  888 88888bb.")  
    print("888    888 d8P  Y8b 888 888 ''88b") 
    print("888    888 88888888 888 888  888") 
    print("888    888 Y8b.     888 888 d88P") 
    print("888    888  *Y8888  888 88888*")  
    print("                        888")      
    print("                        888")      
    print("                        888")
    print("******************************************************")
    print("Usage : python[version] modbus2Psql.py --config [config directory path]**\n")
    print("        * --config [config directory path] : Config files for database connection, modbus server connection, modbus registers to read values with their type (int, float, bool)\n")
    print("")
#

"""
	Dans la version V2, le fichier de config modbus (v2) precise pour chaque registre 
        le data type des donnees afin de definir une lecture =/ quand il s'agit d'un reel
        ou d'un simple entier (pas coder sur le meme nombre de registre)
"""

##############################################################################################

"""
   _____ _       _           _           
  / ____| |     | |         | |          
 | |  __| | ___ | |__   __ _| | ___  ___ 
 | | |_ | |/ _ \| '_ \ / _` | |/ _ \/ __|
 | |__| | | (_) | |_) | (_| | |  __/\__ \
  \_____|_|\___/|_.__/ \__,_|_|\___||___/
"""

# Beggining offset
offset = 40001
timeout = 0

FLAG_timeout = False
client = None

################################### Func utiles _____________________________________________________________
def decode(registre, n_type):
    
    """ 
        [21/09/22] - 
            Lit la valeur dans le registre (registre) de 16 ou 32 bits en fonction du type (float, int, bool)
            car un type n'est pas code sur le meme nombre de registre
    """
    res, val = 0, 0
    
    # Definir decodeur
    
    if n_type == 'float':
        res = client.read_holding_registers( int(registre) - offset, 2, unit = 1)
        decodeur = BinaryPayloadDecoder.fromRegisters(res.registers, byteorder = Endian.Big, wordorder = Endian.Big)
        val = decodeur.decode_32bit_float()
        
    elif n_type == 'int' or n_type == 'bool':
        res = client.read_holding_registers( int(registre) - offset, 1, unit = 1)
        decodeur = BinaryPayloadDecoder.fromRegisters(res.registers, byteorder = Endian.Big, wordorder = Endian.Big)
        val = decodeur.decode_16bit_int()
    
    elif n_type == 'bool':
        res = client.read_holding_registers( int(registre) - offset, 1, unit = 1)
        decodeur = BinaryPayloadDecoder.fromRegisters(res.registers, byteorder = Endian.Big, wordorder = Endian.Big)
        val = decodeur.decode_8bit_int() # ou ? val = decoder.decode_bits()
        
    print("Lu : {}".format(res.registers))
            
    return val
#______________________________________________________________________________________________________________________


# Programme boucle_____________________________________________________________________________________________________
def main_loop(config):

    """
        Main Loop of the service, it will stop until an error occur or the service itself is stopped
        
        Args:
        -----
            * path <str> : Directory path of config files and ressources
    """
    
    # Charger fichier de config modbus
    print("Chargement des fichiers de configs ...\n")
    
    config_mdb = json.load(open(config+"/config_modbus.json"))
    host, port, registres = config_mdb["host"], config_mdb["port"], config_mdb["registres"]
    
    time_registre, time_tag = None, None
    if config_mdb.get('time_registre') is not None:
    
        time_registre = list(config_mdb["time_registre"].keys())[0]       #// registre pour le temps
        time_tag = list(config_mdb["time_registre"].values())[0]          #// tag associe au temps
    
    intels = json.load(open(config+"/config_database.json"))
    tables_registres = intels["tables_registres"]                 #// correspondance tables / registre / tag

    print("... Fichiers de config chargés !")
    
    # Remplir une table de correspondance registre_name : valeur
    modbus_regval = {list(reg.keys())[0] : 0 for reg in registres}

    while True:
        
        ############################### Etablir la connection au serveur modbus
        
        # Premiere connection ?
        if client is None:
            client = ModbusClient(host, port)
            ok = client.connect()

        if not ok:
            print("connection Modbus failed -- waiting to connction to be restore")
            timeout += 1
            time.sleep(1)
            
            # Si tentative precedent echoue
            if FLAG_timeout:

                print("Tentative de restart du networking service echoue || Rebootage du serveur")
                
                exit(-1)
                #os.system("shutdown -r now")

            # Si plus de 500 Seconde d'attente ...
            if timeout > 10000:
                
                # ... print ...
                print("Nb tentative de connection depasse, tentative de restart des connections")

                # ... restart networking interface ...
                os.system("sudo /etc/init.d/networking restart")
                
                # ... sleep a few seconde for re-init ...
                time.sleep(4)
                
                # ... reboot timeout
                timeout = 0

                # ... flag timeout deja effectue
                FLAG_timeout = True
                
        else:

            print("connection Mobdbus success !")

            # Calcule temps d'execution
            s = datetime.now()

            # FLAG repasse a False
            FLAG_timeout = False

            #0 Obtenir le temps récup en modbus qui est sur 4 x 16 bits ....
            date = None
            if time_registre is not None:
                res = client.read_holding_registers( int(time_registre) - offset, 4, unit = 1)

                if res.isError():
                
                    # Les erreur en pymodbus sont renvoye en tant qu'objet, check = res.isError() 
                    print(res.message)
                    
                    # Traitement#1 - Tenter une reconnection apres un sleep d'1/2 sec
                    client.close()
                    client = None
                    time.sleep(1)
                    #goto('connexion')
                
                print("Lu date : {}".format(res.registers))

                # ... decodage en hexa et formatage de la date
                date = hexaTodate(res.registers)
            
            #1 Obtenir la valeurs dans les registres recup en modbus
            for i in registres:

                # Get id@ and type
                id, type_ = int( list(i.keys())[0] ), str( list(i.values())[0] )
                print("registre : {} ({})".format(id, type_))
                
                # Appel la fonction decode(@dress, type variable) --> valeur
                val = decode(id, type_) 
                
                print("Valeur dans le registre {} = {}".format(id, val))

                # <dict> Inserer dans table de correspondance la valeur du registre a T
                print("type : ", i)
                modbus_regval[ list(i.keys())[0] ] = (date, val)

            print(modbus_regval)            
            ################################## PostGreSQL ##########################################

            # Se connecter a la DB PSQL
            try:
                    intels = json.load(open("config/config_database.json"))

                    conn = psycopg.connect(host = intels["host"],
                        dbname = intels["dbname"],
                        user = intels["user"],
                        password = intels["pass"])

                    print('Connecting to the PostgreSQL database...')
                    
                    cursor = conn.cursor()

                    try:

                        # Pour chaque table de la base lister dans fichier de config, insérer les valeurs de registre extrait selon les tags
                        for unit in intels['tlist']:
                            
                            print(unit)
                            
                            # Construire la requete psql ....
                            sql = "INSERT INTO {} (\"{}\",".format(unit, time_tag)

                            for k, v in tables_registres[unit].items():
                                sql += " \"{}\",".format(v)
                                
                            sql += ") VALUES ("
                            
                            # .... Ici j'ai déjà : INSERT INTO table(col1, col2, ...) VAlUES ( reste a faire la 2ième partie (%s, %s, ....)
                            for i in range(0, len(tables_registres[unit])):
                                sql += "%s, "
                            
                            # .... requête finie
                            sql += "%s, %s)"
                            
                            print("Recap Requete SQL : ")
                            print(sql)

                            # Rassembler les valeurs en listant tout les registres...
                            vals = [date]
                            for reg, tag in tables_registres[unit].items():
                                
                                print(reg, tag)

                                # Chercher la valeur pour ce registre et ne prendre que la valeur (pas la date)
                                val = modbus_regval[reg][1]

                                # Inserer la valeur
                                vals.append(val)                           
                            
                            # ... transformer liste en tuple pour l'insertion
                            vals = tuple(vals)
                            print(vals)

                            # Executer la requete
                            cursor.execute(sql, vals)
                                
                            # Commit les changements dans la base
                            conn.commit()
                            
                            # Print
                            print('Insertion complete')

                            # Fermer connection a la base
                            #conn.close()
                          
                    except Exception as error:
                        print('Insertion failed / caused by : {}'.format(error))
                        conn.rollback()

            except (Exception, psycopg.DatabaseError) as error:
                    #logger.info("EROR during connection : {}".format( error.__str__()))
                    print("ERREUR during connection attempt : {}".format(error))
                    conn.close()
                    print('Database connection closed.')
            
            print("Temps d'execution Modbus (Lecture) + PSQL (Ecriture) : {}".format(datetime.now() - s))
            # Dormir temps de mise a jour ~15ms (0,015sec) mais prendre en compte le temps d'execution pour arriver ici
            #client.close() # Cause de probleme lors du 2ieme passage : la methode client.holding_registers() renvoit une erreur - parce que le temps de sleep est trop court => erreur I/O - (passe pour 0,5secs) 
            time.sleep(0.005)

# --------------------------------------------------------------------------------------------------------------------------
def args_parser(args = sys.argv[1:]):

    """
        The function check the parameters key of the script are correct
        
        args (str) : aguments of the script
        
        Return:
        ------
            - Params values
    """
    
    parser = argparse.ArgumentParser(description = "Parser object")
    parser.add_argument("-c", "--config", type = str, help = "path to configuration files for database authentification")
    #parser.add_argument("-t", "--tables", type = str, help = "tables name in db and Tag columns")
    parser.add_argument("-o", "--offset", type = int, default = 40001), help = "beginning offset register -- default is 40001 for coil registers")
    options = parser.parse_args(args)
    
    return options
 
# --------------------------------------------------------------------------------------------------------------------------
"""
  __  __       _         _ 
 |  \/  |     (_)       | |
 | \  / | __ _ _ _ __   | |
 | |\/| |/ _` | | '_ \  | |
 | |  | | (_| | | | | | |_|
 |_|  |_|\__,_|_|_| |_| (_)
 
To clarify how __main__ and the function main() works. 
When you execute a module it will have a name which is stored in __name__. 
If you execute the module stand alone as a script it will have the name __main__. 
If you execute it as part of a module ie import it into another module it will have the name of the module.

The function main() can be named anything you would like, and that wouldn't affect your program. 
It's commonly named "" main  "" in small scripts but it's not a particularly good name if it's part of a larger body of code.
"""

print("Current directory : {}".format(os.system("pwd")))

if __name__ == '__main__':
    
    # Begin by erase previous syslog
    # Uncomment this line if you used a syslog server
    # os.system("echo > //var/log/messages")

    # Get Params
    args = str(sys.argv).split(' ')
    opts = args_parser(sys.argv[1:])
    
    if len(args) == 1 or any(op == None for op in [opts.config, opts.offset]):
        print(opts)
        print("\n ! Paramètre d'éxécution manquant !\n")
        help()
        
    
    # Set offset"
    offset = opt.offset
    
    else:
        
        ################### Cheking file does exist
        if not exists(opts.config):
            print("Directory {} doesn't exist doesn't exist")
            exit(-1)

        ################### Check connection database possible
        intels = json.load(open(opts.config+'config_databse.json'))
        try:          
            conn = psycopg.connect(host = intels["host"],
                            dbname = intels["dbname"],
                            user = intels["user"],
                            password = intels["pass"])

            # connect to the PostgreSQL server
            print('Connecting to the PostgreSQL database possible...')
            conn.close()

        except (Exception, psycopg.DatabaseError) as error:
            print("Exception occured : {}".format(error))
            #syslog.syslog(syslog.LOG_WARNING, "WARNING :Connection to host failed check connection or credentials -- {}".format(error))
            exit(-1)
            
        # lancer Service
        main_loop(opts.config)
            
#FIN
"""
 _________
( Coded by)
(_Chris.P_)            /)
          ^   /\___/\ ((
           \  \`@_@'/  ))
            v {_:Y:.}_//
-------------{_}^-'{_}----------"""
