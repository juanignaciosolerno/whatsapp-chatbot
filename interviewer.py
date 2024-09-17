from flask import Flask, request, redirect, abort

from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from functools import wraps

import time
import os
from dotenv import load_dotenv

import gspread
import googlemaps





# Load environmental variables from .env
load_dotenv()

# Initialize a Gspread Client
credentials_dict = {
    "type": os.getenv("TYPE"),
    "project_id": os.getenv("PROJECT_ID"),
    "private_key_id": os.getenv("PRIVATE_KEY_ID"),
    "private_key": os.getenv("PRIVATE_KEY"),
    "client_email": os.getenv("CLIENT_EMAIL"),
    "client_id": os.getenv("CLIENT_ID"),
    "auth_uri": os.getenv("AUTH_URI"),
    "token_uri": os.getenv("TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL")
    }

credentials_path=".service_account.json"

gc = gspread.service_account(filename=credentials_path)
if gc:
    print('Gspread Client ready.')

key = "1a7NbCtYgD7okcroJmhV07yB3ZqA_FqzGdcvPWBZGg0E"
sh = gc.open_by_key(key)
worksheet = 1
worksheet = sh.get_worksheet(worksheet)
if worksheet:
    print("Gsheet fetched.")

header = worksheet.get("A1:Z1")[0]
header = [int(col_name) for col_name in header]
if header:
    print('Worksheet colum names fetched.')

# Initialize a Twilio Client
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')

# Initialize a Google Maps Client
gmaps = googlemaps.Client(key=os.environ.get("GOOGLE_API_KEY"))
if gmaps:
    print("GoogleMaps Client ready")

app = Flask(__name__)

# Hello World endpoint
@app.route("/")
def hello():
  return "<p>This is Pensamiento Lateral ChatBot!</p>"


# Respond with a simple message with MessagingResponse object 
@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    """Respond to incoming calls with a simple text message."""
    # Start our TwiML response
    resp = MessagingResponse()
    # Add a message
    resp.message("The Robots are coming! Head for the hills!")
    return str(resp)


