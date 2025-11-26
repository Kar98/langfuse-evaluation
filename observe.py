import os
import sys
from google import genai
from google.genai.errors import APIError
from langfuse import Langfuse, get_client, observe

# --- Configuration ---
# Set your API key as an environment variable (e.g., GEMINI_API_KEY or GOOGLE_API_KEY).
# NOTE: Do NOT hardcode your API key directly in this file for production use.
MODEL_NAME = "gemini-2.5-flash"

# --- Langfuse Configuration ---
# IMPORTANT: You must set these environment variables for Langfuse to work:
# LANGFUSE_PUBLIC_KEY
# LANGFUSE_SECRET_KEY
# LANGFUSE_HOST (Optional, defaults to https://cloud.langfuse.com)
LANGFUSE_HOST = "http://localhost:3000"

langfuse = get_client()
 
# Verify connection, do not use in production as this is a synchronous call
if langfuse.auth_check():
    print("Langfuse client is authenticated and ready!")
else:
    print("Authentication failed. Please check your credentials and host.")

def get_api_key():
    """Tries to retrieve the Gemini API key from environment variables."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    return api_key

@observe()
def main():
    """Initializes the client and requests content from the Gemini API, with Langfuse tracing."""
    print("--- Gemini API Query Tool with Langfuse Tracing ---")

    # 1. Check for API Key
    if not get_api_key():
        print("ERROR: Gemini API key not found. Please set the GEMINI_API_KEY or GOOGLE_API_KEY.")
        sys.exit(1)

    # 2. Initialize the Gemini Client
    try:
        client = genai.Client()
    except Exception as e:
        print(f"ERROR: Could not initialize Gemini client. Details: {e}")
        sys.exit(1)

    # 3. Initialize Langfuse
    
    print(f"Model: {MODEL_NAME}")
    
    # 4. Get user prompt
    print("\n----------------------------------------------------")
    print("Enter your prompt (or press Enter to use the default prompt):")
    
    user_input = input("Prompt > ")
    prompt = user_input.strip()
    
    print(f"\nSending prompt to model...")
    print(f"Prompt: '{prompt}'")
    
    generation = None
    
    # 5. Call the Gemini API, wrapped in a Langfuse trace
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )
        

        # 6. Display the response
        print("\n--- Model Response ---")
        print(response.text)
        print("----------------------")

        # 7. Update the Langfuse generation with the results and usage data
        if generation:
            generation.update(
                output=response.text,
                prompt_token_count=response.usage_metadata.prompt_token_count,
                completion_token_count=response.usage_metadata.candidates_token_count
            )

        # Optional: Print metadata
        if response.usage_metadata:
             print("\n--- Usage Metadata ---")
             print(f"Input Tokens: {response.usage_metadata.prompt_token_count}")
             print(f"Output Tokens: {response.usage_metadata.candidates_token_count}")
             print("----------------------")

    except APIError as e:
        print(f"\nAPI Error: An error occurred during the API call. Details: {e}")
        if generation:
             # Log the error in Langfuse
             generation.update(status_message=f"API Error: {e}", level="ERROR")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        if generation:
             # Log the error in Langfuse
             generation.update(status_message=f"Unexpected Error: {e}", level="ERROR")
    finally:
        # 8. Ensure Langfuse data is sent before exiting
        if langfuse:
            print("\nFlushing Langfuse data...")
            langfuse.flush()
            print("Trace sent successfully to Langfuse.")

    return user_input, response.text

if __name__ == "__main__":
    main()
    