import sys

# Ensure we can import the library
sys.path.insert(0, "src")

from humanmint import mint

records = [
    # --- Public Safety ---
    (
        "Chief Robert L. Clayton",
        "rclayton@springfieldpd.gov",
        "(413) 748-3399",
        "Springfield Police Dept",
        "Chief of Police",
    ),
    (
        "Lt. Maria J. Cortez",
        "MCORTEZ@SPRINGFIELDPD.GOV",
        "413-748-3333 x221",
        "Police Department",
        "Lieutenant",
    ),
    (
        "Sgt. John O'Hara",
        "john.ohara@city-lincoln.org",
        "402.441.6000 ext 14",
        "Lincoln PD",
        "Sergeant",
    ),
    (
        "Officer James K. Miller",
        "jmiller@lincolnpd.org",
        "4024416005",
        "LINC PD",
        "Police Officer",
    ),
    (
        "Deputy Sarah D'Amico",
        "sdamico@clarkcounty-sheriff.us",
        "702-455-3200",
        "Clark County Sheriff’s Office",
        "Deputy Sheriff",
    ),
    # --- Fire ---
    (
        "Chief Alan McBride",
        "amcbride@tulsa-fire.gov",
        "(918) 596-9777",
        "Tulsa Fire Dept",
        "Fire Chief",
    ),
    (
        "Capt. Helen F. Monroe",
        "hmonroe@tulsa.gov",
        "918.596.9700 x14",
        "Fire Department",
        "Captain",
    ),
    (
        "Battalion Chief Eric Stenson",
        "eric.stenson@tulsafd.org",
        "9185969741",
        "TFD",
        "Battalion Chief",
    ),
    # --- DPW / Infrastructure ---
    (
        "Mark T. Rivers",
        "mrivers@boston.gov",
        "617-635-4900",
        "000171 - Public Works 555-1212",
        "Public Works Director",
    ),
    (
        "Linda O’Connell",
        "loconnell@boston.gov",
        "(617) 635-4950 ext. 12",
        "DPW - Waste & Recycling Div",
        "Operations Manager",
    ),
    (
        "Derek McKinney",
        "dmckinney@baltimorecity.gov",
        "410 396 3100",
        "Dept of Public Works",
        "Water Systems Analyst",
    ),
    (
        "Karen L. Sato",
        "ksato@portlandoregon.gov",
        "503-823-1700",
        "Transportation Bureau",
        "Transportation Planner",
    ),
    # --- Planning & Development ---
    (
        "Anne-Marie D'Angelo",
        "adangelo@springfieldplanning.gov",
        "413-787-6020 ext. 14",
        "Department of Planning & Development",
        "Senior Planner",
    ),
    (
        "Dr. Jessica V. Chen",
        "jchen@oaklandca.gov",
        "510.238.3941",
        "Planning (Downtown District)",
        "Principal Planner",
    ),
    (
        "Tomás J. Núñez",
        "tnunez@miamidade.gov",
        "305-375-2000",
        "Zoning & Development",
        "Zoning Officer",
    ),
    (
        "William J. Carver",
        "wcarver@phoenix.gov",
        "602-262-6882",
        "Planning & Zoning Dept",
        "Planning Manager",
    ),
    # --- Finance / Budget ---
    (
        "Christine K. Dalton",
        "cdalton@seattle.gov",
        "206 684 2489",
        "Dept of Finance & Admin Services",
        "Budget Analyst",
    ),
    (
        "Michael O. Patel",
        "mpatel@seattle.gov",
        "(206) 684-2480",
        "Finance Department",
        "Financial Manager",
    ),
    (
        "Susan E. Byrne",
        "sbyrne@chicago.gov",
        "312-744-4000",
        "Office of Budget & Mgmt",
        "Senior Budget Analyst",
    ),
    # --- IT / Technology ---
    (
        "Kyle J. Sanders",
        "kyle.sanders@denvergov.org",
        "720-913-5000 x211",
        "Technology Services Dept",
        "IT Systems Administrator",
    ),
    (
        "Rachel P. Wu",
        "rwu@denvergov.org",
        "7209135001",
        "Tech Services",
        "Cybersecurity Analyst",
    ),
    (
        "Joseph M. Frazier",
        "jfrazier@austintexas.gov",
        "512-974-2000",
        "Communications & Tech Mgmt",
        "Network Engineer",
    ),
    # --- HR ---
    (
        "Linda G. Parks",
        "lparks@madisonwi.gov",
        "608-266-4611",
        "Human Resources Dept",
        "HR Manager",
    ),
    (
        "George F. Newman",
        "gnewman@madisonwi.gov",
        "(608) 266-4631",
        "HR",
        "HR Generalist",
    ),
    (
        "Sandra K. Ortiz",
        "sortiz@charlottenc.gov",
        "704-336-2778",
        "Human Resources",
        "Training Coordinator",
    ),
    # --- Clerk / Administration ---
    (
        "Robert T. Jenkins",
        "rjenkins@columbus.gov",
        "614 645 7380",
        "City Clerk",
        "City Clerk",
    ),
    (
        "Michelle A. Rosario",
        "mrosario@columbus.gov",
        "(614) 645-7390",
        "Administrative Services",
        "Administrative Manager",
    ),
    (
        "Judy A. Kim",
        "jkim@lacity.org",
        "213-978-1133",
        "Office of Administrative Services",
        "Administrative Coordinator",
    ),
    # --- Legal ---
    (
        "Amy L. Thompson",
        "athompson@sanantonio.gov",
        "210 207 4000",
        "City Attorney’s Office",
        "Assistant City Attorney",
    ),
    (
        "Marcus D. Vaughn",
        "mvaughn@sanantonio.gov",
        "210-207-4010",
        "Legal Department",
        "Senior Attorney",
    ),
    (
        "Karen B. Jackson",
        "kjackson@atlantaga.gov",
        "(404) 330-6400",
        "Law Department",
        "Paralegal",
    ),
    # --- Elections / Clerk Divisions ---
    (
        "Diane L. Frost",
        "dfrost@maricopa.gov",
        "602-506-1511",
        "Elections Dept",
        "Elections Supervisor",
    ),
    (
        "Thomas K. Riley",
        "triley@maricopa.gov",
        "6025061510",
        "Recorder’s Office",
        "Records Coordinator",
    ),
    (
        "Sandra P. Ellis",
        "sellis@maricopa.gov",
        "602 506 1513 x14",
        "Elections",
        "Election Specialist",
    ),
    # --- Parks & Recreation ---
    (
        "Henry B. Thompson",
        "hthompson@houstontx.gov",
        "713-837-0311",
        "Parks & Recreation",
        "Parks Director",
    ),
    (
        "Emily J. Carter",
        "ecarter@houstontx.gov",
        "(713) 837-0300",
        "Recreation & Community Svcs",
        "Recreation Coordinator",
    ),
    (
        "Jacob L. Fernandez",
        "jfernandez@sanjoseca.gov",
        "408 535 3570",
        "Parks, Recreation & Neighborhood Svcs",
        "Program Specialist",
    ),
    # --- Public Health ---
    (
        "Dr. Olivia T. Mendoza",
        "omendoza@lahealth.gov",
        "213 240 7812",
        "Dept of Public Health",
        "Public Health Officer",
    ),
    (
        "Daniel S. Adams",
        "dadams@lahealth.gov",
        "(213) 240-7800",
        "Public Health",
        "Epidemiologist",
    ),
    (
        "Vanessa R. Nguyen",
        "vnguyen@kingcounty.gov",
        "206-296-4600",
        "Health Department",
        "Health Services Coordinator",
    ),
    # --- Water / Utilities ---
    (
        "Gregory A. Freeman",
        "gfreeman@lacitywater.org",
        "213.367.1000",
        "Water & Power Dept",
        "Water Plant Supervisor",
    ),
    (
        "Jessica L. O’Brien",
        "jobrien@cityoforlando.net",
        "407-246-2271",
        "Utility Services",
        "Utility Analyst",
    ),
    (
        "Kyle D. Harmon",
        "kharmon@phoenix.gov",
        "602-262-6251",
        "Water Services Department",
        "Water Engineer",
    ),
    # --- Housing / Community Development ---
    (
        "Theresa L. Fox",
        "tfox@baltimorecity.gov",
        "410-396-3211",
        "Housing & Community Dev",
        "Housing Specialist",
    ),
    (
        "Martin R. Diaz",
        "mdiaz@baltimorecity.gov",
        "(410) 396-3200",
        "Housing Dept",
        "Community Development Coordinator",
    ),
    (
        "Alyssa J. Gomez",
        "agomez@dallas.gov",
        "214-670-4060",
        "Community Development",
        "Program Analyst",
    ),
    # --- Libraries ---
    (
        "Samuel T. Banks",
        "sbanks@nypl.org",
        "212 621 0200",
        "New York Public Library",
        "Librarian",
    ),
    (
        "Rebecca K. Owens",
        "rowens@nypl.org",
        "(212) 621-0299",
        "Library Services",
        "Library Assistant",
    ),
    (
        "Derek J. Marshall",
        "dmarshall@lapl.org",
        "213 228 7000",
        "Los Angeles Public Library",
        "Library Supervisor",
    ),
    # --- Transportation ---
    (
        "Alan P. Hines",
        "ahines@sfmta.com",
        "415 701 4500",
        "Municipal Transportation Agency",
        "Transportation Manager",
    ),
    (
        "Michelle G. Ruiz",
        "mruiz@sfmta.com",
        "(415) 701-4511",
        "Transportation",
        "Transit Planner",
    ),
    (
        "Jonathan D. Oliver",
        "joliver@septa.org",
        "215-580-7800",
        "Transit Authority",
        "Operations Coordinator",
    ),
    # --- Economic Development ---
    (
        "Jason L. Carter",
        "jcarter@okc.gov",
        "405 297 2400",
        "Economic Dev Dept",
        "Economic Development Analyst",
    ),
    (
        "Linda P. Watts",
        "lwatts@okc.gov",
        "(405) 297-2411",
        "Econ Development Office",
        "Program Coordinator",
    ),
    (
        "Patrick J. Walsh",
        "pwalsh@wichita.gov",
        "316 268 4526",
        "Economic Development",
        "Business Development Manager",
    ),
    # --- County Admin / Commission ---
    (
        "Christopher A. Monroe",
        "cmonroe@kingcounty.gov",
        "206 263 9600",
        "County Executive Office",
        "Policy Analyst",
    ),
    (
        "Jennifer L. Shaw",
        "jshaw@kingcounty.gov",
        "(206) 263-9601",
        "County Administration",
        "Administrative Analyst",
    ),
    (
        "Markus R. Tate",
        "mtate@clarkcountynv.gov",
        "702-455-3500",
        "County Manager’s Office",
        "Management Analyst",
    ),
    # --- Schools / Education ---
    (
        "Dr. Karen E. Holloway",
        "kholloway@phoenixschools.org",
        "602 764 1100",
        "School District Admin",
        "Assistant Superintendent",
    ),
    (
        "Thomas J. Rivera",
        "trivera@phxschools.org",
        "(602) 764-1110",
        "Education Administration",
        "Teacher Specialist",
    ),
    (
        "Martha L. Gonzales",
        "mgonzales@dallasisd.org",
        "972 925 3900",
        "ISD",
        "School Coordinator",
    ),
    # --- More Public Works / Utilities (to reach ~100) ---
    (
        "Anthony J. Wells",
        "awells@lasvegasnevada.gov",
        "702 229 6011",
        "Streets & Highways",
        "Streets Supervisor",
    ),
    (
        "Veronica M. Hughes",
        "vhughes@lasvegasnevada.gov",
        "702-229-6003",
        "Traffic Engineering",
        "Traffic Engineer",
    ),
    (
        "Peter K. Wallace",
        "pwallace@sacramento.gov",
        "916 808 8300",
        "Waste Management",
        "Waste Collection Supervisor",
    ),
    # --- Admin / HR / Clerk extra ---
    (
        "Nancy D. Pearson",
        "npearson@sanjoseca.gov",
        "408-535-3500",
        "Human Resources",
        "Benefits Specialist",
    ),
    (
        "Charles R. Boone",
        "cboone@sanjoseca.gov",
        "408 535 3510",
        "Clerk’s Office",
        "Records Clerk",
    ),
    (
        "Hannah S. Ortiz",
        "hannah.ortiz@cityoftampa.gov",
        "813 274 8211",
        "Administration",
        "Administrative Aide",
    ),
]


def main():
    for i, (name, email, phone, dept, title) in enumerate(records, 1):
        print(f"\n=== RECORD {i} ===")
        result = mint(name=name, email=email, phone=phone, department=dept, title=title)
        print(result.model_dump())


if __name__ == "__main__":
    main()
