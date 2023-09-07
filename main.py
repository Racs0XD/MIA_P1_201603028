from Admin_Discos.FDISK import fdisk
from Admin_Discos.MKDISK import mkdisk
from Admin_Discos.RMDISK import rmdisk
import re


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

    else:
        print("Error: comando no reconocido.")


def main():
    while True:
            command = input("Ingrese el comando: ")
            validar_comando(command)
    

if __name__ == "__main__":
    main()
