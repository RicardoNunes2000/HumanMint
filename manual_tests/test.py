import sys

sys.path.insert(0, "src")


import json

from humanmint import mint

# ==========================================
# THE "REAL WORLD" DATASET (200 Cases)
# ==========================================

more_data = []

# ------------------------------------------
# GROUP 1: CORPORATE / TECH (50 Cases)
# Testing modern job titles and departments.
# ------------------------------------------
corporate = [
    {"title": "Account Executive", "department": "Sales"},
    {"title": "SDR", "department": "Business Dev"},
    {"title": "BDR", "department": "Sales Development"},
    {"title": "Customer Success Manager", "department": "CS"},
    {"title": "CSM", "department": "Client Success"},
    {"title": "Product Manager", "department": "Product"},
    {"title": "PM", "department": "Product Mgmt"},
    {"title": "Head of Product", "department": "Product"},
    {"title": "VP of Engineering", "department": "Eng"},
    {"title": "Software Engineer", "department": "Engineering"},
    {"title": "DevOps Engineer", "department": "Infrastructure"},
    {"title": "Site Reliability Engineer", "department": "SRE"},
    {"title": "Data Scientist", "department": "Data"},
    {"title": "Chief Data Officer", "department": "Data Science"},
    {"title": "Chief People Officer", "department": "People Ops"},
    {"title": "HRBP", "department": "Human Resources"},
    {"title": "Talent Acquisition Specialist", "department": "Recruiting"},
    {"title": "Recruiter", "department": "Talent"},
    {"title": "Chief Revenue Officer", "department": "Revenue"},
    {"title": "CRO", "department": "Exec"},
    {"title": "Chief Marketing Officer", "department": "Marketing"},
    {"title": "CMO", "department": "Marketing"},
    {"title": "Growth Hacker", "department": "Growth"},
    {"title": "Social Media Manager", "department": "Comms"},
    {"title": "Content Strategist", "department": "Content"},
    {"title": "Copywriter", "department": "Creative"},
    {"title": "Art Director", "department": "Design"},
    {"title": "UX Designer", "department": "User Experience"},
    {"title": "UI/UX Designer", "department": "Product Design"},
    {"title": "General Counsel", "department": "Legal"},
    {"title": "Paralegal", "department": "Legal"},
    {"title": "Compliance Officer", "department": "Compliance"},
    {"title": "Controller", "department": "Finance"},
    {"title": "Bookkeeper", "department": "Accounting"},
    {"title": "Payroll Specialist", "department": "Payroll"},
    {"title": "Executive Assistant", "department": "Admin"},
    {"title": "Office Manager", "department": "Facilities"},
    {"title": "Receptionist", "department": "Front Desk"},
    {"title": "IT Support Specialist", "department": "Help Desk"},
    {"title": "System Administrator", "department": "SysAdmin"},
    {"title": "Network Engineer", "department": "NetOps"},
    {"title": "CISO", "department": "InfoSec"},
    {"title": "Security Analyst", "department": "Security"},
    {"title": "Project Manager", "department": "PMO"},
    {"title": "Scrum Master", "department": "Agile"},
    {"title": "Business Analyst", "department": "BI"},
    {"title": "Operations Manager", "department": "Ops"},
    {"title": "Logistics Coordinator", "department": "Supply Chain"},
    {"title": "Procurement Manager", "department": "Purchasing"},
    {"title": "Founder", "department": "Executive"},
]
more_data.extend(corporate)

