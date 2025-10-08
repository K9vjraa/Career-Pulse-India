from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import jwt
import bcrypt
from bson import ObjectId

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

security = HTTPBearer()

# Pydantic Models
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime
    selected_stream: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class ProgressUpdate(BaseModel):
    career_id: str
    step_id: str
    completed: bool

class UserProgress(BaseModel):
    user_id: str
    career_id: str
    completed_steps: List[str] = []
    progress_percentage: float = 0.0
    last_updated: datetime

class CareerRoadmap(BaseModel):
    id: str
    title: str
    stream: str  # Science, Commerce, Arts
    description: str
    steps: List[Dict[str, Any]]
    estimated_duration: str
    difficulty_level: str

# Helper Functions
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user_id, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        created_at=user["created_at"],
        selected_stream=user.get("selected_stream")
    )

# Authentication Routes
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    user_doc = {
        "name": user_data.name,
        "email": user_data.email,
        "password": hashed_password,
        "created_at": datetime.utcnow(),
        "selected_stream": None
    }
    
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    # Create JWT token
    access_token = create_jwt_token(user_id)
    
    user = User(
        id=user_id,
        name=user_data.name,
        email=user_data.email,
        created_at=user_doc["created_at"]
    )
    
    return Token(access_token=access_token, token_type="bearer", user=user)

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    # Find user by email
    user_doc = await db.users.find_one({"email": user_data.email})
    if not user_doc or not verify_password(user_data.password, user_doc["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create JWT token
    access_token = create_jwt_token(str(user_doc["_id"]))
    
    user = User(
        id=str(user_doc["_id"]),
        name=user_doc["name"],
        email=user_doc["email"],
        created_at=user_doc["created_at"],
        selected_stream=user_doc.get("selected_stream")
    )
    
    return Token(access_token=access_token, token_type="bearer", user=user)

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# User Profile Routes
@api_router.put("/user/stream")
async def update_stream(stream_data: dict, current_user: User = Depends(get_current_user)):
    stream = stream_data.get("stream")
    if stream not in ["Science", "Commerce", "Arts"]:
        raise HTTPException(status_code=400, detail="Invalid stream")
    
    await db.users.update_one(
        {"_id": ObjectId(current_user.id)},
        {"$set": {"selected_stream": stream}}
    )
    
    return {"message": "Stream updated successfully", "stream": stream}

# Career Roadmaps Routes
@api_router.get("/roadmaps", response_model=List[CareerRoadmap])
async def get_roadmaps(stream: Optional[str] = None):
    query = {}
    if stream:
        query["stream"] = stream
    
    roadmaps = await db.roadmaps.find(query).to_list(1000)
    return [CareerRoadmap(**{**roadmap, "id": str(roadmap["_id"])}) for roadmap in roadmaps]

@api_router.get("/roadmaps/{roadmap_id}", response_model=CareerRoadmap)
async def get_roadmap(roadmap_id: str):
    try:
        roadmap = await db.roadmaps.find_one({"_id": ObjectId(roadmap_id)})
        if not roadmap:
            raise HTTPException(status_code=404, detail="Roadmap not found")
        return CareerRoadmap(**{**roadmap, "id": str(roadmap["_id"])})
    except:
        raise HTTPException(status_code=404, detail="Roadmap not found")

# Progress Tracking Routes
@api_router.post("/progress")
async def update_progress(
    progress_data: ProgressUpdate,
    current_user: User = Depends(get_current_user)
):
    # Get existing progress or create new
    existing_progress = await db.progress.find_one({
        "user_id": current_user.id,
        "career_id": progress_data.career_id
    })
    
    if existing_progress:
        completed_steps = existing_progress.get("completed_steps", [])
        if progress_data.completed and progress_data.step_id not in completed_steps:
            completed_steps.append(progress_data.step_id)
        elif not progress_data.completed and progress_data.step_id in completed_steps:
            completed_steps.remove(progress_data.step_id)
        
        # Get roadmap to calculate progress percentage
        roadmap = await db.roadmaps.find_one({"_id": ObjectId(progress_data.career_id)})
        total_steps = len(roadmap.get("steps", [])) if roadmap else 0
        progress_percentage = (len(completed_steps) / total_steps * 100) if total_steps > 0 else 0
        
        await db.progress.update_one(
            {"_id": existing_progress["_id"]},
            {"$set": {
                "completed_steps": completed_steps,
                "progress_percentage": progress_percentage,
                "last_updated": datetime.utcnow()
            }}
        )
    else:
        completed_steps = [progress_data.step_id] if progress_data.completed else []
        roadmap = await db.roadmaps.find_one({"_id": ObjectId(progress_data.career_id)})
        total_steps = len(roadmap.get("steps", [])) if roadmap else 0
        progress_percentage = (len(completed_steps) / total_steps * 100) if total_steps > 0 else 0
        
        progress_doc = {
            "user_id": current_user.id,
            "career_id": progress_data.career_id,
            "completed_steps": completed_steps,
            "progress_percentage": progress_percentage,
            "last_updated": datetime.utcnow()
        }
        await db.progress.insert_one(progress_doc)
    
    return {"message": "Progress updated successfully"}

@api_router.get("/progress", response_model=List[UserProgress])
async def get_user_progress(current_user: User = Depends(get_current_user)):
    progress_docs = await db.progress.find({"user_id": current_user.id}).to_list(1000)
    return [UserProgress(**progress) for progress in progress_docs]

@api_router.get("/progress/{career_id}")
async def get_career_progress(career_id: str, current_user: User = Depends(get_current_user)):
    progress = await db.progress.find_one({
        "user_id": current_user.id,
        "career_id": career_id
    })
    
    if not progress:
        return UserProgress(
            user_id=current_user.id,
            career_id=career_id,
            completed_steps=[],
            progress_percentage=0.0,
            last_updated=datetime.utcnow()
        )
    
    return UserProgress(**progress)

# Initialize roadmaps data
@api_router.post("/admin/init-roadmaps")
async def initialize_roadmaps():
    # Check if roadmaps already exist
    existing = await db.roadmaps.count_documents({})
    if existing > 0:
        return {"message": "Roadmaps already initialized"}
    
    # Career roadmaps data will be inserted here
    roadmaps_data = [
        # Science Stream
        {
            "title": "Full Stack Developer",
            "stream": "Science",
            "description": "Complete path to becoming a full-stack web developer with modern technologies",
            "estimated_duration": "12-18 months",
            "difficulty_level": "Intermediate",
            "steps": [
                {"id": "1", "title": "Learn HTML & CSS Basics", "description": "Master HTML5 and CSS3 fundamentals", "resources": ["https://www.freecodecamp.org/", "https://developer.mozilla.org/"], "duration": "4-6 weeks"},
                {"id": "2", "title": "JavaScript Fundamentals", "description": "Learn core JavaScript concepts", "resources": ["https://javascript.info/", "https://www.coursera.org/"], "duration": "6-8 weeks"},
                {"id": "3", "title": "React.js", "description": "Build interactive user interfaces", "resources": ["https://reactjs.org/", "https://www.unacademy.com/"], "duration": "8-10 weeks"},
                {"id": "4", "title": "Backend with Node.js", "description": "Server-side development", "resources": ["https://nodejs.org/", "https://swayam.gov.in/"], "duration": "6-8 weeks"},
                {"id": "5", "title": "Database Management", "description": "Learn MongoDB and SQL", "resources": ["https://university.mongodb.com/", "https://www.coursera.org/"], "duration": "4-6 weeks"},
                {"id": "6", "title": "Build Portfolio Projects", "description": "Create 3-5 full-stack applications", "resources": ["https://github.com/", "https://netlify.com/"], "duration": "8-12 weeks"}
            ]
        },
        {
            "title": "Data Scientist",
            "stream": "Science", 
            "description": "Become a data scientist with Python, ML, and analytics skills",
            "estimated_duration": "15-24 months",
            "difficulty_level": "Advanced",
            "steps": [
                {"id": "1", "title": "Python Programming", "description": "Master Python for data science", "resources": ["https://www.python.org/", "https://swayam.gov.in/"], "duration": "6-8 weeks"},
                {"id": "2", "title": "Statistics & Mathematics", "description": "Linear algebra, calculus, statistics", "resources": ["https://www.khanacademy.org/", "https://www.coursera.org/"], "duration": "10-12 weeks"},
                {"id": "3", "title": "Data Analysis Libraries", "description": "Pandas, NumPy, Matplotlib", "resources": ["https://pandas.pydata.org/", "https://www.unacademy.com/"], "duration": "6-8 weeks"},
                {"id": "4", "title": "Machine Learning", "description": "Scikit-learn, supervised/unsupervised learning", "resources": ["https://scikit-learn.org/", "https://www.coursera.org/"], "duration": "12-16 weeks"},
                {"id": "5", "title": "Deep Learning", "description": "Neural networks, TensorFlow/PyTorch", "resources": ["https://www.tensorflow.org/", "https://pytorch.org/"], "duration": "10-12 weeks"},
                {"id": "6", "title": "Real Projects & Portfolio", "description": "Build data science projects", "resources": ["https://kaggle.com/", "https://github.com/"], "duration": "8-10 weeks"}
            ]
        },
        {
            "title": "Doctor (MBBS)",
            "stream": "Science",
            "description": "Medical career path through NEET and MBBS program",
            "estimated_duration": "6-8 years",
            "difficulty_level": "Advanced",
            "steps": [
                {"id": "1", "title": "Class 12 PCB", "description": "Physics, Chemistry, Biology with 90%+", "resources": ["https://ncert.nic.in/", "https://www.unacademy.com/"], "duration": "2 years"},
                {"id": "2", "title": "NEET Preparation", "description": "Qualify NEET-UG exam", "resources": ["https://www.nta.ac.in/", "https://www.aakash.ac.in/"], "duration": "1-2 years"},
                {"id": "3", "title": "MBBS Degree", "description": "5.5 years medical program", "resources": ["https://www.mciindia.org/", "Medical Colleges"], "duration": "5.5 years"},
                {"id": "4", "title": "Internship", "description": "1 year mandatory internship", "resources": ["Teaching Hospitals", "Medical Institutions"], "duration": "1 year"},
                {"id": "5", "title": "Medical Registration", "description": "Register with Medical Council", "resources": ["https://www.nmc.org.in/"], "duration": "3-6 months"},
                {"id": "6", "title": "Specialization (Optional)", "description": "MD/MS through NEET-PG", "resources": ["https://www.nta.ac.in/", "Post Graduate Medical Colleges"], "duration": "3 years"}
            ]
        },
        {
            "title": "Engineer",
            "stream": "Science",
            "description": "Engineering career through JEE and B.Tech program",
            "estimated_duration": "4-6 years",
            "difficulty_level": "Intermediate",
            "steps": [
                {"id": "1", "title": "Class 12 PCM", "description": "Physics, Chemistry, Mathematics", "resources": ["https://ncert.nic.in/", "https://www.unacademy.com/"], "duration": "2 years"},
                {"id": "2", "title": "JEE Preparation", "description": "JEE Main & Advanced preparation", "resources": ["https://www.nta.ac.in/", "https://www.fiitjee.com/"], "duration": "1-2 years"},
                {"id": "3", "title": "B.Tech Degree", "description": "4-year engineering program", "resources": ["IITs", "NITs", "Engineering Colleges"], "duration": "4 years"},
                {"id": "4", "title": "Internships & Projects", "description": "Gain practical experience", "resources": ["Industry Partners", "Research Labs"], "duration": "During B.Tech"},
                {"id": "5", "title": "Technical Skills", "description": "Programming, design, analysis", "resources": ["https://www.coursera.org/", "https://swayam.gov.in/"], "duration": "Continuous"},
                {"id": "6", "title": "Job/Higher Studies", "description": "Placement or M.Tech/MS", "resources": ["Campus Placements", "Gate Preparation"], "duration": "Final Year"}
            ]
        },
        {
            "title": "Biotechnologist",
            "stream": "Science",
            "description": "Career in biotechnology and life sciences",
            "estimated_duration": "4-6 years",
            "difficulty_level": "Intermediate",
            "steps": [
                {"id": "1", "title": "Class 12 PCB/PCM", "description": "Biology focus with chemistry", "resources": ["https://ncert.nic.in/", "https://www.unacademy.com/"], "duration": "2 years"},
                {"id": "2", "title": "Entrance Exams", "description": "JEE Main, BITSAT, or university exams", "resources": ["https://www.nta.ac.in/", "University Websites"], "duration": "1 year"},
                {"id": "3", "title": "B.Tech/B.Sc Biotechnology", "description": "Undergraduate degree in biotechnology", "resources": ["IITs", "NITs", "Biotechnology Colleges"], "duration": "4 years"},
                {"id": "4", "title": "Laboratory Skills", "description": "Practical lab techniques", "resources": ["College Labs", "Industry Training"], "duration": "During Degree"},
                {"id": "5", "title": "Research Projects", "description": "Undergraduate research experience", "resources": ["Research Institutes", "CSIR Labs"], "duration": "1-2 years"},
                {"id": "6", "title": "Specialization/Job", "description": "M.Tech or industry position", "resources": ["GATE", "Campus Placements"], "duration": "2+ years"}
            ]
        },
        
        # Commerce Stream
        {
            "title": "Chartered Accountant",
            "stream": "Commerce",
            "description": "Professional CA qualification through ICAI",
            "estimated_duration": "4-6 years",
            "difficulty_level": "Advanced",
            "steps": [
                {"id": "1", "title": "Class 12 Commerce", "description": "Accountancy, Business Studies, Economics", "resources": ["https://ncert.nic.in/", "https://www.unacademy.com/"], "duration": "2 years"},
                {"id": "2", "title": "CA Foundation", "description": "Entry level CA examination", "resources": ["https://www.icai.org/", "CA Coaching Institutes"], "duration": "6-12 months"},
                {"id": "3", "title": "CA Intermediate", "description": "Middle level CA examination", "resources": ["https://www.icai.org/", "Self Study + Coaching"], "duration": "12-18 months"},
                {"id": "4", "title": "Articleship Training", "description": "3 years practical training", "resources": ["CA Firms", "Corporate Houses"], "duration": "3 years"},
                {"id": "5", "title": "CA Final", "description": "Final level CA examination", "resources": ["https://www.icai.org/", "Advanced Study"], "duration": "6-18 months"},
                {"id": "6", "title": "Membership & Practice", "description": "ICAI membership and career start", "resources": ["https://www.icai.org/", "CA Firms"], "duration": "Ongoing"}
            ]
        },
        {
            "title": "Investment Banker",
            "stream": "Commerce",
            "description": "Career in investment banking and finance",
            "estimated_duration": "4-6 years",
            "difficulty_level": "Advanced",
            "steps": [
                {"id": "1", "title": "Bachelor's Degree", "description": "B.Com, BBA, or Economics", "resources": ["Commerce Colleges", "Universities"], "duration": "3 years"},
                {"id": "2", "title": "Financial Knowledge", "description": "Learn markets, valuation, modeling", "resources": ["https://www.coursera.org/", "https://www.cfa institute.org/"], "duration": "1-2 years"},
                {"id": "3", "title": "MBA/Finance Specialization", "description": "Master's in Finance/MBA", "resources": ["IIMs", "Top B-Schools"], "duration": "2 years"},
                {"id": "4", "title": "Internships", "description": "Investment banking internships", "resources": ["Goldman Sachs", "Morgan Stanley", "Local Banks"], "duration": "Summer Terms"},
                {"id": "5", "title": "Certifications", "description": "CFA, FRM certifications", "resources": ["https://www.cfainstitute.org/", "https://www.garp.org/"], "duration": "1-3 years"},
                {"id": "6", "title": "Full-time Position", "description": "Analyst/Associate role", "resources": ["Investment Banks", "Financial Services"], "duration": "Career Start"}
            ]
        },
        {
            "title": "Business Analyst",
            "stream": "Commerce",
            "description": "Business analysis and consulting career",
            "estimated_duration": "3-5 years",
            "difficulty_level": "Intermediate",
            "steps": [
                {"id": "1", "title": "Bachelor's Degree", "description": "BBA, B.Com, or related field", "resources": ["Business Schools", "Universities"], "duration": "3 years"},
                {"id": "2", "title": "Business Analysis Skills", "description": "Process mapping, requirements analysis", "resources": ["https://www.coursera.org/", "https://www.iiba.org/"], "duration": "6-12 months"},
                {"id": "3", "title": "Technical Skills", "description": "SQL, Excel, Data Analysis tools", "resources": ["https://www.microsoft.com/", "https://www.tableau.com/"], "duration": "3-6 months"},
                {"id": "4", "title": "Industry Experience", "description": "Internships and entry-level roles", "resources": ["Consulting Firms", "Corporations"], "duration": "1-2 years"},
                {"id": "5", "title": "Certifications", "description": "CBAP, PMI-PBA certifications", "resources": ["https://www.iiba.org/", "https://www.pmi.org/"], "duration": "6-12 months"},
                {"id": "6", "title": "Senior Roles", "description": "Senior BA or consultancy positions", "resources": ["Career Progression", "Networking"], "duration": "Ongoing"}
            ]
        },
        {
            "title": "Marketing Manager",
            "stream": "Commerce",
            "description": "Digital and traditional marketing career path",
            "estimated_duration": "4-6 years",
            "difficulty_level": "Intermediate",
            "steps": [
                {"id": "1", "title": "Bachelor's Degree", "description": "Marketing, BBA, Mass Communication", "resources": ["Business Schools", "Universities"], "duration": "3 years"},
                {"id": "2", "title": "Digital Marketing Skills", "description": "SEO, SEM, Social Media Marketing", "resources": ["https://www.google.com/skillshop/", "https://www.hubspot.com/"], "duration": "3-6 months"},
                {"id": "3", "title": "Marketing Analytics", "description": "Google Analytics, Marketing metrics", "resources": ["https://analytics.google.com/", "https://www.coursera.org/"], "duration": "2-4 months"},
                {"id": "4", "title": "Industry Experience", "description": "Marketing executive/coordinator roles", "resources": ["Marketing Agencies", "Corporate Marketing"], "duration": "2-3 years"},
                {"id": "5", "title": "Specialization", "description": "Brand, Digital, or Product Marketing", "resources": ["https://www.unacademy.com/", "Professional Courses"], "duration": "1-2 years"},
                {"id": "6", "title": "Leadership Role", "description": "Marketing Manager position", "resources": ["Career Growth", "MBA Optional"], "duration": "Ongoing"}
            ]
        },
        {
            "title": "Entrepreneur",
            "stream": "Commerce",
            "description": "Start and scale your own business",
            "estimated_duration": "Varies (3+ years)",
            "difficulty_level": "Advanced",
            "steps": [
                {"id": "1", "title": "Business Education", "description": "BBA, B.Com or relevant field", "resources": ["Business Schools", "Online Courses"], "duration": "3 years"},
                {"id": "2", "title": "Idea Development", "description": "Identify market opportunity", "resources": ["https://www.startupindia.gov.in/", "Market Research"], "duration": "3-6 months"},
                {"id": "3", "title": "Business Plan", "description": "Create comprehensive business plan", "resources": ["https://www.score.org/", "Business Plan Tools"], "duration": "2-4 months"},
                {"id": "4", "title": "Funding & Setup", "description": "Secure funding and legal setup", "resources": ["Angel Investors", "https://www.startupindia.gov.in/"], "duration": "3-12 months"},
                {"id": "5", "title": "Launch & Operations", "description": "Launch product/service and operations", "resources": ["Incubators", "Mentorship Programs"], "duration": "6-18 months"},
                {"id": "6", "title": "Scale & Growth", "description": "Expand business and scale operations", "resources": ["Business Networks", "Growth Strategies"], "duration": "Ongoing"}
            ]
        },
        
        # Arts Stream
        {
            "title": "Teacher",
            "stream": "Arts",
            "description": "Teaching career in schools and higher education",
            "estimated_duration": "4-6 years",
            "difficulty_level": "Intermediate",
            "steps": [
                {"id": "1", "title": "Bachelor's Degree", "description": "BA in subject of interest", "resources": ["Universities", "Arts Colleges"], "duration": "3 years"},
                {"id": "2", "title": "B.Ed Degree", "description": "Bachelor of Education", "resources": ["Education Colleges", "Universities"], "duration": "2 years"},
                {"id": "3", "title": "Teaching Practice", "description": "Student teaching and practice", "resources": ["Practice Schools", "Internship Programs"], "duration": "During B.Ed"},
                {"id": "4", "title": "Qualification Exams", "description": "CTET, TET, or state exams", "resources": ["https://ctet.nic.in/", "State Education Boards"], "duration": "6 months"},
                {"id": "5", "title": "Teaching Position", "description": "School or college appointment", "resources": ["Government Schools", "Private Schools"], "duration": "Career Start"},
                {"id": "6", "title": "Professional Development", "description": "M.Ed, research, or administration", "resources": ["Universities", "Professional Courses"], "duration": "Ongoing"}
            ]
        },
        {
            "title": "Designer",
            "stream": "Arts",
            "description": "Graphic, UI/UX, or product design career",
            "estimated_duration": "3-5 years",
            "difficulty_level": "Intermediate",
            "steps": [
                {"id": "1", "title": "Foundation Skills", "description": "Art, drawing, design fundamentals", "resources": ["Art Schools", "https://www.skillshare.com/"], "duration": "6-12 months"},
                {"id": "2", "title": "Design Software", "description": "Adobe Creative Suite, Figma", "resources": ["https://www.adobe.com/", "https://www.figma.com/"], "duration": "3-6 months"},
                {"id": "3", "title": "Formal Education", "description": "B.Des, Diploma in Design", "resources": ["NIFT", "Design Colleges"], "duration": "3-4 years"},
                {"id": "4", "title": "Portfolio Development", "description": "Build strong design portfolio", "resources": ["https://www.behance.net/", "https://dribbble.com/"], "duration": "Ongoing"},
                {"id": "5", "title": "Specialization", "description": "Choose UI/UX, Graphic, Product Design", "resources": ["https://www.coursera.org/", "https://www.unacademy.com/"], "duration": "6-12 months"},
                {"id": "6", "title": "Professional Work", "description": "Design studio or freelance career", "resources": ["Design Agencies", "Freelance Platforms"], "duration": "Career Start"}
            ]
        },
        {
            "title": "Journalist",
            "stream": "Arts",
            "description": "Media and journalism career path",
            "estimated_duration": "3-4 years",
            "difficulty_level": "Intermediate",
            "steps": [
                {"id": "1", "title": "Bachelor's Degree", "description": "Journalism, Mass Communication, English", "resources": ["Journalism Schools", "Universities"], "duration": "3 years"},
                {"id": "2", "title": "Writing Skills", "description": "News writing, reporting, editing", "resources": ["https://www.coursera.org/", "Writing Workshops"], "duration": "6-12 months"},
                {"id": "3", "title": "Media Training", "description": "Video, audio, digital media skills", "resources": ["Media Training Institutes", "Online Courses"], "duration": "3-6 months"},
                {"id": "4", "title": "Internships", "description": "Newspaper, TV, online media internships", "resources": ["Media Houses", "News Organizations"], "duration": "6-12 months"},
                {"id": "5", "title": "Beat Specialization", "description": "Politics, Sports, Entertainment, etc.", "resources": ["Professional Experience", "Networking"], "duration": "1-2 years"},
                {"id": "6", "title": "Career Growth", "description": "Reporter, Editor, or Media Entrepreneur", "resources": ["Media Organizations", "Independent Media"], "duration": "Ongoing"}
            ]
        },
        {
            "title": "Psychologist",
            "stream": "Arts",
            "description": "Psychology and counseling career",
            "estimated_duration": "5-7 years",
            "difficulty_level": "Advanced",
            "steps": [
                {"id": "1", "title": "Bachelor's in Psychology", "description": "BA/B.Sc Psychology", "resources": ["Psychology Departments", "Universities"], "duration": "3 years"},
                {"id": "2", "title": "Master's Degree", "description": "MA/M.Sc in Psychology", "resources": ["Psychology Colleges", "Universities"], "duration": "2 years"},
                {"id": "3", "title": "Specialization", "description": "Clinical, Counseling, Organizational", "resources": ["Specialization Courses", "Professional Training"], "duration": "1-2 years"},
                {"id": "4", "title": "Practical Training", "description": "Internships, supervised practice", "resources": ["Hospitals", "Clinics", "Counseling Centers"], "duration": "1 year"},
                {"id": "5", "title": "Licensing", "description": "Professional registration and certification", "resources": ["Psychology Councils", "Professional Bodies"], "duration": "3-6 months"},
                {"id": "6", "title": "Practice Setup", "description": "Private practice or institutional work", "resources": ["Healthcare Institutions", "Private Practice"], "duration": "Career Start"}
            ]
        },
        {
            "title": "Writer",
            "stream": "Arts",
            "description": "Creative and content writing career",
            "estimated_duration": "2-4 years",
            "difficulty_level": "Intermediate",
            "steps": [
                {"id": "1", "title": "Language Skills", "description": "Master language and grammar", "resources": ["Literature Courses", "Language Schools"], "duration": "Ongoing"},
                {"id": "2", "title": "Writing Practice", "description": "Daily writing, different formats", "resources": ["Writing Communities", "https://www.wattpad.com/"], "duration": "6-12 months"},
                {"id": "3", "title": "Education", "description": "English, Literature, or Journalism", "resources": ["Universities", "Literature Departments"], "duration": "3 years"},
                {"id": "4", "title": "Portfolio Building", "description": "Published works, blog, articles", "resources": ["https://medium.com/", "Literary Magazines"], "duration": "1-2 years"},
                {"id": "5", "title": "Specialization", "description": "Content, Creative, Technical Writing", "resources": ["https://www.coursera.org/", "Writing Courses"], "duration": "6-12 months"},
                {"id": "6", "title": "Professional Career", "description": "Publisher, freelance, or content creator", "resources": ["Publishing Houses", "Content Agencies"], "duration": "Career Start"}
            ]
        }
    ]
    
    # Insert all roadmaps
    result = await db.roadmaps.insert_many(roadmaps_data)
    return {"message": f"Initialized {len(result.inserted_ids)} career roadmaps successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()