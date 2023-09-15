import struct
import os
from Discos.MBR import MBR
from Discos.EBR import EBR
from Estructuras.SUPER_BLOCK import Superblock
from Estructuras.INODE import Inode
from Estructuras.FOLDER_BLOCK import FolderBlock
from Estructuras.FILE_BLOCK import FileBlock
from Estructuras.POINTER_BLOCK import PointerBlock
from prettytable import PrettyTable


def rep(parametros, particiones_montadas,mapa_de_bytes): 
    global codigo_para_graphviz 
    global current_id
    name = parametros.get('name', '')
    id = parametros.get('id', None).replace(' ', '')
    print(f"*'{id}'*")
    if id == None:
        print("Error: La id es necesaria.")
        return
    partition = None
    for partition_dict in particiones_montadas:
        if id in partition_dict:
            partition = partition_dict[id]
            break
    if not partition:
        print(f"Error: La particion en el id: {id} no existe.")
        return
    # Retrieve partition details.
    path = partition['path']
    inicio = partition['inicio']
    size = partition['size']
    full_path = path
    if not os.path.exists(full_path):
        print(f"Error: El archivo en la ruta: {full_path} no existe.")
        return
    with open(full_path, "rb+") as file:
        if name == 'mbr':
            graphviz_code = ''
            current_id = 0
            file.seek(0)
            mbr = MBR.unpack(file.read(MBR.SIZE))
            object_type, pt, lista,index = imprimir(mbr,0)
            totalMBR, id = prettytable_to_html_string('mbr', pt, lista,0, inicio)         
            particiones = mbr.particiones
            for partition in particiones:
                if partition.type == 'E' and partition.status == 1:
                    next = partition.byte_inicio
                    while next != -1:
                        file.seek(next)
                        try:
                            ebr = EBR.unpack(file.read(EBR.SIZE))
                        except Exception as e:
                            print(f"Se ha producido un error durante la lectura del archivo: {str(e)}")
                        object_type, pt, lista,index = imprimir(ebr,next)
                        total, id = prettytable_to_html_string('ebr', pt, lista,next, inicio)
                        graphviz_code+="\n"+total
                        next = ebr.next

            with open('REP_MBR_EBR.dot', 'w') as f:
                combined_code = f'digraph G {{\n{totalMBR}\n{graphviz_code}\n}}'
                f.write(combined_code)
            generar_imagen('REP_MBR_EBR.dot')

        elif name == 'disk':
            rows = []
            file.seek(0)
            mbr = MBR.unpack(file.read(MBR.SIZE))
            rows.append('\n<TD>MBR</TD>')
            partitions = mbr.particiones
            for partition in partitions:
                print(str(partition))
                if partition.type == 'P' and partition.status == 1:
                    rows.append(f'\n<TD>primaria: {partition.name}</TD>')
                elif partition.type == 'E' and partition.status == 1:
                    extended_rows = []
                    next = partition.byte_inicio
                    while next != -1:
                        file.seek(next)
                        ebr = EBR.unpack(file.read(EBR.SIZE))
                        extended_rows.append(f'\n   <TD>ebr: {ebr.name}</TD>')
                        if ebr.next != -1:
                            extended_rows.append(f'\n   <TD>logica: {ebr.name}</TD>')
                        if ebr.next != -1 and ebr.next < (next + EBR.SIZE+ebr.actual_size):
                            extended_rows.append(f'\n   <TD>LIBRE</TD>')
                        next = ebr.next
                    extended_content = "".join(extended_rows)
                    rows.append(f'\n<TD><TABLE BORDER="2"><TR><TD colspan="10">extendida</TD></TR><TR>{extended_content}</TR></TABLE></TD>')
                elif partition.status == 0:
                    rows.append(f'\n<TD>LIBRE</TD>')
            graphviz_code = f'''digraph G {{
                node [shape=none];
                disk [label=<
                <TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0">
                <TR><TD colspan="5">{id}</TD></TR>
                <TR>{"".join(rows)}</TR>
                </TABLE>
                >];
                }}
                            '''
            
            with open('REP_DISK.dot', 'w') as f:
                    f.write(f'{graphviz_code}')         
            generar_imagen('REP_DISK.dot')                    
    
        elif name == 'bm_inode':
            file.seek(inicio)
            superblock = Superblock.unpack(file.read(Superblock.SIZE))
            codigo_para_graphviz = ''
            for n in mapa_de_bytes:
                codigo_para_graphviz += f'\n{n[0]}'
            for n in range(len(mapa_de_bytes)):
                codigo_para_graphviz += f'\ninode_{n} -> inode_{n+1}'     
            with open('REP_BM_INODE.dot', 'w') as f:
                    f.write(f'digraph G {{\n{codigo_para_graphviz}\n}}')
            generar_imagen('REP_BM_INODE.dot')

        elif name == 'bm_blocK':
            file.seek(inicio)
            superblock = Superblock.unpack(file.read(Superblock.SIZE))
            codigo_para_graphviz = ''
            for n in mapa_de_bytes:
                codigo_para_graphviz += f'\n{n[1]}'
            for n in range(len(mapa_de_bytes)):
                codigo_para_graphviz += f'\nblock_{n} -> block_{n+1}' 
            with open('REP_BM_BLOCK.dot', 'w') as f:
                    f.write(f'digraph G {{\n{codigo_para_graphviz}\n}}')
            generar_imagen('REP_BM_BLOCK.dot')

        elif name == 'inode':
            current_id = 0
            lista_graphviz = []
            cantidad_inodos = superblock.s_inodes_count
            FORMAT = f'{cantidad_inodos}s'
            SIZE = struct.calcsize(FORMAT)
            file.seek(superblock.s_bm_inode_start)
            bitmap_inodos = struct.unpack(FORMAT, file.read(SIZE))[0].decode('utf-8')
            for i,n in enumerate(bitmap_inodos):
                print(n)
                if n == '1':
                    inicio = superblock.s_inode_start + i*Inode.SIZE
                    file.seek(inicio)
                    object = Inode.unpack(file.read(Inode.SIZE))
                    object_type, pt, lista,index = imprimir_como_antes(object,inicio)
                    total, id = prettytable_to_html_string(object_type, pt, lista,inicio, object)
                    codigo_para_graphviz += f'\n =============== EL ID ES {id} DEL OBJETO {object_type} CON EL INDICE {inicio} =============== '
                    codigo_para_graphviz += "\n"+total
            for n in range(current_id):
                codigo_para_graphviz += f'\n{n} -> {n+1}'
            with open('REP_INODE.dot', 'w') as f:
                    f.write(f'digraph G {{\n{codigo_para_graphviz}\n}}')
            generar_imagen('REP_INODE.dot')

        elif name == 'block':
            current_id = 0
            lista_graphviz = []
            cantidad_bloques = superblock.s_blocks_count
            FORMAT = f'{cantidad_bloques}s'
            SIZE = struct.calcsize(FORMAT)
            file.seek(superblock.s_bm_block_start)
            bitmap_bloques = struct.unpack(FORMAT, file.read(SIZE))[0].decode('utf-8')
            for i,n in enumerate(bitmap_bloques):
                print(n)
                if n == '1':
                    inicio = superblock.s_block_start + i*64
                    file.seek(inicio)
                    try:
                        object = FolderBlock.unpack(file.read(FolderBlock.SIZE))
                    except:
                        pass
                    try:
                        object = FileBlock.unpack(file.read(FileBlock.SIZE))
                    except:
                        pass
                    object_type, pt, lista,index = imprimir(object,inicio)
                    total, id = prettytable_to_html_string_para_bloques(object_type, pt, lista,inicio, object)
                    codigo_para_graphviz += f'\n ===============  EL ID ES {id} DEL OBJETO {object_type} CON EL INDICE {inicio} =============== '
                    codigo_para_graphviz += "\n"+total
            for n in range(current_id):
                codigo_para_graphviz += f'\n{n} -> {n+1}'
            with open('REP_BLOCK.dot', 'w') as f:
                    f.write(f'digraph G {{\n{codigo_para_graphviz}\n}}')


        elif name == 'sb':
            file.seek(inicio)
            superblock = Superblock.unpack(file.read(Superblock.SIZE))
            table = PrettyTable(['Attribute', 'Value'])
            attributes = vars(superblock)
            lista = None
            for attr, value in attributes.items():
                table.add_row([attr, value])
            print(table)
            total,_= prettytable_to_html_string("sb", table, lista,inicio, inicio)
            with open('REP_SB.dot', 'w') as f:
                    f.write(f'digraph G {{\n{total}\n}}')
            generar_imagen('REP_SB.dot')

