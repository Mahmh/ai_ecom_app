from sklearn.preprocessing import LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Optional
import os, pandas as pd, numpy as np
from src.lib.data.constants import TRANSFORMED_DATA_PATH, TOP_K_RECOMMENDED
from src.lib.data.db import engine, ProductData
from src.lib.utils.db import get_all_products

_retrieve = lambda query: pd.DataFrame(pd.read_sql(query, engine))

def _load_transformed_data() -> Optional[pd.DataFrame]:
    """Loads the transformed data for recommendations"""
    return pd.read_csv(TRANSFORMED_DATA_PATH) if os.path.exists(TRANSFORMED_DATA_PATH) else None


def _load_label_encoders() -> Dict[str, LabelEncoder]:
    """Loads label encoders for consistent transformations"""
    users_df = _retrieve("SELECT username FROM users")
    products_df = _retrieve("SELECT category, owner FROM products")
    return {
        'username': LabelEncoder().fit(users_df['username'].fillna("Unknown")),
        'category': LabelEncoder().fit(products_df['category'].fillna("Unknown")),
        'owner': LabelEncoder().fit(products_df['owner'].fillna("Unknown"))
    }


def _recommend_similar_items(df: pd.DataFrame, target_index: int, top_k: int = TOP_K_RECOMMENDED) -> List[int]:
    """Generates recommendations based on cosine similarity"""
    target_vector = df.iloc[target_index].values.reshape(1, -1)
    all_vectors = df.values
    similarities = cosine_similarity(target_vector, all_vectors)[0]

    # Filter unique product IDs
    seen_product_ids = set()
    recommendations = []
    similar_indices = np.argsort(similarities)[::-1][1:]
    
    for index in similar_indices:
        product_id = df.loc[index, 'product_id']
        if product_id not in seen_product_ids:
            recommendations.append(product_id)
            seen_product_ids.add(product_id)
        if len(recommendations) >= top_k:
            break
    return recommendations


def _recommend_for_username(df: pd.DataFrame, username: str, label_encoders: Dict[str, LabelEncoder], top_k: int = TOP_K_RECOMMENDED) -> List[int]:
    """Recommends unique product IDs for a given username"""
    encoded_username = label_encoders['username'].transform([username])[0]
    target_index = df[df['username'] == encoded_username].index[0]
    recommendations = _recommend_similar_items(df, target_index, top_k)
    return recommendations


def recommend_products(username: str, top_k: int = TOP_K_RECOMMENDED) -> List[ProductData]:
    """Returns recommendations for a given username"""
    transformed_df = _load_transformed_data()

    if transformed_df is None:
        print("Transformed data not available. Run the pipeline first.")
        return []

    label_encoders = _load_label_encoders()
    product_ids = _recommend_for_username(transformed_df, username, label_encoders, top_k)
    recommended = []
    for product_id in product_ids:
        try: recommended.append(get_all_products(product_id=int(product_id))[0])
        except IndexError: continue
    return recommended