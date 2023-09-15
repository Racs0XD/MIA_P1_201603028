from Admin_Discos.FDISK import fdisk
from Admin_Discos.MKDISK import mkdisk
from Admin_Discos.RMDISK import rmdisk
from Admin_Discos.MOUNT import mount
from Admin_Discos.UNMOUNT import unmount
from Admin_Discos.MKFS import mkfs
from Admin_Usuario_Grupo.LOGIN import login
from Admin_Usuario_Grupo.MKGRP import mkgrp
from Admin_Usuario_Grupo.RMGRP import rmgrp
from Admin_Usuario_Grupo.MKUSR import mkusr
from Admin_Usuario_Grupo.RMUSR import rmusr
from Estructuras.BITMAP import bitMap, bytesMapD
from REP import rep
import re

# Se definen las variables globales
particiones_montadas = []
usuarios = None  # Valor predeterminado None al inicio del programa
particion_actual = None  # Valor predeterminado None al inicio del program


def execute(comando):
    # Obtener el path del archivo
    path = re.search(r'(?<=-path=).*', comando).group(0)
    # Validar que el archivo tenga la extensión adecuada
    print(path)
    if not path.endswith(".adsj"):
        print("Error: El archivo debe tener extensión .adsj")
        return
    try:
        # Abrir el archivo
        with open(path, 'r') as file:
            # Leer el archivo linea por linea
            for line in file:
                # Eliminar los saltos de linea, los comentarios y validar el comando
                line = line.strip()
                if not line or line.isspace():  # Ignorar líneas en blanco o con solo espacios
                    continue
                if '#' not in line:
                    if line == "pause":
                        input("Presione enter para continuar...\n")
                    else:
                        validar_comando(line)
    except FileNotFoundError:
        print("Error: El archivo especificado no existe")

def validar_comando(comando):
    global usuarios, particion_actual
    # Separar el comando y los argumentos
    comando_separado = comando.split('-')
    cmd = comando_separado[0].replace(' ', '').lower() # Obtenemos el comando
    argumentos = comando_separado[1:] # Obtenemos los argumentos
    # Verificar si es el comando mkdisk
    
    if cmd == "mkdisk":
        mkdiskCom(argumentos)

    elif cmd == "rmdisk":
        rmdiskCom(argumentos)

    elif cmd == "fdisk":
        fdiskCom(argumentos)

    elif cmd == "mount":
        mountCom(argumentos)
    
    elif cmd == "unmount":
        unmountCom(argumentos)

    elif cmd == "mkfs":
        mkfsCom(argumentos)

    elif cmd == "login":
        loginCom(argumentos)
    
    elif cmd == "logout":
        logoutCom(argumentos)          
    
    elif cmd == "mkgrp":
        mkgrpCom(argumentos)
    
    elif cmd == "rmgrp":
        rmgrpCom(argumentos)
    
    elif cmd == "mkusr":
        mkusrCom(argumentos)

    elif cmd == "rmusr":
        rmusrCom(argumentos)
    
    elif cmd == "rep":
        repCom(argumentos)    

    elif cmd == "exit":
        exit()

    else:
        print("Error: comando no reconocido.")

def mkdiskCom(argumentos):
        # Convertir los argumentos en un diccionario
        parametros = {}
        for arg in argumentos:
            key, value = arg.split('=')
            parametros[key.lower()] = value
            
        # Validar los parametros recibidos
        if "size" not in parametros or "path" not in parametros:
            print("Error: los parametros size y path son obligatorios para el comando mkdisk")
            return
        else:
            mkdisk(parametros)
        
def rmdiskCom(argumentos):
    # Convertir los argumentos en un diccionario
    parametros = {}
    for arg in argumentos:
        key, value = arg.split('=')
        parametros[key.lower()] = value

    # Validar los parametros recibidos
    if "path" not in parametros:
        print("Error: el parametro path es obligatorio para el comando rmdisk")
        return
    else:
        rmdisk(parametros)

def fdiskCom(argumentos):
    # Convertir los argumentos en un diccionario
    parametros = {}
    for arg in argumentos:
        key, value = arg.split('=')
        parametros[key.lower()] = value

    # Validar los parametros recibidos
    if "size" not in parametros or "path" not in parametros or "name" not in parametros:
        print("Error: los parametros size, path y name son obligatorios para el comando fdisk")
        return
    else:
        fdisk(parametros)   

def mountCom(argumentos):
    global particion_actual
    # Convertir los argumentos en un diccionario
    parametros = {}
    for arg in argumentos:
        key, value = arg.split('=')
        parametros[key.lower()] = value

    # Validar los parametros recibidos
    if "path" not in parametros or "name" not in parametros:
        print("Error: los parametros path y name son obligatorios para el comando mount")
        return
    else:
        particion_actual = parametros['name'].replace(' ', '')
        mount(parametros, particiones_montadas)
        
