# Importando la libreria os para manipular archivos
import os

# Función para eliminar un disco
def rmdisk(params):
    # Obtiene el nombre del archivo a eliminar
    path_param = params.get('path').replace('"', '')
    partes = path_param.rsplit('/', 1)
    nombre_archivo = partes[1]
    ruta_archivo = partes[0]
    
    # Obtener el path completo del archivo
    full_path = os.path.join(path_param)
    # Si el archivo no existe, muestra un error
    if not os.path.exists(full_path):
        print(f"Error: El archivo {full_path} no existe.")
        return

    

    while True:
        # Pide confirmación al usuario antes de la eliminación
        respuesta = input(f"¿Desea eliminar {nombre_archivo}? (y/n): ").strip().lower()
        if respuesta == 'y':
            os.remove(full_path)
            print(f"El disco {nombre_archivo} se eliminó correctamente.")
            return
        elif respuesta == 'n':
            print("Se cancelo la acción.")
            return
        else:
            print("Respuesta inválida. Seleccione una opción correcta.")