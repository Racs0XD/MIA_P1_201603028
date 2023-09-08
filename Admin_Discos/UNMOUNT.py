# Define la función para desmontar una partición
def unmount(params, mounted_partitions):
    # Obtiene el ID de la partición a desmontar
    id_to_unmount = params.get('id').replace(' ', '')
    
    # Busca el diccionario de la partición en la lista de particiones montadas y la elimina de ser encontrada
    for index, partition_dict in enumerate(mounted_partitions):
        if id_to_unmount in partition_dict:
            mounted_partitions.pop(index)
            print(f"La partición {id_to_unmount} fue desmontada exitosamente.")
            return
    # Si la partición no se encuentra en la lista de particiones montadas, retorna un error
    print(f"Error: La partición {id_to_unmount} no existe.")