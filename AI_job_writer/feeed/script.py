def list_available_models():
    import google.generativeai as genai
    import os
    genai.configure(api_key="AIzaSyC3u27HQYLxIkPBU8KKLdY-vPzAWPz8ltA")

    print("Available models that support generateContent:\n")
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            print(f"  {m.name}")

if __name__ == "__main__":
    list_available_models()