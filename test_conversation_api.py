#!/usr/bin/env python3
"""
test_conversation_api.py
Automated test script for Conversational Complaint Intake Engine
"""

import requests
import json
import time
from typing import Optional

BASE_URL = "http://localhost:8000"

class ConversationTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.session_id: Optional[str] = None
    
    def register_user(self, username: str = "test_conv_user"):
        """Register a new test user."""
        print("\n📝 Registering user...")
        response = requests.post(
            f"{self.base_url}/auth/register",
            json={
                "username": username,
                "email": f"{username}@test.com",
                "password": "test123",
                "role": "citizen"
            }
        )
        if response.status_code == 200:
            print("✅ User registered successfully")
            return True
        elif "already registered" in response.text.lower():
            print("ℹ️  User already exists")
            return True
        else:
            print(f"❌ Registration failed: {response.text}")
            return False
    
    def login(self, username: str = "test_conv_user"):
        """Login and get JWT token."""
        print("\n🔐 Logging in...")
        response = requests.post(
            f"{self.base_url}/auth/login",
            data={
                "username": username,
                "password": "test123"
            }
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            print("✅ Login successful")
            return True
        else:
            print(f"❌ Login failed: {response.text}")
            return False
    
    def start_conversation(self, message: str):
        """Start a new conversation."""
        print(f"\n💬 User: {message}")
        response = requests.post(
            f"{self.base_url}/conversation/start",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"message": message}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.session_id = data.get("session_id")
            print(f"🤖 AI: {data.get('ai_response')}")
            return data
        else:
            print(f"❌ Failed: {response.text}")
            return None
    
    def send_message(self, message: str):
        """Send a message in ongoing conversation."""
        print(f"\n💬 User: {message}")
        response = requests.post(
            f"{self.base_url}/conversation/message",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"message": message}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("conversation_complete"):
                print("✅ Conversation Complete!")
                if "complaint" in data:
                    complaint = data["complaint"]
                    print(f"\n📋 Complaint Filed:")
                    print(f"   Reference ID: {complaint.get('reference_id')}")
                    print(f"   Department: {complaint.get('department')}")
                    print(f"   Priority: {complaint.get('priority')}")
                    print(f"   Category: {complaint.get('category')}")
            else:
                print(f"🤖 AI: {data.get('ai_response')}")
            return data
        else:
            print(f"❌ Failed: {response.text}")
            return None
    
    def get_session_state(self):
        """Get current session state."""
        response = requests.get(
            f"{self.base_url}/conversation/session",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        if response.status_code == 200:
            return response.json()
        return None

def test_emotional_user_scenario():
    """Test Scenario 1: Emotional user with payment failure."""
    print("\n" + "="*60)
    print("TEST SCENARIO 1: Emotional User - Payment Failure")
    print("="*60)
    
    tester = ConversationTester()
    
    # Setup
    if not tester.register_user("emotional_user"):
        return False
    if not tester.login("emotional_user"):
        return False
    
    # Start conversation with emotional message
    tester.start_conversation("Oh my god my payment failed! I am so worried!")
    time.sleep(1)
    
    # Provide information step by step
    tester.send_message("State Bank of India")
    time.sleep(1)
    
    tester.send_message("UPI payment")
    time.sleep(1)
    
    tester.send_message("5000 rupees")
    time.sleep(1)
    
    tester.send_message("Today morning around 10 AM")
    time.sleep(1)
    
    tester.send_message("I don't have the transaction ID")
    time.sleep(1)
    
    result = tester.send_message(
        "Money was deducted from my account but merchant did not receive it"
    )
    
    return result and result.get("conversation_complete")

def test_detailed_user_scenario():
    """Test Scenario 2: User provides detailed information upfront."""
    print("\n" + "="*60)
    print("TEST SCENARIO 2: Detailed User - All Info Upfront")
    print("="*60)
    
    tester = ConversationTester()
    
    if not tester.register_user("detailed_user"):
        return False
    if not tester.login("detailed_user"):
        return False
    
    # Start with comprehensive message
    result = tester.start_conversation(
        "I want to file a complaint about a failed NEFT transaction of "
        "Rs 25000 from HDFC Bank on 15th January. Transaction ID is NEFT123456. "
        "The amount was debited but not credited to beneficiary account."
    )
    
    # AI should extract most information and ask for remaining fields
    if result:
        print("\n✅ AI successfully extracted information from detailed message")
        
        # Check session state
        session = tester.get_session_state()
        if session:
            print(f"\n📊 Session State:")
            print(json.dumps(session.get("form_state"), indent=2))
    
    return True

def test_status_query_scenario():
    """Test Scenario 3: User wants to check complaint status."""
    print("\n" + "="*60)
    print("TEST SCENARIO 3: Status Query")
    print("="*60)
    
    tester = ConversationTester()
    
    if not tester.register_user("status_user"):
        return False
    if not tester.login("status_user"):
        return False
    
    # Ask about status
    result = tester.start_conversation("What is the status of my complaint?")
    
    if result and "reference number" in result.get("ai_response", "").lower():
        print("✅ AI correctly identified status query")
        return True
    
    return False

def run_all_tests():
    """Run all test scenarios."""
    print("\n" + "="*60)
    print("🧪 CONVERSATIONAL INTAKE ENGINE - TEST SUITE")
    print("="*60)
    
    results = {
        "Emotional User Scenario": False,
        "Detailed User Scenario": False,
        "Status Query Scenario": False
    }
    
    try:
        results["Emotional User Scenario"] = test_emotional_user_scenario()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    
    time.sleep(2)
    
    try:
        results["Detailed User Scenario"] = test_detailed_user_scenario()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    
    time.sleep(2)
    
    try:
        results["Status Query Scenario"] = test_status_query_scenario()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    print("🚀 Starting Conversational Intake Engine Tests...")
    print("⚠️  Make sure the FastAPI server is running on http://localhost:8000")
    print("⚠️  Make sure GROQ_API_KEY is set in .env file")
    
    input("\nPress Enter to continue...")
    
    success = run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        exit(1)
