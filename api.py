import time
import random
import requests
from requests.exceptions import Timeout, ConnectionError

def make_api_request_with_retry(url, headers, max_retries=3, base_timeout=30):
    """Make API request with exponential backoff retry logic"""
    retries = 0
    while retries <= max_retries:
        try:
            if retries > 0:
                # Log retry attempt
                print(f"Retry attempt {retries}/{max_retries} for URL: {url}")
                
            # Add jitter to prevent thundering herd problem
            timeout = base_timeout * (1 + random.random())
            
            # Make the request with timeout
            response = requests.get(url, headers=headers, timeout=timeout)
            
            # Check for server errors (5xx) which should be retried
            if 500 <= response.status_code < 600:
                print(f"Server error: {response.status_code}, retrying...")
                retries += 1
                # Exponential backoff with jitter
                wait_time = (2 ** retries) + random.uniform(0, 1)
                time.sleep(wait_time)
                continue
                
            # Handle rate limiting (429)
            if response.status_code == 429:
                # Check for Retry-After header
                retry_after = response.headers.get('Retry-After')
                wait_time = int(retry_after) if retry_after and retry_after.isdigit() else (2 ** retries) + 5
                print(f"Rate limited. Waiting for {wait_time} seconds...")
                time.sleep(wait_time)
                retries += 1
                continue
                
            # For successful or client error responses, return immediately
            return response
            
        except (ConnectionError, Timeout) as e:
            # Only retry on connection issues or timeouts
            retries += 1
            if retries > max_retries:
                print(f"Max retries ({max_retries}) exceeded. Last error: {str(e)}")
                raise
            
            # Exponential backoff with jitter
            wait_time = (2 ** retries) + random.uniform(0, 1)
            print(f"Request failed with {str(e)}. Retrying in {wait_time:.2f} seconds...")
            time.sleep(wait_time)
    
    # This should not be reached due to the raise in the except block
    return None