def generar_imagen(graphviz_file):
    # Generar imagen a partir del archivo de texto con el código de Graphviz.
    image_file = os.path.splitext(graphviz_file)[0] + '.png'
    os.system(f'dot -Tpng {graphviz_file} -o {image_file}')

    # Verificar si la imagen se creó correctamente.
    if os.path.exists(image_file):
        print(f'Imagen creada: {image_file}')
    else:
        print(f'Error al crear la imagen: {image_file}')

COLORS = {'Inode': 'lightblue', 'Superblock': '#E0E0E0', 'FolderBlock': '#FFCC00', 'FileBlock': 'green', 'sb': 'orange',  'Content': '#FFCC00','mbr': 'orange','ebr': 'orange'}
def imprimir(obj,index):
    object_type = type(obj).__name__
    if object_type == 'FileBlock':
        obj.b_content = obj.b_content.replace('\x00', '')
    if object_type == 'FolderBlock':
        for n in obj.b_content:
            n.b_name = n.b_name.replace('\x00', '')
    table = PrettyTable(['Attribute', 'Value'])
    attributes = vars(obj)
    lista = None
    for attr, value in attributes.items():
        if not isinstance(value, list):
            table.add_row([attr, value])
        else:
            lista = value
    return object_type, table, lista,index


def imprimir_como_antes(obj,index):
    object_type = type(obj).__name__
    if object_type == 'FileBlock':
        obj.b_content = obj.b_content.replace('\x00', '')
    if object_type == 'FolderBlock':
        for n in obj.b_content:
            n.b_name = n.b_name.replace('\x00', '')
    table = PrettyTable(['Attribute', 'Value'])
    attributes = vars(obj)
    lista = None
    for attr, value in attributes.items():
        table.add_row([attr, value])
        
    return object_type, table, lista,index
