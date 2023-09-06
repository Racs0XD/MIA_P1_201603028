from Admin_Discos.FDISK import fdisk
from Admin_Discos.MKDISK import mkdisk
from Admin_Discos.RMDISK import rmdisk
import re

# Expresiones regulares para parsear los comandos
MKDISK_RE = re.compile(r'mkdisk\s*(-\w+)\s*=\s*(\S+)\s*(-\w+)\s*=\s*(\S+)?\s*(-\w+)\s*=\s*(\S+)?\s*')
RMDISK_RE = re.compile(r'rmdisk\s*(-\w+)\s*=\s*(\S+)\s*')
FDISK_RE = re.compile(r'fdisk\s*(-\w+)\s*=\s*(\S+)\s*(-\w+)\s*=\s*(\S+)\s*(-\w+)\s*=\s*(\S+)\s*(-\w+)\s*=\s*(\S+)?\s*(-\w+)\s*=\s*(\S+)?\s*(-\w+)\s*=\s*(\S+)?\s*(-\w+)\s*=\s*(\S+)?\s*')

# Función para parsear el comando y sus argumentos
def parse_input(input_str):
    # Seleccionar la expresión regular correspondiente según el comando
    if input_str.startswith("mkdisk"):
        command_re = MKDISK_RE
    elif input_str.startswith("rmdisk"):
        command_re = RMDISK_RE
    elif input_str.startswith("fdisk"):
        command_re = FDISK_RE
    else:
        raise CommandError("Comando desconocido")

    # Parsear la entrada utilizando la expresión regular
    match = command_re.search(input_str)
    if not match:
        raise CommandError("Entrada invalida")

    # Extraer los argumentos del comando
    args = {}
    for i in range(1, match.lastindex + 1):
        arg_name = match.group(i)[1:]
        arg_value = match.group(i + 1)
        args[arg_name] = arg_value

    return args

# Función para ejecutar el comando correspondiente
def run_command(args):
    command_name = list(args.keys())[0]

    if command_name == "mkdisk":
        command = mkdisk(args)
    elif command_name == "rmdisk":
        command = rmdisk(args)
    elif command_name == "fdisk":
        command = fdisk(args)
    else:
        raise CommandError("Comando desconocido")

    command.execute()

# Clase para manejar errores de comando
class CommandError(Exception):
    pass

# Bucle principal que lee los comandos desde la consola y los ejecuta
while True:
    try:
        # Leer entrada del usuario
        input_str = input("Ingrese un comando: ")

        # Parsear la entrada y ejecutar el comando correspondiente
        args = parse_input(input_str)
        run_command(args)
    except CommandError as e:
        # Mostrar errores de comando
        print(str(e))
    except Exception as e:
        # Mostrar otros errores
        print("Error desconocido:", str(e))