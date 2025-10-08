#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Indian Career Roadmap Application
Tests all authentication, user profile, roadmaps, and progress tracking endpoints
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Base URL from frontend environment
BASE_URL = "https://path-finder-in.preview.emergentagent.com/api"

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        self.test_results = []
        
    def log_test(self, test_name, success, message, response_data=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            result["response"] = response_data
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
    def make_request(self, method, endpoint, data=None, headers=None):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if headers is None:
                headers = {}
            
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            headers["Content-Type"] = "application/json"
            
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
            
        except requests.exceptions.RequestException as e:
            return None
    
    def test_admin_init_roadmaps(self):
        """Test admin roadmaps initialization"""
        print("\n=== Testing Admin Roadmaps Initialization ===")
        
        response = self.make_request("POST", "/admin/init-roadmaps")
        
        if response is None:
            self.log_test("Admin Init Roadmaps", False, "Network error - could not connect to server")
            return False
            
        if response.status_code == 200:
            data = response.json()
            self.log_test("Admin Init Roadmaps", True, f"Roadmaps initialized: {data.get('message', 'Success')}")
            return True
        else:
            self.log_test("Admin Init Roadmaps", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_user_registration(self):
        """Test user registration"""
        print("\n=== Testing User Registration ===")
        
        # Generate unique test data
        unique_id = str(uuid.uuid4())[:8]
        test_user = {
            "name": f"Arjun Sharma {unique_id}",
            "email": f"arjun.sharma.{unique_id}@gmail.com",
            "password": "SecurePass123!"
        }
        
        response = self.make_request("POST", "/auth/register", test_user)
        
        if response is None:
            self.log_test("User Registration", False, "Network error - could not connect to server")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                self.auth_token = data["access_token"]
                self.user_data = data["user"]
                self.log_test("User Registration", True, f"User registered successfully: {data['user']['name']}")
                return True
            else:
                self.log_test("User Registration", False, "Missing access_token or user in response")
                return False
        else:
            self.log_test("User Registration", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_user_login(self):
        """Test user login with registered credentials"""
        print("\n=== Testing User Login ===")
        
        if not self.user_data:
            self.log_test("User Login", False, "No user data available for login test")
            return False
            
        # Extract email from registered user
        login_data = {
            "email": self.user_data["email"],
            "password": "SecurePass123!"
        }
        
        # Clear token to test fresh login
        old_token = self.auth_token
        self.auth_token = None
        
        response = self.make_request("POST", "/auth/login", login_data)
        
        if response is None:
            self.log_test("User Login", False, "Network error - could not connect to server")
            self.auth_token = old_token  # Restore token
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                self.auth_token = data["access_token"]
                self.log_test("User Login", True, f"Login successful for: {data['user']['name']}")
                return True
            else:
                self.log_test("User Login", False, "Missing access_token or user in response")
                self.auth_token = old_token  # Restore token
                return False
        else:
            self.log_test("User Login", False, f"HTTP {response.status_code}: {response.text}")
            self.auth_token = old_token  # Restore token
            return False
    
    def test_get_current_user(self):
        """Test getting current user info"""
        print("\n=== Testing Get Current User ===")
        
        if not self.auth_token:
            self.log_test("Get Current User", False, "No auth token available")
            return False
            
        response = self.make_request("GET", "/auth/me")
        
        if response is None:
            self.log_test("Get Current User", False, "Network error - could not connect to server")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "id" in data and "name" in data and "email" in data:
                self.log_test("Get Current User", True, f"Retrieved user info: {data['name']}")
                return True
            else:
                self.log_test("Get Current User", False, "Missing required user fields in response")
                return False
        else:
            self.log_test("Get Current User", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_update_user_stream(self):
        """Test updating user stream preference"""
        print("\n=== Testing Update User Stream ===")
        
        if not self.auth_token:
            self.log_test("Update User Stream", False, "No auth token available")
            return False
            
        stream_data = {"stream": "Science"}
        
        response = self.make_request("PUT", "/user/stream", stream_data)
        
        if response is None:
            self.log_test("Update User Stream", False, "Network error - could not connect to server")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if data.get("stream") == "Science":
                self.log_test("Update User Stream", True, f"Stream updated to: {data['stream']}")
                return True
            else:
                self.log_test("Update User Stream", False, "Stream not properly updated in response")
                return False
        else:
            self.log_test("Update User Stream", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_get_all_roadmaps(self):
        """Test getting all career roadmaps"""
        print("\n=== Testing Get All Roadmaps ===")
        
        response = self.make_request("GET", "/roadmaps")
        
        if response is None:
            self.log_test("Get All Roadmaps", False, "Network error - could not connect to server")
            return False, []
            
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                self.log_test("Get All Roadmaps", True, f"Retrieved {len(data)} roadmaps")
                return True, data
            else:
                self.log_test("Get All Roadmaps", False, "No roadmaps found or invalid response format")
                return False, []
        else:
            self.log_test("Get All Roadmaps", False, f"HTTP {response.status_code}: {response.text}")
            return False, []
    
    def test_get_science_roadmaps(self):
        """Test getting Science stream roadmaps"""
        print("\n=== Testing Get Science Stream Roadmaps ===")
        
        response = self.make_request("GET", "/roadmaps?stream=Science")
        
        if response is None:
            self.log_test("Get Science Roadmaps", False, "Network error - could not connect to server")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                science_count = len([r for r in data if r.get("stream") == "Science"])
                self.log_test("Get Science Roadmaps", True, f"Retrieved {science_count} Science roadmaps")
                return True
            else:
                self.log_test("Get Science Roadmaps", False, "Invalid response format")
                return False
        else:
            self.log_test("Get Science Roadmaps", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_get_specific_roadmap(self, roadmaps):
        """Test getting specific roadmap details"""
        print("\n=== Testing Get Specific Roadmap ===")
        
        if not roadmaps:
            self.log_test("Get Specific Roadmap", False, "No roadmaps available for testing")
            return False, None
            
        # Use first roadmap for testing
        test_roadmap = roadmaps[0]
        roadmap_id = test_roadmap["id"]
        
        response = self.make_request("GET", f"/roadmaps/{roadmap_id}")
        
        if response is None:
            self.log_test("Get Specific Roadmap", False, "Network error - could not connect to server")
            return False, None
            
        if response.status_code == 200:
            data = response.json()
            if "id" in data and "title" in data and "steps" in data:
                self.log_test("Get Specific Roadmap", True, f"Retrieved roadmap: {data['title']}")
                return True, data
            else:
                self.log_test("Get Specific Roadmap", False, "Missing required roadmap fields")
                return False, None
        else:
            self.log_test("Get Specific Roadmap", False, f"HTTP {response.status_code}: {response.text}")
            return False, None
    
    def test_update_progress(self, roadmap):
        """Test updating step completion progress"""
        print("\n=== Testing Update Progress ===")
        
        if not self.auth_token:
            self.log_test("Update Progress", False, "No auth token available")
            return False
            
        if not roadmap or "steps" not in roadmap:
            self.log_test("Update Progress", False, "No roadmap data available for testing")
            return False
            
        # Mark first step as completed
        first_step = roadmap["steps"][0]
        progress_data = {
            "career_id": roadmap["id"],
            "step_id": first_step["id"],
            "completed": True
        }
        
        response = self.make_request("POST", "/progress", progress_data)
        
        if response is None:
            self.log_test("Update Progress", False, "Network error - could not connect to server")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                self.log_test("Update Progress", True, f"Progress updated: {data['message']}")
                return True
            else:
                self.log_test("Update Progress", False, "Missing success message in response")
                return False
        else:
            self.log_test("Update Progress", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_get_user_progress(self):
        """Test getting user's overall progress"""
        print("\n=== Testing Get User Progress ===")
        
        if not self.auth_token:
            self.log_test("Get User Progress", False, "No auth token available")
            return False
            
        response = self.make_request("GET", "/progress")
        
        if response is None:
            self.log_test("Get User Progress", False, "Network error - could not connect to server")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                self.log_test("Get User Progress", True, f"Retrieved progress for {len(data)} careers")
                return True
            else:
                self.log_test("Get User Progress", False, "Invalid response format")
                return False
        else:
            self.log_test("Get User Progress", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_get_career_progress(self, career_id):
        """Test getting progress for specific career"""
        print("\n=== Testing Get Career Progress ===")
        
        if not self.auth_token:
            self.log_test("Get Career Progress", False, "No auth token available")
            return False
            
        if not career_id:
            self.log_test("Get Career Progress", False, "No career ID available for testing")
            return False
            
        response = self.make_request("GET", f"/progress/{career_id}")
        
        if response is None:
            self.log_test("Get Career Progress", False, "Network error - could not connect to server")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "user_id" in data and "career_id" in data:
                progress_pct = data.get("progress_percentage", 0)
                self.log_test("Get Career Progress", True, f"Career progress: {progress_pct}%")
                return True
            else:
                self.log_test("Get Career Progress", False, "Missing required progress fields")
                return False
        else:
            self.log_test("Get Career Progress", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        print("\n=== Testing Invalid Login ===")
        
        invalid_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = self.make_request("POST", "/auth/login", invalid_data)
        
        if response is None:
            self.log_test("Invalid Login Test", False, "Network error - could not connect to server")
            return False
            
        if response.status_code == 401:
            self.log_test("Invalid Login Test", True, "Correctly rejected invalid credentials")
            return True
        else:
            self.log_test("Invalid Login Test", False, f"Expected 401, got {response.status_code}")
            return False
    
    def test_unauthorized_access(self):
        """Test accessing protected endpoint without token"""
        print("\n=== Testing Unauthorized Access ===")
        
        # Temporarily remove token
        old_token = self.auth_token
        self.auth_token = None
        
        response = self.make_request("GET", "/auth/me")
        
        # Restore token
        self.auth_token = old_token
        
        if response is None:
            self.log_test("Unauthorized Access Test", False, "Network error - could not connect to server")
            return False
            
        if response.status_code == 401 or response.status_code == 403:
            self.log_test("Unauthorized Access Test", True, "Correctly rejected unauthorized access")
            return True
        else:
            self.log_test("Unauthorized Access Test", False, f"Expected 401/403, got {response.status_code}")
            return False
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print(f"🚀 Starting Indian Career Roadmap Backend API Tests")
        print(f"📍 Base URL: {self.base_url}")
        print("=" * 60)
        
        # Initialize roadmaps first
        self.test_admin_init_roadmaps()
        
        # Authentication flow
        if not self.test_user_registration():
            print("❌ Registration failed - stopping tests")
            return self.generate_summary()
            
        self.test_user_login()
        self.test_get_current_user()
        
        # User profile
        self.test_update_user_stream()
        
        # Roadmaps
        success, roadmaps = self.test_get_all_roadmaps()
        self.test_get_science_roadmaps()
        
        roadmap = None
        if success and roadmaps:
            success, roadmap = self.test_get_specific_roadmap(roadmaps)
        
        # Progress tracking
        if roadmap:
            self.test_update_progress(roadmap)
            self.test_get_user_progress()
            self.test_get_career_progress(roadmap["id"])
        
        # Error cases
        self.test_invalid_login()
        self.test_unauthorized_access()
        
        return self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"  • {test['test']}: {test['message']}")
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": passed_tests/total_tests*100,
            "details": self.test_results
        }

def main():
    """Main test execution"""
    tester = APITester()
    summary = tester.run_all_tests()
    
    # Exit with error code if tests failed
    if summary["failed"] > 0:
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()