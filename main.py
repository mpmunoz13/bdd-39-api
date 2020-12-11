from flask import Flask, json, request
from pymongo import MongoClient

USER = "grupo39"
PASS = "grupo39"
DATABASE = "grupo39"

URL = f"mongodb://{USER}:{PASS}@gray.ing.puc.cl/{DATABASE}?authSource=admin"
client = MongoClient(URL)

MESSAGE_KEYS = ['message', 'sender',
            'receptant', 'lat', 'long', 'date']

FILTRAR = ['desired', 'required','forbidden','userId']
FILTRAR_mapa = ['userId', 'f1','f2','desired']

# Base de datos del grupo
db = client["grupo39"]

# Seleccionamos la collección de usuarios
usuarios = db.usuarios
mensajes = db.mensajes

#Iniciamos la aplicación de flask
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route("/")
def home():
    '''
    Página de inicio
    '''
    return "<h1>¡Hola!</h1>"


@app.route("/messages/<int:mid>")
def get_message(mid):
    messages = list(db.mensajes.find({"mid":mid}, {"_id": 0}))
    if messages == []:
        return json.jsonify({"Error":"Mensaje no existe"})
    return json.jsonify(messages)

@app.route("/messages/", methods = ['GET'])
def get_message_cruzado():
    ids = request.args.to_dict()
    if ids == {}:
        messages = list(db.mensajes.find({}, {"_id": 0}))
        return json.jsonify(messages)
    id1 = int(ids['id1'])
    id2 = int(ids['id2'])
    user = list(db.usuarios.find({"uid":id1}, {"_id": 0}))
    if user == []:
        return json.jsonify({"Error":f"Usuario {id1} no existe"})
    user = list(db.usuarios.find({"uid":id2}, {"_id": 0}))
    if user == []:
        return json.jsonify({"Error":f"Usuario {id2} no existe"})
    messages1 = list(db.mensajes.find({"sender":id1, "receptant":id2},{"_id": 0}))
    messages2 = list(db.mensajes.find({"sender":id2, "receptant":id1},{"_id": 0}))
    if messages1 + messages2 == []:
        return json.jsonify({"Error":"No hay mensajes entre usuarios"})
    return json.jsonify(messages1 + messages2)

@app.route("/users")
def get_users():
    users = list(db.usuarios.find({}, {"_id": 0}))
    return json.jsonify(users)

@app.route("/encontrarid/<string:nombre>/<string:apellido>/<int:edad>")
def get_id():
    users = list(db.usuarios.find({"name":nombre+" "+apellido, "age":edad}, {"_id": 0}))
    return json.jsonify(users["uid"])

@app.route("/users/emitidos/<int:uid>")
def get_user_e(uid):
    user = list(db.usuarios.find({"uid":uid}, {"_id": 0}))
    if user == []:
        return json.jsonify({"Error":f"Usuario {uid} no existe"})
    mensaje = list(db.mensajes.find({"sender":uid}, {"_id": 0}))
    return json.jsonify(mensaje)

@app.route("/users/recibidos/<int:uid>")
def get_user_r(uid):
    user = list(db.usuarios.find({"uid":uid}, {"_id": 0}))
    if user == []:
        return json.jsonify({"Error":f"Usuario {uid} no existe"})
    mensaje = list(db.mensajes.find({"receptant":uid}, {"_id": 0}))
    return json.jsonify(mensaje)

'''
DELETE
'''

@app.route("/message/<int:mid>", methods=['DELETE'])
def delete_message(mid):
    messages = list(db.mensajes.find({"mid":mid}, {"_id": 0}))
    if messages == []:
        return json.jsonify({"Error":"Mensaje no existe"})
    mensajes.remove({"mid": mid})
    return json.jsonify({"success": True})

'''
POST
'''

@app.route("/messages", methods=['POST'])
def create_message():
    for key in request.json.keys():
        if key not in MESSAGE_KEYS:
            return json.jsonify({"Error":f'Key {key} invalida'})
    for key in MESSAGE_KEYS:
        if key not in request.json.keys():
            return json.jsonify({"Error":f'Key {key} faltante'})
    data = {key: request.json[key] for key in MESSAGE_KEYS}
    print(data)
    if type(data["message"]) == str and type(data["sender"]) == int and \
       type(data["receptant"]) == int and type(data["lat"]) == float and \
       type(data["date"]) == str: 
        existe_sender = list(db.usuarios.find({"uid":data["sender"]}, {"_id": 0}))
        existe_receptant = list(db.usuarios.find({"uid":data["receptant"]}, {"_id": 0}))
        if existe_receptant != [] and existe_sender != []:
            max = list(db.mensajes.find({},{"_id": 0}).sort([("mid", -1)]).limit(1))
            id = int(max[0]["mid"])
            # id del primero que no existe = id + 1 
            data["mid"] = id+1
            result = mensajes.insert_one(data)
            return json.jsonify({"success": True})
        else:
            return json.jsonify({"Error":"Sender o Receptant no existe"})
    else:
        return json.jsonify({"Error":"Tipos de datos no corresponden"})