# Validate Twilio Requests with a RequestValidator object
def validate_twilio_request(f):
    """Validates that incoming requests genuinely originated from Twilio"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Create an instance of the RequestValidator class
        validator = RequestValidator(os.environ.get('TWILIO_AUTH_TOKEN'))

        # Validate the request using its URL, POST data,
        # and X-TWILIO-SIGNATURE header
        request_valid = validator.validate(
            request.url,
            request.form,
            request.headers.get('X-TWILIO-SIGNATURE', ''))

        # Continue processing the request if it's valid, return a 403 error if
        # it's not
        if request_valid:
            return f(*args, **kwargs)
        else:
            return abort(403)
    return decorated_function


# Respond with a simple message with MessagingResponse object if it is a valid Twilio request
@app.route('/message', methods=['POST'])
#@validate_twilio_request
def incoming_message():
    """Twilio Messaging URL - receives incoming messages from Twilio"""
    # Create a new TwiML response
    resp = MessagingResponse()
    # <Message> a text back to the person who texted us
    body = "Your text to me was {0} characters long. Webhooks are neat :)" \
        .format(len(request.values['Body']))
    resp.message(body)
    # Return the TwiML
    return str(resp)






### ENTREVISTA ###

# Preguntas predefinidas
questions = [
    #"Hola, soy Vecinal, un asistente virtual. Te escribo porque estoy evaluando los servicios de la Muni en el barrio. ¿Cómo estás?",
    "¿Tienes unos minutos para responder algunas preguntas?",
    "¿Del 1 al 10 cuan satisfecho/a estás con los servicios que ofrece la municipalidad en tu barrio?",
    "¿Podrías decirme por qué le diste ese puntaje?",
    "¿Del 1 al 10, cómo calificarías la limpieza y la recolección de residuos en el barrio?",
    "¿Qué aspectos te parecen los más importantes a mejorar con respecto a esto último?",
    "¿Del 1 al 10 cómo calificarías el estado de las calles y las veredas?",
    "¿Qué aspectos te parecen los más importantes a mejorar con respecto a esto último?",
    "¿Con respecto a la seguridad, hay algo que te preocupa o te parece importante mejorar?",
    "¿En qué aspectos del barrio te parece que debería trabajarse?",
    "¿Hay algo que esperas que la Municipalidad o el intendente haga en el barrio?",
    "Te agradezco mucho por compartirme tus opiniones. ¿Hay algo más que te gustaría decirme?",
    "Te molestaría decirme en qué barrio, localidad y provincia vives?",
]




# Función para obtener la pregunta actual
def fetch_question(question_index):
    if 0 <= question_index < len(questions):
        return questions[question_index]
    else:
        return "Perdón, pero tu entrevista ya ha terminado. Gracias nuevamente!"

# Función para obtener la data de localización
def get_location_data(location_string):
    geocode_result = gmaps.geocode(location_string)
    if geocode_result:
        lat = geocode_result[0]['geometry']['location']['lat']
        long = geocode_result[0]['geometry']['location']['lat']
        location_type = geocode_result[0]['geometry']['location_type']
        formatted_address = geocode_result[0]['formatted_address']
    location_data = {
        'lat':lat,
        'long':long,
        'location_type':location_type,
        'formatted_address':formatted_address
        }
    return location_data


# Estado global
status_template = {
    "current_system_msg_index": 0,
    "current_user_msg_index": 0,
    "user_messages": {},
    "start_time": None,
    "end_time": None,
    "database_update": False
}

status = status_template




@app.route('/interview', methods=['POST'])
def interview():
    print("Interview endpoint alcanzado")

    # Start TwiML response
    resp = MessagingResponse()
    
    # Obtener el índice del último mensaje recibido o asignarle 0
    current_user_msg_index = status.get("current_user_msg_index", 0)
    print(f'Mensaje del usuario recibido: índice asignado {current_user_msg_index}')

    # Obtener el mensaje entrante del usuario
    user_msg = request.values.get('Body', '').strip()
    print(f'Mensaje del usuario: {user_msg}')

    user_phone_number = request.values.get('From', '').strip()
    print(user_phone_number)

    # Si el mensaje está vacío, devolver una respuesta de error
    if not user_msg:
        return 'Hola! No encuentro ningún texto en tu mensaje, me has querido decir algo?'
    
    # Almacenar el mensaje del usuario en status
    status["user_messages"][current_user_msg_index] = user_msg

    # Inicializar el tiempo de inicio si es la primera respuesta
    if current_user_msg_index == 0:
        status['start_time'] = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
        print(f"Momento de inicio de la entrevista: {status['start_time']}")

    # Obtener el índice del último mensaje del sistema
    current_system_msg_index = status.get("current_system_msg_index", 0)

    # Verificar si la entrevista ha terminado
    if current_system_msg_index == len(questions):

        if status['database_update'] == False:

            # Obtener el resultado de la entrevista
            interview_result = status['user_messages']

            # Crear una lista para almacenar las respuestas
            interview_list = [interview_result.get(i, "") for i in range(len(questions))]

            # Obtener la información geográfica
            location_data = get_location_data(user_msg)
            interview_list.append(location_data['lat'])
            interview_list.append(location_data['long'])
            interview_list.append(location_data['location_type'])
            interview_list.append(location_data['formatted_address'])

            
            # Agregar el tiempo de inicio y finalización de la entrevista
            interview_list.append(status['start_time'])

            status['end_time'] = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
            interview_list.append(status['end_time'])
            print(f"Momento de cierre de la entrevista: {status['end_time']}")

            # Obtener el número de teléfono del entrevistado
            interview_list.append(user_phone_number)

            # Convertir la lista en una tupla e ingresarla en la base de datos
            interview_tuple = tuple(interview_list)

            # Asume que `worksheet` está definido y está apuntando a la hoja de cálculo adecuada
            worksheet.append_row(interview_tuple)
            print('Entrevista ingresada en la base de datos')

            # Actualiza el estado de ingreso de la fila en la base de datos
            status['database_update'] = True

            # Asignar el mensaje de respuesta al Objeto de Respuesta Twilio
            resp.message("Muchas gracias por tu tiempo y por ayudar a mejorar el barrio. ¡Que tengas un lindo día!")
            return str(resp)
        
        else:
            # Asignar el mensaje de respuesta al Objeto de Respuesta Twilio
            resp.message("Gracias nuevamente, tu entrevista ya terminó")
            return str(resp)
    
    # Obtener la siguiente pregunta y devolverla
    system_msg = fetch_question(current_system_msg_index)
    resp.message(system_msg)
    print(f'Mensaje del sistema enviado: índice {current_system_msg_index}')
    print(f'{system_msg}')
    
    # Incrementar el índice del sistema y del usuario después de enviar la pregunta
    status["current_system_msg_index"] += 1
    status["current_user_msg_index"] += 1

    return str(resp)





if __name__ == "__main__":
    app.run(debug=True)
