# Importando la libreria os para manipular archivos
import os

# Función para eliminar un disco
def rmdisk(params):
    # Obtiene el nombre del archivo a eliminar
    filename = params.get('path')

    # Verifica que se haya proporcionado el parámetro obligatorio
    if not filename:
        print("-path parameter is mandatory!")
        return

    # Obtiene la ruta completa al archivo
    current_directory = os.getcwd()
    full_path = os.path.join(current_directory, 'discos_test', filename)

    # Si el archivo no existe, muestra un error
    if not os.path.exists(full_path):
        print(f"Error: El archivo {full_path} no existe.")
        return

    # Pide confirmación al usuario antes de la eliminación
    respuesta = input(f"¿Está seguro de que desea eliminar {full_path}? (yes/no): ").strip().lower()

    if respuesta == 'yes':
        os.remove(full_path)
        print(f"El disco {full_path} se eliminó correctamente.")
    elif respuesta == 'no':
        print("Eliminación del disco cancelada.")
    else:
        print("Respuesta inválida. El disco no se eliminó.")