@app.route("/text-search", methods=['GET'])
def filtrar_mensaje():
    try:
        for key in request.json.keys():
            if key not in FILTRAR:
                return json.jsonify({"Error":f'Key {key} invalida'})
        FILTRAR2 = []
        for key in request.json.keys():
            if request.json[key]!=[] and request.json[key]!=[""]:
                FILTRAR2.append(key)
        data = {key: request.json[key] for key in FILTRAR2}
        print(FILTRAR2)
        if FILTRAR2 == [] or (FILTRAR2 == ['userId'] and data['userId'] == 0):
            messages = list(db.mensajes.find({}, {"_id": 0}))
            return json.jsonify(messages)
        elif FILTRAR2 == ["forbidden"] or FILTRAR2 == ["forbidden",'userId'] or FILTRAR2 == ['userId',"forbidden"]:
            no = data['forbidden']
            mensajes_prohibidos = []
            for palabra in no:
                print("palabra", palabra)
                str_busqueda = "\"" + palabra + "\" "
                print(str_busqueda)
                mensajes_prohibidos += list(db.mensajes.find({"$text": {"$search":str_busqueda}},{"_id": 0}))
                print(mensajes_prohibidos)
            if 'userId' in FILTRAR2 and data['userId']!= 0:
                todos_messages = list(db.mensajes.find({"sender":data['userId']}, {"_id": 0}))
            else:
                todos_messages = list(db.mensajes.find({}, {"_id": 0}))
            mensajes_buenos = []
            for m in todos_messages:
                if m not in mensajes_prohibidos:
                    mensajes_buenos.append(m)
            return json.jsonify(mensajes_buenos)
                   
        elif FILTRAR2 == ['userId'] and data['userId'] != 0:
            user = list(db.usuarios.find({"uid":data['userId']}, {"_id": 0}))
            if user == []:
                return json.jsonify({"Error":f"Usuario {data['userId']} no existe"})
            mensaje = list(db.mensajes.find({"sender":data['userId']}, {"_id": 0}))
            return json.jsonify(mensaje)

        else:
            str_busqueda = ""
            if "desired" in FILTRAR2:
                desired = data['desired']
                for palabra in desired:
                    str_busqueda += palabra + " "
            if "required" in FILTRAR2:
                required = data['required']
                for palabra in required:
                    str_busqueda += "\"" + palabra + "\" "
            if "forbidden" in FILTRAR2:
                no = data['forbidden']
                for palabra in no:
                    str_busqueda += '-\"'+ palabra +'\" '
            print("str busqueda",str_busqueda)
            if data['userId'] != 0:
                try:
                    mensajes = list(db.mensajes.find({"$text": {"$search":str_busqueda},"sender":data["userId"]},{"_id": 0}))
                except Exception:
                    mensajes = list(db.mensajes.find({"$text": {"$search":str_busqueda}},{"_id": 0}))
                print("mensajes",mensajes)
            else:
                mensajes = list(db.mensajes.find({"$text": {"$search":str_busqueda}},{"_id": 0}))
            return json.jsonify(mensajes)
    except Exception as e:
        print(e)
        messages = list(db.mensajes.find({}, {"_id": 0}))
        return json.jsonify(messages)


@app.route("/mapa", methods=['GET'])
def filtrar_mensaje_mapa():
    for key in FILTRAR_mapa:
        if key not in request.json.keys():              
            return json.jsonify({"Error":f'Falta información'})
    data = {key: request.json[key] for key in FILTRAR_mapa}
    desired = data['desired']  
    f1 = data['f1'].split("-")
    f2 = data['f2'].split("-") 
    str_busqueda = ""   
    for palabra in desired:
        str_busqueda += palabra + " "
    mensajes = list(db.mensajes.find({"$text": {"$search":str_busqueda},"sender":data["userId"]},{"_id": 0}))
    mensajes += list(db.mensajes.find({"$text": {"$search":str_busqueda},"receptant":data["userId"]},{"_id": 0}))
    print("mensajes", mensajes)
    mensajes_fecha = []
    for m in mensajes:  
        fecha = m['date'].split("-")          
        if f1[0] < fecha[0] and f2[0] < fecha[0]:
            mensajes_fecha.append({'message': m["message"], 'lat':m['lat'], 'long': m['long']})
        elif f1[0] == fecha[0]:
            if f1[1]< fecha[1]:
                mensajes_fecha.append({'message': m["message"], 'lat':m['lat'], 'long': m['long']})
            elif f1[1] == fecha[1]:
                if f1[2] <= fecha[2]:
                    mensajes_fecha.append({'message': m["message"], 'lat':m['lat'], 'long': m['long']})
        elif f2[0] == fecha[0]:
            if f2[1] > fecha[1]:
                mensajes_fecha.append({'message': m["message"], 'lat':m['lat'], 'long': m['long']})
            elif f2[1] == fecha[1]:
                if f2[2] >= fecha[2]:
                    mensajes_fecha.append({'message': m["message"], 'lat':m['lat'], 'long': m['long']})
        print(mensajes_fecha)
    return json.jsonify(mensajes_fecha)




if __name__ == "__main__":
    app.run(debug=True, threaded=True, port=5000)