def unmountCom(argumentos):
    # Convertir los argumentos en un diccionario
    parametros = {}
    for arg in argumentos:
        key, value = arg.split('=')
        parametros[key.lower()] = value

    # Validar los parametros recibidos
    if "id" not in parametros:
        print("Error: el parametro id es obligatorio para el comando unmount")
        return
    else:
        unmount(parametros, particiones_montadas)

def mkfsCom(argumentos):
    # Convertir los argumentos en un diccionario
    parametros = {}
    for arg in argumentos:
        key, value = arg.split('=')
        parametros[key.lower()] = value
    
    # Validar los parametros recibidos
    if "id" not in parametros:
        print("Error: el parametro id es obligatorio para el comando mkfs")
        return
    else:
        mkfs(parametros, particiones_montadas,usuarios)

def loginCom(argumentos):
    global usuarios, particion_actual
    # Convertir los argumentos en un diccionario
    parametros = {}
    for arg in argumentos:
        key, value = arg.split('=')
        parametros[key.lower()] = value
    
    # Validar los parametros recibidos
    if "user" not in parametros or "pass" not in parametros or "id" not in parametros:
        print("Error: los parametros user, pass e id son obligatorios para el comando login")
        return
    else:
        login_result = login(parametros, particiones_montadas)
        for particion in particiones_montadas:
            if particion_actual == particion[list(particion.keys())[0]]['name']:
                n_id = particion[list(particion.keys())[0]]['id']
        
        bitMap('login '+str(parametros), particiones_montadas, n_id)
        if login_result is None:
            print("Error: la funcion login no devolvio valores validos")
            return
        usuarios, particion_actual = login_result

def logoutCom(argumentos):
    global usuarios
    logout_users = {}
    if usuarios != None:
        logout_users = usuarios
        usuarios = None
    else:
        print("No hay usuarios logueados")
    result = ('logout', logout_users)
    return result    

def mkgrpCom(argumentos):
    # Convertir los argumentos en un diccionario
    parametros = {}
    for arg in argumentos:
        key, value = arg.split('=')
        parametros[key.lower()] = value
    
    # Validar los parametros recibidos
    if "name" not in parametros:
        print("Error: el parametro name es obligatorio para el comando mkgrp")
        return
    else:
        if usuarios != None and usuarios['username'] == 'root':
            mkgrp(parametros, particiones_montadas, particion_actual)
            bitMap('mkgrp '+str(parametros), particiones_montadas, particion_actual)
        else:
            print("No hay usuarios logueados")

def rmgrpCom(argumentos):
    # Convertir los argumentos en un diccionario
    parametros = {}
    for arg in argumentos:
        key, value = arg.split('=')
        parametros[key.lower()] = value
    
    # Validar los parametros recibidos
    if "name" not in parametros:
        print("Error: el parametro name es obligatorio para el comando rmgrp")
        return
    else:
        if usuarios != None and usuarios['username'] == 'root':
            rmgrp(parametros, particiones_montadas, particion_actual)
            bitMap('rmgrp '+str(parametros), particiones_montadas, particion_actual)
        else:
            print("No hay usuarios logueados")

def mkusrCom(argumentos):
    # Convertir los argumentos en un diccionario
    parametros = {}
    for arg in argumentos:
        key, value = arg.split('=')
        parametros[key.lower()] = value
    
    # Validar los parametros recibidos
    if "user" not in parametros or "pass" not in parametros or "grp" not in parametros:
        print("Error: los parametros user, pass y grp son obligatorios para el comando mkusr")
        return
    else:
        if usuarios != None and usuarios['username'] == 'root':
            mkusr(parametros, particiones_montadas, particion_actual)
            bitMap('mkusr '+str(parametros), particiones_montadas, particion_actual)
        else:
            print("No hay usuarios logueados")

def rmusrCom(argumentos):
    # Convertir los argumentos en un diccionario
    parametros = {}
    for arg in argumentos:
        key, value = arg.split('=')
        parametros[key.lower()] = value
    
    # Validar los parametros recibidos
    if "user" not in parametros:
        print("Error: el parametro user es obligatorio para el comando rmusr")
        return
    else:
        if usuarios is not None:
            rmusr(parametros, particiones_montadas, particion_actual)
            bitMap('rmusr '+str(parametros), particiones_montadas, particion_actual)
        else:
            print("No hay usuarios logueados")

def repCom(argumentos):
    # Convertir los argumentos en un diccionario
    parametros = {}
    for arg in argumentos:
        key, value = arg.split('=')
        parametros[key.lower()] = value
    
    # Validar los parametros recibidos
    if "name" not in parametros or "path" not in parametros or "id" not in parametros:
        print("Error: los parametros name, path e id son obligatorios para el comando rep")
        return
    else:
        if usuarios != None:
            rep(parametros, particiones_montadas, bytesMapD)
        else:
            print("No hay usuarios logueados")

def main():
    while True:
            command = input("Ingrese el comando: ")
            if command.startswith('exec'):
                execute(command)
            else:
                validar_comando(command)

if __name__ == "__main__":
    main()