#------------------ Sert pour la lecture de la date dans les registres ----------------- #
#                                                                                        #

from datetime import datetime

# format du type date pour postgreSQL
format = "%Y-%m-%d %H:%M:%S.%f"

def hexaTodate(registers):
    
    """
        La date dans l'automate est codee 8x8 octets ==> 64 bits
        Donc : 4 registres de 16bits
        
        Exemple : [8711, 4882, 2356, 33316]
        
        - Les 16 premiers bits codent l'annee le mois 
        - Les 16 suivant le jour et l'heure
        - Les 16 suivant les minutes et les sec
        - Les 16 derniers les millisecondes
        
        Ce qui donne : hex(8711) = 2207, hex(4882) = 1312; hex(2356) = 934, hex(33316) = 8224

        ==> 2022-07-13 12:09:34.008224
        
        Params:
        -------
            registers : <list>
                Contient les valeurs décimal lu des registres
                
        Retour: 
        -------
            La date au format <datetime> 
    """
    
    # Transformer en hexa
    hexaTime = [ hex(word) for word in registers ]
    print(hexaTime)

    # L'année est codé avec une valeur allant de 0 --> 99 donc + 2000 pour obtenir l'année
    annee, mois = 2000+ int(hexaTime[0].split('x')[1][:2]), hexaTime[0].split('x')[1][2:]
    #jour, heure = hexaTime[1].split('x')[1][:2], hexaTime[1].split('x')[1][2:]

    # Corection
    if len(hexaTime[1].split('x')[1]) % 4 == 0:
       jour, heure = hexaTime[1].split('x')[1][:2], hexaTime[1].split('x')[1][2:]
    else:

       # 3 Cas possibles
       
       #1
       if len(hexaTime[1].split('x')[1]) % 2 == 0:
          # Soit la date est de format 0x17 et jour = 01 et heures = 07
          jour, heure = hexaTime[1].split('x')[1][:1], hexaTime[1].split('x')[1][1:]
    
       #2
       elif len(hexaTime[1].split('x')[1]) % 3 == 0:
        
          # Soit la date est de format 0x147 et jour = 14 et heures = 7 ==> mais lirai  j=01 et h = 47
          if int(hexaTime[1].split('x')[1][1:]) > 23:
             jour, heure = hexaTime[1].split('x')[1][:2], hexaTime[1].split('x')[1][2:]
        
          # Soit la date est de format 0x817 et jour = 08 et heures = 17  ==> mais lirai j=81 et h = 7
          elif int(hexaTime[1].split('x')[1][1:]) > 31:
             jour, heure = hexaTime[1].split('x')[1][:1], hexaTime[1].split('x')[1][1:]
          
          else:
             jour, heure = hexaTime[1].split('x')[1][:1], hexaTime[1].split('x')[1][1:]
    
    # Obliger de checker car ne code pas 01, 02, 03, mais 1, 2, 3 si <10minutes donc que 3 digits et donc la séparation est diff
    if len(hexaTime[2].split('x')[1]) % 4 == 0:

        minute, sec = hexaTime[2].split('x')[1][:2], hexaTime[2].split('x')[1][2:]
    else:
         minute, sec = hexaTime[2].split('x')[1][:1], hexaTime[2].split('x')[1][1:]

    ms = hexaTime[3].split('x')[1]

    # print(datetime(annee, int(mois), int(jour), int(heure), int(minute), int(s), int(ms)))
    print(annee, mois, jour, heure, minute, sec)

    return datetime(int(annee), int(mois), int(jour), int(heure), int(minute), int(sec), int(ms)).strftime(format)[:-3]
#done