# ------------------------------------------
# GROUP 2: HEALTHCARE (30 Cases)
# Testing medical abbreviations.
# ------------------------------------------
healthcare = [
    {"title": "Registered Nurse", "department": "Nursing"},
    {"title": "RN", "department": "ICU"},
    {"title": "LPN", "department": "Nursing Home"},
    {"title": "CNA", "department": "Assisted Living"},
    {"title": "Nurse Practitioner", "department": "Clinic"},
    {"title": "NP", "department": "Family Practice"},
    {"title": "Physician Assistant", "department": "Urgent Care"},
    {"title": "PA-C", "department": "Orthopedics"},
    {"title": "Medical Doctor", "department": "Internal Med"},
    {"title": "MD", "department": "Cardiology"},
    {"title": "Surgeon", "department": "Surgery"},
    {"title": "Chief of Surgery", "department": "Surgery"},
    {"title": "Anesthesiologist", "department": "Anesthesia"},
    {"title": "Radiologist", "department": "Radiology"},
    {"title": "Rad Tech", "department": "Imaging"},
    {"title": "Phlebotomist", "department": "Lab"},
    {"title": "Lab Tech", "department": "Pathology"},
    {"title": "Pharmacist", "department": "Pharmacy"},
    {"title": "PharmD", "department": "Pharmacy"},
    {"title": "Pharmacy Tech", "department": "Retail Pharmacy"},
    {"title": "Physical Therapist", "department": "PT"},
    {"title": "Occupational Therapist", "department": "OT"},
    {"title": "Speech Therapist", "department": "SLP"},
    {"title": "Respiratory Therapist", "department": "RT"},
    {"title": "Dietitian", "department": "Nutrition"},
    {"title": "Social Worker", "department": "Case Mgmt"},
    {"title": "LCSW", "department": "Behavioral Health"},
    {"title": "Psychologist", "department": "Psychiatry"},
    {"title": "Medical Director", "department": "Admin"},
    {"title": "Hospital Administrator", "department": "Administration"},
]
more_data.extend(healthcare)

# ------------------------------------------
# GROUP 3: ACADEMIC / EDUCATION (30 Cases)
# Testing university titles.
# ------------------------------------------
academic = [
    {"title": "Professor", "department": "History"},
    {"title": "Associate Professor", "department": "English"},
    {"title": "Assistant Professor", "department": "Math"},
    {"title": "Adjunct Professor", "department": "Physics"},
    {"title": "Lecturer", "department": "Chemistry"},
    {"title": "Instructor", "department": "Biology"},
    {"title": "Dean", "department": "College of Arts"},
    {"title": "Dean of Students", "department": "Student Affairs"},
    {"title": "Provost", "department": "Academic Affairs"},
    {"title": "Chancellor", "department": "Administration"},
    {"title": "President", "department": "Office of the President"},
    {"title": "Registrar", "department": "Registrar's Office"},
    {"title": "Bursar", "department": "Finance"},
    {"title": "Admissions Officer", "department": "Admissions"},
    {"title": "Financial Aid Advisor", "department": "Financial Aid"},
    {"title": "Librarian", "department": "Library"},
    {"title": "Archivist", "department": "Special Collections"},
    {"title": "Research Assistant", "department": "Psychology Lab"},
    {"title": "Teaching Assistant", "department": "Computer Science"},
    {"title": "Postdoc", "department": "Neuroscience"},
    {"title": "PhD Candidate", "department": "Sociology"},
    {"title": "Principal", "department": "High School"},
    {"title": "Vice Principal", "department": "Middle School"},
    {"title": "Superintendent", "department": "District Office"},
    {"title": "Guidance Counselor", "department": "Counseling"},
    {"title": "School Nurse", "department": "Health Office"},
    {"title": "Coach", "department": "Athletics"},
    {"title": "Athletic Director", "department": "Sports"},
    {"title": "Alumni Director", "department": "Alumni Relations"},
    {"title": "Development Officer", "department": "Fundraising"},
]
more_data.extend(academic)

# ------------------------------------------
# GROUP 4: NAMES (Complex & International) (40 Cases)
# ------------------------------------------
names_complex = [
    {"name": "Ursula K. Le Guin"},
    {"name": "Gabriel Garcia Marquez"},  # No accent
    {"name": "Gabriel García Márquez"},  # With accent
    {"name": "Bjork"},
    {"name": "Björk"},
    {"name": "Sinead O'Connor"},
    {"name": "Sinéad O'Connor"},
    {"name": "Rene Descartes"},
    {"name": "René Descartes"},
    {"name": "W.E.B. Du Bois"},
    {"name": "T.S. Eliot"},
    {"name": "J.R.R. Tolkien"},
    {"name": "George R.R. Martin"},
    {"name": "C. S. Lewis"},  # Spaces in initials
    {"name": "H. G. Wells"},
    {"name": "Ludwig van Beethoven"},
    {"name": "Johann Sebastian Bach"},
    {"name": "Wolfgang Amadeus Mozart"},
    {"name": "Rembrandt van Rijn"},
    {"name": "Leonardo DiCaprio"},
    {"name": "Robert De Niro"},
    {"name": "Helena Bonham Carter"},
    {"name": "Daniel Day-Lewis"},
    {"name": "Julia Louis-Dreyfus"},
    {"name": "Sacha Baron Cohen"},
    {"name": "Lin-Manuel Miranda"},
    {"name": "Andrew Lloyd Webber"},
    {"name": "Olivia Newton-John"},
    {"name": "Mary Tyler Moore"},
    {"name": "Jamie Lee Curtis"},
    {"name": "Sarah Jessica Parker"},
    {"name": "Neil Patrick Harris"},
    {"name": "Joseph Gordon-Levitt"},
    {"name": "Keegan-Michael Key"},
    {"name": "Simu Liu"},
    {"name": "Sandra Oh"},
    {"name": "John Cho"},
    {"name": "Lucy Liu"},
    {"name": "Constance Wu"},
    {"name": "Michelle Yeoh"},
]
more_data.extend(names_complex)

