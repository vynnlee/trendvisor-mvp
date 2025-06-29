#!/usr/bin/env python3
"""
Trendvisor Data Collection Tool
Accepts a keyword and saves a dummy list of scraped reviews to an output file.
"""
import json
import os
import sys
import time
import random

def crawl_reviews(product_name: str, task_id: str) -> str:
    """
    Simulates crawling reviews for a given product.
    In a real implementation, this would involve web scraping.
    
    Args:
        product_name: The name of the product to crawl reviews for.
        task_id: The unique ID for the current task.

    Returns:
        The file path to the saved data.
    """
    # Simulate network latency and processing time
    time.sleep(random.randint(3, 6))

    # Generate more realistic mock data
    mock_reviews = []
    for i in range(random.randint(50, 150)):
        is_positive = random.random() > 0.2
        rating = random.randint(4, 5) if is_positive else random.randint(1, 3)
        review_text = (
            f"This is a {'great' if is_positive else 'terrible'} product! "
            f"I {'love' if is_positive else 'hate'} the new {product_name}. "
            f"Gave it a {rating} star rating. Review number {i+1}."
        )
        mock_reviews.append({
            "id": f"review_{i+1}",
            "rating": rating,
            "text": review_text
        })
    
    # --- File Output ---
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    
    file_path = os.path.join(output_dir, f"{task_id}_reviews.json")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(mock_reviews, f, indent=4, ensure_ascii=False)
        
    return file_path

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python crawl_reviews.py <product_name> <task_id>", file=sys.stderr)
        sys.exit(1)
        
    product_name_arg = sys.argv[1]
    task_id_arg = sys.argv[2]
    
    try:
        # This script should only print the final file path to stdout on success.
        # All other logging or status updates are handled by the agent calling this tool.
        final_path = crawl_reviews(product_name=product_name_arg, task_id=task_id_arg)
        print(final_path)
    except Exception as e:
        print(f"An error occurred in crawl_reviews: {e}", file=sys.stderr)
        sys.exit(1) 