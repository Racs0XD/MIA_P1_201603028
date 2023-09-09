#Funcion para cargar usuarios y grupos desde un contenido de string en una estructura de diccionario
def load_users_from_content(content):
    lines = content.split("\n")
    data_structure = {}
    # Recorre cada linea del contenido
    for line in lines:
        if line == '':
            continue
        parts = line.strip().split(",")
        if parts[1] == 'G':  # Grupo
            if parts[0] != '0':
                data_structure[parts[2]] = {}
        else:  # Usuario
            if parts[0] != '0':
                group_name = parts[2]
                user_data = {
                    'id': parts[0],
                    'username': parts[3],
                    'password': parts[4]
                }
                if group_name in data_structure:
                    data_structure[group_name][parts[3]] = user_data
                else:
                    data_structure[group_name] = {parts[3]: user_data}

    return data_structure

#Funcion para analizar usuarios
def parse_users(texto):
    lines = texto.split('\n')
    users_list = []
    
    # Almacén temporal de grupos
    groups = {}
    grupo_actual = ''
    # Recorre cada linea del texto
    for line in lines:
        parts = line.split(',')
        
        # Grupo
        if len(parts) == 3 and parts[1] == 'G'and parts[0]!='0':
            groups[parts[2]] = parts[0]
            grupo_actual = parts[2]
        
        # Usuario
        elif len(parts) == 5 and parts[1] == 'U' and parts[0]!='0':
            if grupo_actual == parts[2]:
                user_data = {
                    parts[3]: {
                        'id': parts[0],
                        'username': parts[3],
                        'password': parts[4],
                        'group': parts[2]
                    }
                }
                users_list.append(user_data)
            
    return users_list

#Funcion para obtener un usuario si está autenticado
def get_user_if_authenticated(usuarios, user, password):
    print(f'buscando a {user} con password {password} en {usuarios}')
    # Recorre cada usuario en la lista de usuarios
    for user_data in usuarios:
        if user in user_data:
            # Usuario encontrado
            if user_data[user]['password'] == password:
                # La contraseña coincide
                return user_data[user]
    # El usuario no se encontró o la contraseña no coincide
    return None

#Funcion para obtener el id de un grupo por su nombre
def get_id_by_group(grupos, group):
    for item in grupos:
        user_data = item[next(iter(item))]
        if user_data['group'] == group:
            return user_data['id']
    return None  # Si el grupo no se encontró

#Funcion para extraer grupos activos
def extract_active_groups(text):
    lines = text.split("\n")
    groups = []
    # Recorre cada linea del texto
    for line in lines:
        if line == '':
            continue
        parts = line.split(",")
        # Verificar si el registro es para un grupo y está activo
        if parts[1] == 'G' and parts[0] != '0':
            groups.append({'groupname': parts[2], 'id': int(parts[0])})
    return groups

#Funcion para obtener el id de un grupo por su nombre
def get_group_id(group_name, groups):
    for group in groups:
        if group['groupname'] == group_name:
            return group['id']
    return None