# ------------------------------------------
# GROUP 5: ADDRESSES (Suites & Weirdness) (30 Cases)
# ------------------------------------------
addresses_weird = [
    {"address": "123 Main St Suite 100"},
    {"address": "123 Main St, Suite 100"},
    {"address": "123 Main St. Ste 100"},
    {"address": "123 Main St #100"},
    {"address": "Suite 100 123 Main St"},
    {"address": "Ste 100, 123 Main St"},
    {"address": "#100 123 Main St"},
    {"address": "123 Main St Unit 5"},
    {"address": "123 Main St Apt 5"},
    {"address": "123 Main St Building A"},
    {"address": "123 Main St Bldg A"},
    {"address": "123 Main St Floor 2"},
    {"address": "123 Main St Fl 2"},
    {"address": "123 Main St 2nd Floor"},
    {"address": "One Infinite Loop"},
    {"address": "1 Hacker Way"},
    {"address": "1600 Amphitheatre Pkwy"},
    {"address": "350 5th Ave"},
    {"address": "30 Rockefeller Plaza"},
    {"address": "4 Times Square"},
    {"address": "1 World Trade Center"},
    {"address": "PO Box 4000"},
    {"address": "P.O. Box 5000"},
    {"address": "Post Office Box 6000"},
    {"address": "Rural Route 1 Box 5"},
    {"address": "RR 2 Box 10"},
    {"address": "HC 1 Box 20"},
    {"address": "General Delivery"},
    {"address": "The White House"},
    {"address": "The Pentagon"},
]
more_data.extend(addresses_weird)

# ------------------------------------------
# GROUP 6: DIRTY DATA (20 Cases)
# ------------------------------------------
dirty = [
    {"name": "Smith, John,"},  # Trailing comma
    {"name": ",John Smith"},  # Leading comma
    {"name": "John  Smith"},  # Double space
    {"name": "John Smith "},  # Trailing space
    {"name": " John Smith"},  # Leading space
    {"name": "john smith"},  # Lowercase
    {"name": "JOHN SMITH"},  # Uppercase
    {"name": "JoHn SmItH"},  # Mixed case
    {"email": "test@test.com,"},  # Trailing comma
    {"email": "test@test.com."},  # Trailing dot
    {"email": " test@test.com "},  # Spaces
    {"phone": "555-123-4567,"},  # Trailing comma
    {"phone": "555-123-4567."},  # Trailing dot
    {"department": "HR,"},  # Trailing comma
    {"department": "HR."},  # Trailing dot
    {"title": "Manager,"},  # Trailing comma
    {"title": "Manager."},  # Trailing dot
    {"address": "123 Main St,"},  # Trailing comma
    {"address": "123 Main St."},  # Trailing dot
    {"organization": "Acme Corp,"},  # Trailing comma
]
more_data.extend(dirty)

# ==========================================
# EXECUTION
# ==========================================

results = []
print(f"Running {len(more_data)} real-world cases...")

for i, case in enumerate(more_data):
    try:
        r = mint(**case)

        # Build output dict dynamically
        out = {}
        if "name" in case:
            out["name"] = r.name_standardized
        if "title" in case:
            out["title"] = r.title_canonical
        if "department" in case:
            out["dept"] = r.department_canonical
        if "email" in case:
            out["email"] = r.email_standardized
        if "phone" in case:
            out["phone"] = r.phone_pretty
        if "address" in case:
            out["address"] = r.address_canonical
        if "organization" in case:
            out["org"] = r.organization_canonical

        results.append({"id": i, "input": case, "output": out})

    except Exception as e:
        results.append({"id": i, "input": case, "error": str(e)})

with open("manual_tests/real_world_test_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)
