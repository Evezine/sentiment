import streamlit as st
from pymongo import MongoClient
from textblob import TextBlob
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import csv
from io import StringIO

# MongoDB connection setup
client = MongoClient("mongodb://localhost:27017/")
db = client["feedback_db"]
feedback_collection = db["feedback"]

# Function to analyze sentiment
def analyze_sentiment(feedback_text):
    blob = TextBlob(feedback_text)
    polarity = blob.sentiment.polarity
    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    else:
        return "Neutral"

# Streamlit UI
st.title("Feedback Sentiment Analyzer")

# Input form for user feedback
st.header("Submit Feedback")
user_name = st.text_input("Your Name")
feedback_text = st.text_area("Your Feedback")

if st.button("Submit"):
    if user_name and feedback_text:
        sentiment = analyze_sentiment(feedback_text)
        feedback = {
            "user_name": user_name,
            "feedback_text": feedback_text,
            "sentiment": sentiment,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        feedback_collection.insert_one(feedback)
        st.success(f"Feedback submitted! Sentiment: {sentiment}")
    else:
        st.error("Please provide both name and feedback.")

# Display all feedback
st.header("View Submitted Feedback")
feedback_list = list(feedback_collection.find({}))

if feedback_list:
    for feedback in feedback_list:
        st.subheader(feedback["user_name"])
        st.write(f"Feedback: {feedback['feedback_text']}")
        st.write(f"Sentiment: {feedback['sentiment']}")
        st.write(f"Submitted on: {feedback['timestamp']}")
        st.write("---")
else:
    st.info("No feedback submitted yet.")

# Sentiment Distribution Visualization
st.header("Sentiment Distribution")
positive_count = feedback_collection.count_documents({"sentiment": "Positive"})
neutral_count = feedback_collection.count_documents({"sentiment": "Neutral"})
negative_count = feedback_collection.count_documents({"sentiment": "Negative"})

if positive_count or neutral_count or negative_count:
    sentiments = ["Positive", "Neutral", "Negative"]
    counts = [positive_count, neutral_count, negative_count]

    fig, ax = plt.subplots()
    ax.pie(counts, labels=sentiments, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)
else:
    st.info("No feedback data available for sentiment distribution.")

# Search Feedback by Keyword
st.header("Search Feedback")
search_query = st.text_input("Enter a keyword to search feedback:")

if search_query:
    search_results = feedback_collection.find({"feedback_text": {"$regex": search_query, "$options": "i"}})
    st.write(f"Showing results for '{search_query}':")

    for feedback in search_results:
        st.subheader(feedback["user_name"])
        st.write(f"Feedback: {feedback['feedback_text']}")
        st.write(f"Sentiment: {feedback['sentiment']}")
        st.write(f"Submitted on: {feedback['timestamp']}")
        st.write("---")
else:
    st.info("Enter a keyword to search feedback.")

# Display Feedback Trends Over Time
st.header("Feedback Trend Over Time")

feedbacks = list(feedback_collection.find({}, {"timestamp": 1, "_id": 0}))

if feedbacks:
    df = pd.DataFrame(feedbacks)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    feedback_counts = df.groupby('date').size().reset_index(name='counts')

    st.line_chart(feedback_counts.set_index('date'))
else:
    st.info("No feedback data available for trend analysis.")

# Export Feedback to CSV
st.header("Export Feedback")

if st.button("Export to CSV"):
    feedbacks = list(feedback_collection.find({}, {"_id": 0}))

    if feedbacks:
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=feedbacks[0].keys())
        writer.writeheader()
        writer.writerows(feedbacks)

        st.download_button(
            label="Download CSV",
            data=output.getvalue(),
            file_name='feedback.csv',
            mime='text/csv'
        )
    else:
        st.info("No feedback to export.")

# Option to delete all feedback
if st.button("Delete All Feedback"):
    feedback_collection.delete_many({})
    st.warning("All feedback deleted.")
