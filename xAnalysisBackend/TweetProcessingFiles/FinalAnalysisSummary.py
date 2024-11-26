import pandas as pd
from sentence_transformers import SentenceTransformer, util
from groq import Groq
from TweetProcessor.models import Tweet  # Assuming your Tweet model is here

# Load the embedding model globally
model = SentenceTransformer('all-MiniLM-L6-v2')  # Replace with your model if different

import torch
from sentence_transformers import SentenceTransformer, util
from TweetProcessor.models import Tweet
import pandas as pd

# Load the model globally
model = SentenceTransformer('all-MiniLM-L6-v2')

def retrieve_texts(query, top_k=10):
    """
    Retrieves the top texts from the database based on semantic similarity and keyword relevance.

    Args:
        query (str): The search query.
        top_k (int): Number of top texts to retrieve.

    Returns:
        list: A list of the top `top_k` texts.
    """
    # Fetch tweets from the database
    tweets = Tweet.objects.all().values('text', 'embeddings')
    df = pd.DataFrame(tweets)

    if df.empty:
        print("No tweets found in the database.")
        return []

    # Encode the query into a tensor
    query_embedding = model.encode(query, convert_to_tensor=True)

    # Convert stored embeddings into PyTorch tensors
    doc_embeddings = torch.stack([torch.tensor(embedding) for embedding in df['embeddings']])

    # Compute cosine similarities for semantic relevance
    cosine_scores = util.cos_sim(query_embedding, doc_embeddings)[0]

    # Keyword matching: create a flag for keyword presence in the text
    df['keyword_match'] = df['text'].apply(lambda x: query.lower() in x.lower())

    # Combine cosine scores and keyword match into a DataFrame
    scores_df = pd.DataFrame({
        'text': df['text'],
        'semantic_score': cosine_scores.tolist(),
        'keyword_match': df['keyword_match']
    })

    # Adjust scores for keyword matches
    scores_df.loc[scores_df['keyword_match'], 'semantic_score'] += 0.5

    # Sort by the adjusted scores and select the top_k entries
    top_texts = scores_df.sort_values(by='semantic_score', ascending=False).head(top_k)['text'].tolist()

    return top_texts


def generate_summary_from_texts(texts, api_key):
    """
    Generates a summary from the provided texts using the Groq API.

    Args:
        texts (list): A list of text strings to summarize.
        api_key (str): API key for the Groq service.

    Returns:
        str: A summary of the texts.
    """
    if not texts:
        return "No relevant texts found to generate a summary."

    full_text = " ".join(texts)
    client = Groq(api_key=api_key)

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "user", "content": "write the main points from these tweets in around 150 words use a * at the beginning of each point" + full_text}
        ],
        model="llama3-8b-8192"
    )
    summary = chat_completion.choices[0].message.content
    return summary


def generate_summary(query, api_key, top_k=10):
    """
    Generates a summary for tweets relevant to a given query.

    Args:
        query (str): The search query.
        api_key (str): API key for the Groq service.
        top_k (int): Number of top texts to retrieve.

    Returns:
        str: A summary of the top tweets matching the query.
    """
    # Retrieve relevant texts
    texts = retrieve_texts(query, top_k=top_k)

    # Generate summary from the texts
    summary = generate_summary_from_texts(texts, api_key)

    return summary
