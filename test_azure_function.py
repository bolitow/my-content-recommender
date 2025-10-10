"""
Script de test pour vérifier que l'Azure Function répond correctement
"""

import os
import requests
import json
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

AZURE_FUNCTION_URL = os.getenv("AZURE_FUNCTION_URL")
AZURE_FUNCTION_KEY = os.getenv("AZURE_FUNCTION_KEY")

print("=" * 70)
print("🧪 TEST AZURE FUNCTION")
print("=" * 70)
print(f"\n📍 URL: {AZURE_FUNCTION_URL}")
print(f"🔑 Clé: {AZURE_FUNCTION_KEY[:20]}...{AZURE_FUNCTION_KEY[-10:]}")

# Test 1 : User ID 123
print("\n\n--- Test 1 : User ID 123 ---")

try:
    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "user_id": 123,
        "n_recommendations": 5
    }

    # Construction de l'URL complète avec la clé
    full_url = f"{AZURE_FUNCTION_URL}?code={AZURE_FUNCTION_KEY}"

    print(f"⏳ Envoi de la requête...")
    response = requests.post(full_url, json=payload, headers=headers, timeout=30)

    print(f"📊 Status code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Succès!")
        print(f"\n🎯 Recommandations pour l'utilisateur {data['user_id']}:")
        for i, article_id in enumerate(data['recommendations'], 1):
            print(f"   {i}. Article #{article_id}")
        print(f"\n📊 Modèle: {data['model']}")
        print(f"⏰ Timestamp: {data.get('timestamp', 'N/A')}")
    else:
        print(f"❌ Erreur!")
        print(f"Message: {response.text}")

except requests.exceptions.Timeout:
    print("❌ Timeout: La fonction Azure met trop de temps à répondre (> 30s)")
    print("💡 C'est peut-être le cold start. Réessaye dans quelques secondes.")

except requests.exceptions.ConnectionError:
    print("❌ Erreur de connexion: Impossible de joindre Azure")
    print("💡 Vérifie l'URL et ta connexion internet")

except Exception as e:
    print(f"❌ Erreur inattendue: {e}")

# Test 2 : User ID 456
print("\n\n--- Test 2 : User ID 456 ---")

try:
    payload = {
        "user_id": 456,
        "n_recommendations": 3
    }

    print(f"⏳ Envoi de la requête...")
    response = requests.post(full_url, json=payload, headers=headers, timeout=10)

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Succès! {len(data['recommendations'])} recommandations obtenues")
        print(f"   Articles: {data['recommendations']}")
    else:
        print(f"❌ Erreur {response.status_code}: {response.text}")

except Exception as e:
    print(f"❌ Erreur: {e}")

print("\n" + "=" * 70)
print("✅ Tests terminés!")
print("=" * 70)
print("\n💡 Si tous les tests sont verts, tu peux utiliser Streamlit :")
print("   1. Lance : streamlit run app_v2.py")
print("   2. DÉCOCHE 'Mode test'")
print("   3. Clique sur 'Recommander'")
print("   4. 🎉 Profite de tes recommandations Azure !")
