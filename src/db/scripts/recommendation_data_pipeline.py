"""Script that runs on the background to process interaction data, which will be utilized by the recommendation system"""
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sentence_transformers import SentenceTransformer
from typing import Dict, Tuple
from time import sleep
from datetime import datetime
import pandas as pd, numpy as np
from src.lib.data.constants import PIPELINE_INTERVAL, TRANSFORMED_DATA_PATH, EMBEDDER_FOR_RECOMMENDATION
from src.server.models.recommender import _retrieve

def extract_interaction_data() -> pd.DataFrame:
    """Extracts interaction data from the interactions table"""
    return _retrieve("""
        SELECT username, product_id, rating, sentiments, in_cart
        FROM interactions;
    """)


def transform_data(interactions_df: pd.DataFrame) -> Tuple[pd.DataFrame, StandardScaler, Dict[str, LabelEncoder]]:
    """Transforms the data: embeddings, scaling, and encoding"""
    # Step 1: Read user and product tables
    users_df = _retrieve("SELECT username, bio FROM users")
    products_df = _retrieve("SELECT product_id, name, description, price, category, owner FROM products")

    # Step 2: Merge data
    result_df = interactions_df.merge(users_df, on="username", how="left")
    result_df = result_df.merge(products_df, on="product_id", how="left")

    # Step 3: Text Embedding
    text_columns = ['bio', 'name', 'description']
    embedder = SentenceTransformer(EMBEDDER_FOR_RECOMMENDATION)

    def _embed_text(column: pd.Series) -> pd.Series:
        return column.fillna('').apply(lambda x: embedder.encode(x) if isinstance(x, str) else embedder.encode(''))

    for col in text_columns:
        result_df[col] = _embed_text(result_df[col])
        result_df[col] = result_df[col].apply(lambda x: np.array(x))

    # Step 4: Process sentiments column (sum the list)
    def _sum_sentiments(sentiments: any) -> float:
        return float(sum(sentiments)) if isinstance(sentiments, list) else 0.0

    result_df['sentiments'] = result_df['sentiments'].apply(_sum_sentiments)

    # Step 5: Scale continuous features
    scaler = StandardScaler()
    result_df['price'] = scaler.fit_transform(result_df[['price']])
    result_df['sentiments'] = scaler.fit_transform(result_df[['sentiments']])

    # Step 6: Label Encode discrete features
    label_encoders = {}
    for col in ['username', 'category', 'owner']:
        le = LabelEncoder()
        result_df[col] = le.fit_transform(result_df[col].fillna("Unknown"))
        label_encoders[col] = le

    # Step 7: Combine embeddings
    embedding_features = result_df[text_columns].apply(lambda x: np.concatenate(x.values), axis=1)

    transformed_df = pd.concat([
        result_df.drop(columns=text_columns), 
        pd.DataFrame(embedding_features.tolist())
    ], axis=1)
    return transformed_df, scaler, label_encoders


def save_transformed_data(df: pd.DataFrame) -> None:
    """Saves the transformed data to a CSV file."""
    df.to_csv(TRANSFORMED_DATA_PATH, index=False)


def main(run_once: bool = False) -> None:
    """Runs the pipeline in the background every 4 minutes"""
    print(f'[{datetime.now()}] Starting Recommendation Pipeline...')
    while True:
        try:
            print(f'[{datetime.now()}] Extracting data...')
            interactions_df = extract_interaction_data()

            print(f'[{datetime.now()}] Transforming data...')
            transformed_df = transform_data(interactions_df)[0]

            print(f'[{datetime.now()}] Saving transformed data...')
            save_transformed_data(transformed_df)

            print(f'[{datetime.now()}] Pipeline complete.')
            if run_once: break

            print(f'[{datetime.now()}] Sleeping for {PIPELINE_INTERVAL} seconds...')
            sleep(PIPELINE_INTERVAL)
        except KeyboardInterrupt:
            print(f'[{datetime.now()}] Stopping pipeline...')
            break


if __name__ == "__main__": main()