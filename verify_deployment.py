import requests
import json
import sys

# Configuration
# BACKEND_URL = "http://localhost:8000"  # Local
BACKEND_URL = "https://em-sme-system-ws.onrender.com"  # Production
LOGIN_URL = f"{BACKEND_URL}/api/v1/auth/login"
HEALTH_URL = f"{BACKEND_URL}/health"

def check_endpoint(name, method, url, headers=None, json_data=None):
    print(f"\n--- Checking {name} [{method} {url}] ---")
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=json_data)
        elif method == "OPTIONS":
            response = requests.options(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print("Headers:")
        for k, v in response.headers.items():
            if k.lower().startswith("access-control"):
                print(f"  {k}: {v}")
        
        if response.status_code >= 400:
            print(f"Error Content: {response.text[:200]}...")
            if response.status_code == 404:
                print(">>> CRITICAL: Endpoint not found (404). Check URL path.")
            if response.status_code == 405:
                print(">>> Method Not Allowed. This is GOOD for GET requests to POST endpoints (implies route exists).")
        else:
            print(">>> Success!")
            
    except Exception as e:
        print(f"Failed to connect: {e}")

def main():
    print(f"Verifying Deployment at: {BACKEND_URL}")
    
    # 1. Health Check
    check_endpoint("Health Check", "GET", HEALTH_URL)
    
    # 2. CORS Preflight Check (Simulating Browser)
    origin = "https://em-sme-system.vercel.app"
    cors_headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"
    }
    check_endpoint("CORS Preflight", "OPTIONS", LOGIN_URL, headers=cors_headers)
    
    # 3. Direct Route Check (GET on POST endpoint)
    # Should return 405 Method Not Allowed if route exists, or 404 if not.
    check_endpoint("Route Existence (GET)", "GET", LOGIN_URL)

    # 4. Actual Login Attempt (Dummy Data)
    login_data = {"email": "test@example.com", "password": "WrongPassword123!"}
    check_endpoint("Login Attempt", "POST", LOGIN_URL, json_data=login_data)

    # 5. Registration Attempt (Random Email to avoid conflicts)
    import random
    rand_int = random.randint(1000, 9999)
    reg_data = {
        "email": f"test_reg_{rand_int}@example.com",
        "password": "StrongPassword123!",
        "full_name": "Test User",
        "organization_name": f"Test Org {rand_int}"
    }
    REG_URL = f"{BACKEND_URL}/api/v1/auth/register"
    check_endpoint("Registration Attempt", "POST", REG_URL, json_data=reg_data)

if __name__ == "__main__":
    main()
