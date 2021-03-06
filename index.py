from flask import Flask,request,jsonify,render_template
import os
import dialogflow
import requests
import json
import pusher

app = Flask(__name__)
 # initialize Pusher
pusher_client = pusher.Pusher(
        app_id=os.getenv('PUSHER_APP_ID'),
        key=os.getenv('PUSHER_KEY'),
        secret=os.getenv('PUSHER_SECRET'),
        cluster=os.getenv('PUSHER_CLUSTER'),
        ssl=True)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_song_detail', methods = ['POST'])
def get_song_detail():
    data = request.get_json(silent = True)
    song = data['queryResult']['parameters']['artist']['track']
    api_key = os.getenv('MUSIX_API_KEY')
    
    song_detail = requests.get('https://api.musixmatch.com/ws/1.1/matcher.lyrics.get?format=jsonp&callback=callback&q_track={}&q_artist={}&api_key={}').format(track,artist, api_key).content
    song_detail = json.loads(song_detail)
    response = """
        lyrics_id :{0}
        lyrics_body : {1}
        script_tracking_url : {2}
        pixel_tracking_url : {3}
    """.format(song_detail['lyrics_id'], song_detail['lyrics_body'],song_detail['script_tracking_url'],song_detail['pixel_tracking_url'] )
    
  
    
    reply = {
        "fulfillmentText" : response,
    }
    
    return jsonify(reply) 


def detect_intent_texts(project_id, session_id, text, language_code):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)
    
    if text:
        text_input = dialogflow.types.TextInput(
        text=text, language_code=language_code)
        query_input = dialogflow.types.QueryInput(text=text_input)
        response = session_client.detect_intent(
        session=session, query_input=query_input)
        
    return response.query_result.fulfillment_text


@app.route('/send_message', methods=['POST'])
def send_message():
    message = request.form['message']
    project_id = os.getenv('DIALOGFLOW_PROJECT_ID')
    fulfillment_text = detect_intent_texts(project_id, "unique", message, 'en')
    response_text = { "message":  fulfillment_text }

    socketId = request.form['socketId']
    pusher_client.trigger('MOJO', 'new_message', 
                             {'human_message': message, 'bot_message': fulfillment_text},
                             socketId)
    
    return jsonify(response_text)


        
if __name__ == "__main__":
    app.run()

