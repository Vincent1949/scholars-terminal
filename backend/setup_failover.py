# setup_failover.py - Setup script for the LLM failover system

import subprocess
import sys
import os
from pathlib import Path

def install_package(package_name):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package_name}: {e}")
        return False

def check_ollama_running():
    """Check if Ollama is running locally"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama is running with {len(models)} models available")
            for model in models[:5]:  # Show first 5 models
                print(f"   - {model['name']}")
            return True
    except:
        pass
    
    print("⚠️  Ollama not running or not accessible at localhost:11434")
    print("   Please start Ollama if you want to use local models")
    return False

def setup_environment():
    """Setup .env file if it doesn't exist"""
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    print("📝 Creating .env file template...")
    
    env_template = """# LLM Failover System Configuration

# OpenAI API Key (for embeddings and backup LLM)
OPENAI_API_KEY=your_openai_api_key_here

# Google Gemini API Key (free tier available)
GOOGLE_API_KEY=your_google_api_key_here

# Anthropic Claude API Key (optional)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Provider Priorities (comma-separated, in order of preference)
EMBEDDING_PROVIDERS=openai,local,ollama
LLM_PROVIDERS=ollama_qwen,ollama_mistral,openai,gemini

# System Settings
MAX_RETRIES=3
REQUEST_TIMEOUT=30
RATE_LIMIT_DELAY=1
LOG_LEVEL=INFO

# Cost and Usage Tracking
TRACK_COSTS=true
DAILY_COST_LIMIT=10.00
"""
    
    with open(env_file, 'w') as f:
        f.write(env_template)
    
    print(f"✅ Created .env template at {env_file.absolute()}")
    print("⚠️  Please edit the .env file with your actual API keys")

def download_local_embedding_model():
    """Download local embedding model for offline use"""
    try:
        print("📥 Downloading local embedding model (this may take a few minutes)...")
        from sentence_transformers import SentenceTransformer
        
        # Download a lightweight, fast model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Local embedding model downloaded successfully")
        
        # Test the model
        test_embedding = model.encode("test sentence")
        print(f"✅ Model test successful - embedding dimension: {len(test_embedding)}")
        
    except Exception as e:
        print(f"❌ Failed to download embedding model: {e}")
        print("   You can try again later or use only API-based embeddings")

def test_api_connections():
    """Test connections to various API providers"""
    print("\n🔍 Testing API connections...")
    
    # Test OpenAI
    try:
        import openai
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and api_key != 'your_openai_api_key_here':
            client = openai.OpenAI(api_key=api_key)
            models = client.models.list()
            print("✅ OpenAI API connection successful")
        else:
            print("⚠️  OpenAI API key not configured")
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
    
    # Test Google Gemini
    try:
        import google.generativeai as genai
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key and api_key != 'your_google_api_key_here':
            genai.configure(api_key=api_key)
            models = list(genai.list_models())
            print("✅ Google Gemini API connection successful")
        else:
            print("⚠️  Google API key not configured")
    except Exception as e:
        print(f"❌ Google Gemini API test failed: {e}")

def setup_ollama_models():
    """Setup recommended Ollama models"""
    if not check_ollama_running():
        return
    
    recommended_models = [
        "qwen2.5:latest",  # Good general-purpose model
        "mistral:7b",      # Fast and efficient
        "nomic-embed-text" # For embeddings
    ]
    
    print("\n📦 Recommended Ollama models:")
    for model in recommended_models:
        print(f"   - {model}")
    
    install_models = input("\nWould you like to install these models? (y/N): ").lower().strip()
    
    if install_models == 'y':
        for model in recommended_models:
            print(f"📥 Installing {model}...")
            try:
                result = subprocess.run(['ollama', 'pull', model], 
                                      capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    print(f"✅ {model} installed successfully")
                else:
                    print(f"❌ Failed to install {model}: {result.stderr}")
            except subprocess.TimeoutExpired:
                print(f"⏰ {model} installation timed out (may still be downloading)")
            except Exception as e:
                print(f"❌ Error installing {model}: {e}")

def main():
    """Main setup function"""
    print("🚀 Setting up LLM Failover System")
    print("=" * 40)
    
    # Install required packages
    print("\n📦 Installing required packages...")
    packages = [
        "sentence-transformers",
        "google-generativeai", 
        "python-dotenv",
        "requests",
        "openai>=1.0.0"
    ]
    
    failed_packages = []
    for package in packages:
        if not install_package(package):
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n⚠️  Some packages failed to install: {', '.join(failed_packages)}")
        print("   You may need to install them manually or check your Python environment")
    
    # Setup environment file
    print("\n🔧 Setting up environment...")
    setup_environment()
    
    # Check Ollama
    print("\n🤖 Checking Ollama status...")
    ollama_running = check_ollama_running()
    
    # Download local embedding model
    print("\n🧠 Setting up local embedding model...")
    download_local_embedding_model()
    
    # Test API connections
    test_api_connections()
    
    # Setup Ollama models if available
    if ollama_running:
        setup_ollama_models()
    
    print("\n" + "=" * 50)
    print("✅ Setup Complete!")
    print("\n📋 Next steps:")
    print("1. Edit your .env file with actual API keys")
    print("2. Start Ollama if you want to use local models")
    print("3. Run your chatbot with the new failover system")
    print("\n💡 Tips:")
    print("- The system will automatically fallback to available providers")
    print("- Monitor the logs to see which providers are being used")
    print("- Use the status interface to check system health")
    
    if not ollama_running:
        print("\n🚨 Important: Ollama is not running!")
        print("   - Install Ollama from: https://ollama.ai")
        print("   - Start it with: ollama serve")
        print("   - Then run: ollama pull qwen2.5")

if __name__ == "__main__":
    main()