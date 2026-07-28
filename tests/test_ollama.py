"""
Test script to verify Ollama is working correctly
"""
import os
import time
from dotenv import load_dotenv

load_dotenv()

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def test_ollama_connection():
    """Test if Ollama server is reachable"""
    print_header("Testing Ollama Connection")
    
    import requests
    
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print(f"✅ Ollama server is running at {ollama_url}")
            
            data = response.json()
            models = data.get("models", [])
            
            if models:
                print(f"\n📦 Installed models:")
                for model in models:
                    name = model.get("name", "unknown")
                    size = model.get("size", 0) / (1024**3)  # Convert to GB
                    print(f"   • {name} ({size:.2f} GB)")
            else:
                print("\n⚠️  No models installed!")
                print("   Run: ollama pull llama3.2")
            
            return True
        else:
            print(f"❌ Ollama server returned status {response.status_code}")
            return False
            
    except requests.ConnectionError:
        print(f"❌ Cannot connect to Ollama at {ollama_url}")
        print("\n💡 Solutions:")
        print("   1. Start Ollama: ollama serve")
        print("   2. Check if Ollama is installed")
        print("   3. Verify OLLAMA_URL in .env")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_text_generation():
    """Test basic text generation"""
    print_header("Testing Text Generation")
    
    from llm import generate_text
    
    print("Sending test prompt to Ollama...")
    print("Prompt: 'Say hello in one sentence.'")
    
    start_time = time.time()
    response = generate_text("Say hello in one sentence.", temperature=0.7)
    elapsed = time.time() - start_time
    
    if response.startswith("[ERROR]"):
        print(f"\n❌ Generation failed:")
        print(f"   {response}")
        return False
    else:
        print(f"\n✅ Generation successful! ({elapsed:.2f}s)")
        print(f"\nResponse:")
        print(f"   {response}")
        return True

def test_json_generation():
    """Test JSON generation"""
    print_header("Testing JSON Generation")
    
    from llm import generate_json
    
    print("Sending test prompt for JSON output...")
    print('Prompt: \'Return JSON with keys "status" and "message"\'')
    
    start_time = time.time()
    response = generate_json(
        'Return a JSON object with two keys: "status" set to "ok" and "message" set to "test successful"',
        temperature=0.3
    )
    elapsed = time.time() - start_time
    
    if "_raw" in response and response["_raw"].startswith("[ERROR]"):
        print(f"\n❌ Generation failed:")
        print(f"   {response['_raw']}")
        return False
    elif "_raw" in response:
        print(f"\n⚠️  JSON parsing failed, but got response ({elapsed:.2f}s)")
        print(f"   Raw: {response['_raw'][:100]}...")
        return False
    else:
        print(f"\n✅ JSON generation successful! ({elapsed:.2f}s)")
        print(f"\nParsed JSON:")
        import json
        print(f"   {json.dumps(response, indent=2)}")
        return True

def test_email_generation():
    """Test email generation (like the actual app)"""
    print_header("Testing Email Generation (Real Use Case)")
    
    from llm import generate_text
    
    prompt = """You are an expert B2B sales email writer.
Write a short sales email (2-3 sentences) for:
- Customer: John Doe at Acme Corp
- Product: SalesAI - AI-powered sales automation

Start directly with "Subject:" - no preamble."""
    
    print("Generating sample sales email...")
    
    start_time = time.time()
    response = generate_text(prompt, temperature=0.8)
    elapsed = time.time() - start_time
    
    if response.startswith("[ERROR]"):
        print(f"\n❌ Generation failed:")
        print(f"   {response}")
        return False
    else:
        print(f"\n✅ Email generated successfully! ({elapsed:.2f}s)")
        print(f"\nGenerated Email:")
        print("-" * 60)
        print(response)
        print("-" * 60)
        return True

def main():
    print("\n" + "🔍 SalesAI Ollama Test Suite".center(60))
    
    results = []
    
    # Test 1: Connection
    results.append(("Connection", test_ollama_connection()))
    
    if not results[0][1]:
        print("\n❌ Cannot proceed without Ollama connection.")
        print("\n💡 Start Ollama first: ollama serve")
        return
    
    # Test 2: Text Generation
    results.append(("Text Generation", test_text_generation()))
    
    # Test 3: JSON Generation
    results.append(("JSON Generation", test_json_generation()))
    
    # Test 4: Email Generation
    results.append(("Email Generation", test_email_generation()))
    
    # Summary
    print_header("Test Summary")
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! SalesAI is ready to use.")
        print("\nNext steps:")
        print("   1. Run: python api.py")
        print("   2. Open: frontend/index.html")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("\n💡 Common solutions:")
        print("   • Make sure Ollama is running: ollama serve")
        print("   • Download model: ollama pull llama3.2")
        print("   • Increase timeout in .env: OLLAMA_TIMEOUT_S=300")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏸️  Tests interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
