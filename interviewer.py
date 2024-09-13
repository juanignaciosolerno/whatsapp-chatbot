from flask import Flask, request, redirect, abort
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from functools import wraps

import os

from dotenv import load_dotenv

# Load environmental variables from .env
load_dotenv()

app = Flask(__name__)

auth_token = os.environ.get('TWILIO_AUTH_TOKEN')

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


# Respond with a simple message with MessagingResponse object 
@app.route("/wp", methods=['GET', 'POST'])
def wp_reply():
    
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

### ENTREVISTA


# Preguntas predefinidas, 13 (indices 0-12)
questions = [
    "Hola, soy Vecinal, un asistente virtual. Te escribo porque estoy evaluando los servicios de la Muni en el barrio. ¿Cómo estás?",
    "¿Tienes unos minutos para responder algunas preguntas sobre tu experiencia con los servicios de la Muni?",
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
    "Muchas gracias por tu tiempo y por ayudar a mejorar el barrio. ¡Que tengas un lindo día!"
]


# Función para obtener la pregunta actual
def fetch_question(question_index):
    if question_index <= len(questions):
        return questions[question_index]
    else:
        return "Perdón, pero tu entrevista ya ha terminado. Gracias nuevamente!"


# Estado global (esto se debería manejar por sesión o en una base de datos para múltiples usuarios)
status = {
    "current_system_msg_index": 0,
    "current_user_msg_index": 0,
    "user_messages": {}
}


@app.route('/interview', methods=['POST'])
def interview():

    # Obtener el índice del último mensaje enviado o asignarle 0
    current_system_msg_index = status.get("current_system_msg_index", 0)

    # Obtener el índice del último mensaje recibido o asignarle 0
    current_user_msg_index = status.get("current_user_msg_index", 0)

    # Si el último mensaje ya fue enviado (mensaje de despedida), responder amablemente que la entrevista terminó
    if current_system_msg_index > len(questions):
        return "Perdón, pero tu entrevista ya ha terminado. Gracias nuevamente!"
    
    # Obtener el mensaje entrante del usuario
    user_msg = request.values.get('Body', '').strip()

    # Si el mensaje está vacío, devolver una respuesta de error
    if not user_msg:
        system_msg = 'Hola! No encuentro ningún texto en tu mensaje, me has querido decir algo?'
        return system_msg

    # Almacenar el mensaje del usuario
    status["user_messages"][current_user_msg_index] = user_msg

    # Obtener el mensaje del sistema que corresponde
    system_msg = fetch_question(current_system_msg_index)

    # Incrementar el índice del mensaje actual
    status["current_system_msg_index"] += 1

    return system_msg


if __name__ == "__main__":
    app.run(debug=True)