current_id = 0

def get_next_id():
    global current_id
    current_id += 1
    return current_id


def prettytable_to_html_string(object_type, pt, lista,index, object):
    global current_id
    get_next_id()
    header_node = f'subgraph cluster_{object_type}{index} {"{"} label = "{object_type}{index}" style = filled fillcolor = "{COLORS[object_type]}"'
    nodo_tabla = f'\n{current_id} [label='
    html_string = '''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">\n'''
    html_string += "  <TR>\n"
    for field in pt._field_names:
        html_string += f"    <TD>{field}</TD>\n"
    html_string += "  </TR>\n"
    for row in pt._rows:
        html_string += "  <TR>\n"
        for cell in row:
            cell = str(cell).replace("\n", "<BR/>")
            html_string += f"    <TD>{cell}</TD>\n"
        html_string += "  </TR>\n"

    html_string += "</TABLE>> shape=box];\n"
    bloques = f'\nnode [shape=record];\nbloques{current_id} [label='
    if lista is not None:
        bloques += '"{'
        for i,n in enumerate(lista):
            bloques += f"<content{i}> {n.__str__()} | "
        bloques += '\n}"];'
    if lista is None:
        total = header_node + nodo_tabla + html_string + "}"
    else:
        total = header_node + nodo_tabla + html_string +  bloques + "}" 
    if object_type=='FolderBlock':
        total = header_node +  bloques + "}"

    return total,current_id

def prettytable_to_html_string_para_bloques(object_type, pt, lista,index, object):
    global current_id
    get_next_id()
    header_node = f'subgraph cluster_{object_type}{index} {"{"} label = "{object_type}{index}" style = filled fillcolor = "{COLORS[object_type]}"'
    nodo_tabla = f'\n{current_id} [label='
    html_string = '''<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">\n'''
    html_string += "  <TR>\n"
    for field in pt._field_names:
        html_string += f"    <TD>{field}</TD>\n"
    html_string += "  </TR>\n"
    for row in pt._rows:
        html_string += "  <TR>\n"
        for cell in row:
            cell = str(cell).replace("\n", "<BR/>")
            html_string += f"    <TD>{cell}</TD>\n"
        html_string += "  </TR>\n"

    html_string += "</TABLE>> shape=box];\n"
    bloques = f'\nnode [shape=record];\n{current_id} [label='
    if lista is not None:
        bloques += '"{'
        for i,n in enumerate(lista):
            bloques += f"<content{i}> {n.__str__()} | "
        bloques += '\n}"];'
    if lista is None:
        total = header_node + nodo_tabla + html_string + "}"
    else:
        total = header_node + nodo_tabla + html_string +  bloques + "}" 
    if object_type=='FolderBlock':
        total = header_node +  bloques + "}"

    return total,current_id

codigo_para_graphviz = ''

