from Admin_Discos.FDISK import fdisk
from Admin_Discos.MKDISK import mkdisk
from Admin_Discos.RMDISK import rmdisk
from Admin_Discos.MOUNT import mount
from Admin_Discos.UNMOUNT import unmount
import re

#Se definen las variables globales
particiones_montadas = []
usuarios = None
particion_actual = None

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
                if '#' not in line:
                    validar_comando(line.strip())
    except FileNotFoundError:
        print("Error: El archivo especificado no existe")

def validar_comando(comando):
    # Separar el comando y los argumentos
    comando_separado = comando.split('-')
    cmd = comando_separado[0].replace(' ', '').lower() # Obtenemos el comando
    # Verificar si es el comando mkdisk
    
    if cmd == "mkdisk":
        argumentos = comando_separado[1:] # Obtenemos los argumentos
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

    elif cmd == "rmdisk":
        argumentos = comando_separado[1:]
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

    elif cmd == "fdisk":
        argumentos = comando_separado[1:]
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

    elif cmd == "mount":
        argumentos = comando_separado[1:]
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
            mount(parametros, particiones_montadas)
    
    elif cmd == "unmount":
        argumentos = comando_separado[1:]
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

    elif cmd == "exit":
        exit()

    else:
        print("Error: comando no reconocido.")

def main():
    while True:
            command = input("Ingrese el comando: ")
            if command.startswith('execute'):
                execute(command)
            else:
                validar_comando(command)

if __name__ == "__main__":
    main()