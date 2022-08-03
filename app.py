from google.cloud import storage
from google.cloud import speech
import logging
import os
from typing import Union

from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")

def form():
    return render_template("index.html")


@app.route("/", methods=["POST"])
def my_form_post():
    if request.method == 'POST':
           
        uploaded_file = request.files.get('file')

        if not uploaded_file:
            return 'No file uploaded.', 400

        # Create a Cloud Storage client.
        gcs = storage.Client()

        # Get the bucket that the file will be uploaded to.
        bucket = gcs.get_bucket("bb-transcriber-bucket")

        # Create a new blob and upload the file's content.
        blob = bucket.blob(uploaded_file.filename)

        blob.upload_from_string(
            uploaded_file.read(),
            content_type=uploaded_file.content_type
        )

        # Make the blob public. This is not necessary if the
        # entire bucket is public.
        # See https://cloud.google.com/storage/docs/access-control/making-data-public.
        #blob.make_public()

        # The public URL can be used to directly access the uploaded file via HTTP.
        gcs_uri= "gs://bb-transcriber-bucket/" + uploaded_file.filename
        render_template("index.html", recognition_output="Waiting for operation to complete...")
        output=transcribe_gcs(gcs_uri)
        delete_blob("bb-transcriber-bucket", uploaded_file.filename)
        
        #return render_template("index.html", recognition_output=output)
    

@app.errorhandler(500)
def server_error(e: Union[Exception, int]) -> str:
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500      
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# Python program to translate
# speech to text and text to speech

def transcribe_gcs(gcs_uri):
    """Asynchronously transcribes the audio file specified by the gcs_uri."""

    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(uri=gcs_uri)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.AMR,
        sample_rate_hertz=8000,
        language_code="en-CA",
    )
    #save to GCS after removing extension from uri and add new .txt extension
    outputConfig = speech.TranscriptOutputConfig(gcs_uri = gcs_uri[0:-4] + ".txt")

    long_running_recognize_request = speech.LongRunningRecognizeRequest(config=config, audio=audio, output_config=outputConfig)

    print("Waiting for operation to complete...")
    operation = client.long_running_recognize(long_running_recognize_request)
    response = operation.result(timeout=6000)
    
    transcript = ''
    
    # Each result is for a consecutive portion of the audio. Iterate through
    # them to get the transcripts for the entire audio file.
    for result in response.results:
        # The first alternative is the most likely one for this portion.
        transcript += result.alternatives[0].transcript        
    
    render_template("index.html", recognition_output = transcript)
    return transcript
    
def delete_blob(bucket_name, blob_name):
    """Deletes a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)

    #blob.delete()