import azure.functions as func
import logging
from textblob import TextBlob
from azure.storage.blob import BlobServiceClient
import json,os, matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd
import io, base64




app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.function_name("get_messages")
@app.route(route="get_messages")
@app.blob_output(arg_name = "outputBlob", path = "text-messages/{rand-guid}.txt", connection = "AzureWebJobsStorage")

def get_messages(req: func.HttpRequest, outputBlob : func.Out[str]) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    text = req.params.get('message')
    if not text:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            text = req_body.get('text')

    if text:
        # Save the text to the output blob
        outputBlob.set(text)
        logging.info(f"Text '{text}' saved to the blob!")
        return func.HttpResponse(f"Text '{text}' saved to the blob!", status_code=200)

    else:
        return func.HttpResponse(
             "This HTTP triggered function is used to perform sentiment analysis, just asdd ?message= 'your message'.",
             status_code=200
        )


@app.blob_trigger(arg_name="myblob", path="text-messages",connection="AzureWebJobsStorage")
@app.blob_output(arg_name="outputBlob", path="records/{rand-guid}.txt", connection="AzureWebJobsStorage")
def analyze_sentiment(myblob: func.InputStream, outputBlob : func.Out[str]) -> func.HttpResponse:
    logging.info(f" Starting to analyze the sentiment of the blob {myblob.name}")
    try:
        message = myblob.read().decode('utf-8')
        logging.info(f"Message: {message}")
        # Perform sentiment analysis
        blob = TextBlob(message)
        sentiment = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        logging.info(f"Sentiment: {sentiment}")
        
        # Display the sentiment
        if sentiment > 0:
            sentiment_label = "Positive"
        elif sentiment == 0:
            sentiment_label = "Neutral"
        else:
            sentiment_label = "Negative"
        # Save the sentiment analysis details to an output blob
        results = {
            "message": message,
            "sentiment": sentiment,
            "sentiment_label": sentiment_label,
            "subjectivity": subjectivity,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        outputBlob.set(json.dumps(results, indent=2))
        logging.info(f"Sentiment analysis details are saved to the blob!")
        # Display the sentiment
        logging.info(f"Done Analysis")
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(f"Error: {e}", status_code=500)
    return None

@app.function_name("update_visualization")
@app.blob_trigger(arg_name="myblob", path="records", connection="AzureWebJobsStorage")
@app.blob_output(arg_name="vsBlob", path="visualization/sentiment_analysis.png", connection="AzureWebJobsStorage")
def update_visualization(myblob: func.InputStream, vsBlob: func.Out[str]) -> None:
    logging.info(f"Updating the sentiment visualization with the new blob {myblob.name}")
    # connect to the blob storage
    try:
        blob_service_client = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
        container_client = blob_service_client.get_container_client("records")
        
        # Get the list of blobs in the container
        blobs = container_client.list_blobs()
        
        # Get the sentiment details from the blobs
        data_points = []
        
        for blob in blobs:
            blob_client = container_client.get_blob_client(blob)
            content = blob_client.download_blob().readall()
            data = json.loads(content)
            
            # Add error checking and logging
            logging.info(f"Processing blob data: {data}")
            
            data_points.append({
                'sentiment': float(data.get('sentiment', 0)), 
                'subjectivity': float(data.get('subjectivity', 0)),
                'message': data.get('message', '')
            })

        # Create a data frame from the sentiment details
        df = pd.DataFrame(data_points)
        
        # Generate a visualization (Scatter plot)
        plt.figure(figsize=(10, 6))
        scatter = plt.scatter(
            df['sentiment'], 
            df['subjectivity'],
            c=df['sentiment'],  
            cmap='viridis', 
            alpha=0.6,
            s=100  
        )
        
        plt.title("Sentiment Analysis Results", fontsize=14, pad=20)
        plt.xlabel("Sentiment Score", fontsize=12)
        plt.ylabel("Subjectivity Score", fontsize=12)
        
        # Add reference lines
        plt.axhline(y=0.5, color='gray', linestyle='--', alpha=0.3)
        plt.axvline(x=0, color='gray', linestyle='--', alpha=0.3)
        
        plt.grid(True, alpha=0.3)
        plt.colorbar(scatter, label='Sentiment Score')
        
        # Save the visualization
        plot_buf = io.BytesIO()
        plt.savefig(plot_buf, format='png', bbox_inches='tight', dpi=300)
        plot_buf.seek(0)
        vsBlob.set(plot_buf.getvalue())  # Save the plot directly to the blob
        plt.close()
        
        logging.info("Visualization updated successfully!")
        
    except Exception as e:
        logging.error(f"Error updating visualization: {str(e)}")
        raise  # Re-raise the exception for the Azure Functions runtime to handle

    return


@app.route(route="view_visualization", auth_level=func.AuthLevel.ANONYMOUS)
def view_visualization(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Connect to blob storage
        blob_service_client = BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])
        
        # Get the records from the container to calculate statistics
        rec_container = blob_service_client.get_container_client("records")
        data_points = []

        # Collect all records
        for blob in rec_container.list_blobs():
            blob_client = rec_container.get_blob_client(blob)
            content = blob_client.download_blob().readall()
            data = json.loads(content)
            data_points.append({
                'sentiment': float(data.get('sentiment', 0)),
                'subjectivity': float(data.get('subjectivity', 0)),
                'message': data.get('message', ''),
                'timestamp': data.get('timestamp', '')
            })

        # Create a DataFrame only if we have data
        if data_points:
            df = pd.DataFrame(data_points)
            stats = {
                'total_messages': len(df),
                'average_sentiment': float(df['sentiment'].mean()),
                'positive_count': int((df['sentiment'] > 0).sum()),
                'negative_count': int((df['sentiment'] < 0).sum()),
                'neutral_count': int((df['sentiment'] == 0).sum()),
                'average_subjectivity': float(df['subjectivity'].mean())
            }
        else:
            stats = {
                'total_messages': 0,
                'average_sentiment': 0.0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'average_subjectivity': 0.0
            }

        # Try to get the visualization image if it exists
        vis_container = blob_service_client.get_container_client("visualization")
        try:
            blob_client = vis_container.get_blob_client("sentiment_analysis.png")
            image = blob_client.download_blob().readall()
            encoded_image = base64.b64encode(image).decode('utf-8')
            has_visualization = True
        except Exception as e:
            logging.info("No visualization found yet")
            has_visualization = False

        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sentiment Analysis Visualization</title>
            <meta http-equiv="refresh" content="5">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 20px;
                }}
                .stat-box {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 4px;
                    text-align: center;
                }}
                .stat-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .stat-label {{
                    color: #7f8c8d;
                    margin-top: 5px;
                }}
                .visualization {{
                    text-align: center;
                    margin-top: 20px;
                    padding: 20px;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                }}
                .update-time {{
                    text-align: right;
                    color: #666;
                    font-size: 0.9em;
                    margin-top: 10px;
                }}
                h1 {{
                    color: #2c3e50;
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .message {{
                    text-align: center;
                    padding: 20px;
                    color: #666;
                    font-style: italic;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Real-time Sentiment Analysis Dashboard</h1>
                
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-value">{stats['total_messages']}</div>
                        <div class="stat-label">Total Messages</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{stats['average_sentiment']:.3f}</div>
                        <div class="stat-label">Average Sentiment</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{stats['positive_count']}</div>
                        <div class="stat-label">Positive Messages</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{stats['negative_count']}</div>
                        <div class="stat-label">Negative Messages</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{stats['neutral_count']}</div>
                        <div class="stat-label">Neutral Messages</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{stats['average_subjectivity']:.3f}</div>
                        <div class="stat-label">Average Subjectivity</div>
                    </div>
                </div>
                
                <div class="visualization">
                    {f'<img src="data:image/png;base64,{encoded_image}" style="max-width: 100%; height: auto;" alt="Sentiment Analysis Visualization"/>' if has_visualization else '<div class="message">Waiting for data... Please submit some messages for analysis.</div>'}
                </div>
                
                <div class="update-time">
                    Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                </div>
            </div>
        </body>
        </html>
        """
        
        return func.HttpResponse(
            html_content,
            mimetype="text/html",
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"Error displaying visualization: {str(e)}")
        return func.HttpResponse(
            f"""
            <html>
                <body>
                    <h1>Error</h1>
                    <p>An error occurred while displaying the visualization: {str(e)}</p>
                    <p>Please make sure you have submitted some messages for analysis.</p>
                </body>
            </html>
            """,
            mimetype="text/html",
            status_code=500
        )
'''
Disclaimer: The visualisaton code was been generated with the help of Claude Opus AI in terms of the HTML and CSS code.
However, the Python code was written by me.
'''