"""
Gods-Eye OS — Deterministic Civic Data Seeder
Generates realistic Indian constituency/booth/citizen data for demo without any database dependency.
All data is held in-memory and served by FastAPI endpoints.
"""
import random
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta

# Seed for reproducibility across restarts
random.seed(42)

# ─── Reference Data ──────────────────────────────────────────────

CONSTITUENCIES = [
    {"id": "CON-01", "name": "Chandni Chowk", "state": "Delhi", "lat": 28.6562, "lng": 77.2307},
    {"id": "CON-02", "name": "Varanasi", "state": "Uttar Pradesh", "lat": 25.3176, "lng": 82.9739},
    {"id": "CON-03", "name": "Mumbai South", "state": "Maharashtra", "lat": 18.9322, "lng": 72.8347},
    {"id": "CON-04", "name": "Bangalore South", "state": "Karnataka", "lat": 12.9352, "lng": 77.6245},
    {"id": "CON-05", "name": "Kolkata North", "state": "West Bengal", "lat": 22.6071, "lng": 88.3950},
]

WARD_NAMES = [
    "Sector A", "Sector B", "Sector C", "Sector D", "Sector E",
    "Zone North", "Zone South", "Zone East", "Zone West", "Zone Central",
    "Block 1", "Block 2", "Block 3", "Block 4", "Block 5",
    "Division Alpha", "Division Beta", "Division Gamma", "Division Delta", "Division Epsilon",
    "Area I", "Area II", "Area III", "Area IV", "Area V",
]

MALE_NAMES = [
    "Rajesh Kumar", "Amit Sharma", "Vijay Singh", "Suresh Patel", "Manish Gupta",
    "Deepak Verma", "Rahul Yadav", "Arun Mishra", "Sanjay Tiwari", "Pradeep Joshi",
    "Rohit Chauhan", "Nikhil Dubey", "Ashish Pandey", "Gaurav Srivastava", "Vivek Rathi",
    "Anand Shukla", "Ramesh Agarwal", "Sunil Mehta", "Naveen Reddy", "Harish Iyer",
]

FEMALE_NAMES = [
    "Priya Sharma", "Anita Devi", "Sunita Kumari", "Meena Patel", "Kavita Singh",
    "Rekha Gupta", "Pooja Verma", "Suman Yadav", "Lakshmi Nair", "Geeta Mishra",
    "Rani Tiwari", "Savita Joshi", "Neha Chauhan", "Pallavi Dubey", "Ankita Pandey",
    "Ritu Srivastava", "Swati Rathi", "Divya Shukla", "Megha Agarwal", "Shalini Mehta",
]

SURNAMES = [
    "Kumar", "Sharma", "Singh", "Patel", "Gupta", "Verma", "Yadav", "Mishra",
    "Tiwari", "Joshi", "Chauhan", "Dubey", "Pandey", "Srivastava", "Rathi",
    "Shukla", "Agarwal", "Mehta", "Reddy", "Iyer", "Nair", "Das", "Dey", "Sen",
]

ISSUES = ["Water Supply", "Road Repair", "Healthcare Access", "Employment", "Education", "Electricity", "Sanitation", "Public Transport"]
ISSUE_WEIGHTS = [0.22, 0.18, 0.15, 0.14, 0.12, 0.08, 0.06, 0.05]

SCHEMES = [
    {"id": "SCH-01", "name": "Ayushman Bharat", "ministry": "Health", "target_segment": "All", "benefit": "₹5L health cover"},
    {"id": "SCH-02", "name": "PM-Kisan", "ministry": "Agriculture", "target_segment": "Farmer", "benefit": "₹6000/year"},
    {"id": "SCH-03", "name": "Mudra Yojana", "ministry": "Finance", "target_segment": "Business", "benefit": "Loan up to ₹10L"},
    {"id": "SCH-04", "name": "PM Ujjwala", "ministry": "Petroleum", "target_segment": "Women", "benefit": "Free LPG connection"},
    {"id": "SCH-05", "name": "PMAY", "ministry": "Housing", "target_segment": "All", "benefit": "Affordable housing"},
    {"id": "SCH-06", "name": "Skill India", "ministry": "Skill Dev", "target_segment": "Youth", "benefit": "Free skill training"},
    {"id": "SCH-07", "name": "PM Vishwakarma", "ministry": "MSME", "target_segment": "Business", "benefit": "Artisan support ₹3L"},
    {"id": "SCH-08", "name": "Sukanya Samriddhi", "ministry": "Finance", "target_segment": "Women", "benefit": "Girl child savings"},
]

STREETS = [
    "Gali No. 1", "Gali No. 2", "Gali No. 3", "Gali No. 4", "Gali No. 5",
    "Main Road", "Back Lane", "Market Street", "Temple Road", "School Lane",
    "Naya Mohalla", "Purana Mohalla", "Station Road", "Hospital Road", "Park Avenue",
]

PROJECT_TYPES = ["Road Resurfacing", "Streetlight Installation", "Drainage System", "Community Center", "Park Development", "Water Pipeline"]

WORKER_ROLES = ["Field Coordinator", "Survey Agent", "Outreach Specialist", "Data Collector", "Community Liaison"]

COMPLAINT_TEMPLATES = [
    "Water supply has been irregular for the past {days} days in {street}.",
    "The road near {street} is completely broken and dangerous for vehicles.",
    "No streetlights working in {street}, very unsafe at night.",
    "Government hospital in our area has no medicines available.",
    "Youth in {street} area are unable to find jobs despite having degrees.",
    "Drainage overflow causing health hazards in {street}.",
    "The school building in {street} area needs urgent repair.",
    "Electricity cuts happening 4-5 times daily in {street}.",
    "Thank you for fixing the water pipeline in {street}, it's working well now.",
    "The new road constructed in {street} is excellent quality.",
    "Ayushman card distribution was very smooth, appreciate the effort.",
    "PM-Kisan amount received on time this quarter, very helpful.",
]

# ─── Data Generation Functions ───────────────────────────────────

def _generate_citizen_id(booth_id: str, index: int) -> str:
    raw = f"{booth_id}-{index}"
    return f"CIT-{hashlib.md5(raw.encode()).hexdigest()[:8].upper()}"


def _determine_segment(age: int, gender: str, occupation: str) -> str:
    if occupation == "Farmer":
        return "Farmer"
    if gender == "Female":
        return "Women"
    if age <= 35:
        return "Youth"
    if occupation in ("Shopkeeper", "Trader", "Entrepreneur"):
        return "Business"
    return "Senior" if age >= 60 else "General"


def _generate_citizens(booth_id: str, count: int = 400) -> List[dict]:
    citizens = []
    occupations = ["Farmer", "Shopkeeper", "Teacher", "Student", "Homemaker", "Trader",
                    "Labourer", "Driver", "Entrepreneur", "Government Employee", "Retired"]

    for i in range(count):
        gender = random.choice(["Male", "Female"])
        age = random.randint(18, 82)
        name = random.choice(MALE_NAMES if gender == "Male" else FEMALE_NAMES)
        occupation = random.choice(occupations)
        segment = _determine_segment(age, gender, occupation)
        street = random.choice(STREETS)

        # Assign sentiment per citizen — weighted towards issues relevant to their segment
        primary_issue = random.choices(ISSUES, weights=ISSUE_WEIGHTS, k=1)[0]
        sentiment_score = random.randint(10, 95)

        # Assign scheme beneficiaries based on segment eligibility
        enrolled_schemes = []
        for scheme in SCHEMES:
            target = scheme["target_segment"]
            if target == "All" or target == segment:
                if random.random() < 0.45:  # 45% enrollment rate
                    enrolled_schemes.append(scheme["id"])

        citizens.append({
            "id": _generate_citizen_id(booth_id, i),
            "name": name,
            "age": age,
            "gender": gender,
            "occupation": occupation,
            "segment": segment,
            "street": street,
            "phone": f"+91-{random.randint(70000, 99999)}{random.randint(10000, 99999)}",
            "primary_issue": primary_issue,
            "sentiment_score": sentiment_score,
            "sentiment_label": "Positive" if sentiment_score > 60 else ("Negative" if sentiment_score < 40 else "Neutral"),
            "enrolled_schemes": enrolled_schemes,
            "last_interaction": (datetime.now() - timedelta(days=random.randint(0, 90))).isoformat(),
            "influence_score": random.randint(1, 100),
            "is_key_voter": random.random() < 0.15,
        })

    return citizens


def _generate_workers(constituency_id: str, ward_id: str, booth_ids: List[str], count_per_booth: int = 4) -> List[dict]:
    workers = []
    for booth_id in booth_ids:
        for j in range(count_per_booth):
            wid = f"WKR-{constituency_id[-2:]}{ward_id[-2:]}{booth_id[-3:]}-{j+1:02d}"
            tasks_total = random.randint(10, 50)
            tasks_done = random.randint(int(tasks_total * 0.4), tasks_total)
            workers.append({
                "id": wid,
                "name": random.choice(MALE_NAMES + FEMALE_NAMES),
                "role": random.choice(WORKER_ROLES),
                "phone": f"+91-{random.randint(70000, 99999)}{random.randint(10000, 99999)}",
                "assigned_booth": booth_id,
                "assigned_ward": ward_id,
                "assigned_constituency": constituency_id,
                "lat": float(f"{random.uniform(12.0, 29.0):.4f}"),
                "lng": float(f"{random.uniform(72.0, 88.0):.4f}"),
                "status": random.choice(["Online", "Online", "Online", "Offline", "On Leave"]),
                "tasks_assigned": tasks_total,
                "tasks_completed": tasks_done,
                "performance_score": round((tasks_done / tasks_total) * 100, 1),
                "last_checkin": (datetime.now() - timedelta(minutes=random.randint(0, 480))).isoformat(),
                "daily_households_visited": random.randint(5, 40),
            })
    return workers


def _generate_projects(ward_id: str, ward_name: str, constituency_name: str, lat: float, lng: float) -> List[dict]:
    projects = []
    for k in range(random.randint(1, 3)):
        pid = f"PRJ-{ward_id[-2:]}-{k+1:02d}"
        ptype = random.choice(PROJECT_TYPES)
        status = random.choice(["Completed", "Completed", "In Progress", "Pending"])
        street = random.choice(STREETS)
        budget = random.randint(5, 50) * 100000  # 5L to 50L

        projects.append({
            "id": pid,
            "name": f"{ptype} — {street}, {ward_name}",
            "type": ptype,
            "ward": ward_id,
            "ward_name": ward_name,
            "constituency": constituency_name,
            "street": street,
            "status": status,
            "budget": budget,
            "budget_display": f"₹{budget/100000:.1f}L",
            "lat": lat + random.uniform(-0.02, 0.02),
            "lng": lng + random.uniform(-0.02, 0.02),
            "start_date": (datetime.now() - timedelta(days=random.randint(30, 180))).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d") if status == "Completed" else None,
            "affected_residents": random.randint(50, 500),
            "before_image": f"/api/v1/assets/before_{pid.lower()}.jpg",
            "after_image": f"/api/v1/assets/after_{pid.lower()}.jpg",
            "sentiment_before": random.randint(15, 40),
            "sentiment_after": random.randint(55, 90) if status == "Completed" else None,
        })
    return projects


def _generate_complaints(booth_id: str, citizens: List[dict], count: int = 20) -> List[dict]:
    complaints = []
    for i in range(count):
        citizen = random.choice(citizens)
        street = citizen["street"]
        template = random.choice(COMPLAINT_TEMPLATES)
        text = template.format(days=random.randint(3, 30), street=street)

        is_positive = "thank" in text.lower() or "excellent" in text.lower() or "good" in text.lower() or "appreciate" in text.lower()

        complaints.append({
            "id": f"CMP-{booth_id[-3:]}-{i+1:03d}",
            "citizen_id": citizen["id"],
            "citizen_name": citizen["name"],
            "booth_id": booth_id,
            "street": street,
            "text": text,
            "language": random.choice(["English", "English", "Hindi", "Hindi", "Tamil"]),
            "sentiment": "Positive" if is_positive else random.choice(["Negative", "Negative", "Neutral"]),
            "sentiment_score": random.randint(60, 90) if is_positive else random.randint(10, 45),
            "issue_category": citizen["primary_issue"],
            "timestamp": (datetime.now() - timedelta(hours=random.randint(0, 720))).isoformat(),
            "resolved": random.random() < 0.3,
        })
    return complaints


# ─── Master Data Builder ─────────────────────────────────────────

def build_civic_dataset() -> dict:
    """
    Generates the entire Gods-Eye OS demo dataset.
    Returns a dictionary with all entities keyed for fast lookup.
    """
    dataset = {
        "constituencies": [],
        "wards": [],
        "booths": [],
        "citizens": [],
        "workers": [],
        "projects": [],
        "complaints": [],
        "schemes": SCHEMES,
        "stats": {},
    }

    total_citizens = 0
    total_workers = 0

    for c_idx, con in enumerate(CONSTITUENCIES):
        con_data = {**con, "wards": [], "total_population": 0, "avg_sentiment": 0}
        ward_sentiments = []

        for w_idx in range(5):
            ward_id = f"WRD-{con['id'][-2:]}-{w_idx+1:02d}"
            ward_name = WARD_NAMES[c_idx * 5 + w_idx]
            ward_data = {
                "id": ward_id,
                "name": ward_name,
                "constituency_id": con["id"],
                "constituency_name": con["name"],
                "booths": [],
                "lat": con["lat"] + random.uniform(-0.05, 0.05),
                "lng": con["lng"] + random.uniform(-0.05, 0.05),
            }

            booth_ids = []
            booth_sentiments = []

            for b_idx in range(5):
                booth_id = f"BTH-{con['id'][-2:]}-{ward_id[-2:]}-{b_idx+1:03d}"
                booth_ids.append(booth_id)

                citizens = _generate_citizens(booth_id, count=random.randint(300, 500))
                complaints = _generate_complaints(booth_id, citizens, count=random.randint(15, 30))

                # Compute booth-level aggregations
                avg_sentiment = round(sum(c["sentiment_score"] for c in citizens) / len(citizens), 1)
                booth_sentiments.append(avg_sentiment)

                segments = {}
                for c in citizens:
                    seg = c["segment"]
                    segments[seg] = segments.get(seg, 0) + 1

                issue_counts = {}
                for c in citizens:
                    iss = c["primary_issue"]
                    issue_counts[iss] = issue_counts.get(iss, 0) + 1
                top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:3]

                scheme_counts = {}
                for c in citizens:
                    for s in c["enrolled_schemes"]:
                        scheme_counts[s] = scheme_counts.get(s, 0) + 1

                booth_data = {
                    "id": booth_id,
                    "name": f"Booth {b_idx+1} — {ward_name}",
                    "ward_id": ward_id,
                    "ward_name": ward_name,
                    "constituency_id": con["id"],
                    "constituency_name": con["name"],
                    "lat": ward_data["lat"] + random.uniform(-0.015, 0.015),
                    "lng": ward_data["lng"] + random.uniform(-0.015, 0.015),
                    "population": len(citizens),
                    "avg_sentiment": avg_sentiment,
                    "sentiment_label": "Positive" if avg_sentiment > 60 else ("Negative" if avg_sentiment < 40 else "Neutral"),
                    "segments": segments,
                    "top_issues": [{"issue": i[0], "count": i[1]} for i in top_issues],
                    "scheme_coverage": scheme_counts,
                    "key_voters": len([c for c in citizens if c["is_key_voter"]]),
                    "complaints_count": len(complaints),
                    "unresolved_complaints": len([c for c in complaints if not c["resolved"]]),
                }

                dataset["booths"].append(booth_data)
                dataset["citizens"].extend(citizens)
                dataset["complaints"].extend(complaints)
                total_citizens += len(citizens)

                ward_data["booths"].append(booth_id)

            # Ward-level projects
            projects = _generate_projects(ward_id, ward_name, con["name"], ward_data["lat"], ward_data["lng"])
            dataset["projects"].extend(projects)

            # Ward-level workers
            workers = _generate_workers(con["id"], ward_id, booth_ids, count_per_booth=4)
            dataset["workers"].extend(workers)
            total_workers += len(workers)

            ward_sentiments.extend(booth_sentiments)
            dataset["wards"].append(ward_data)
            con_data["wards"].append(ward_id)

        con_data["total_population"] = sum(
            b["population"] for b in dataset["booths"] if b["constituency_id"] == con["id"]
        )
        con_data["avg_sentiment"] = round(sum(ward_sentiments) / len(ward_sentiments), 1) if ward_sentiments else 50.0
        dataset["constituencies"].append(con_data)

    # Global stats
    dataset["stats"] = {
        "total_constituencies": len(dataset["constituencies"]),
        "total_wards": len(dataset["wards"]),
        "total_booths": len(dataset["booths"]),
        "total_citizens": total_citizens,
        "total_workers": total_workers,
        "total_projects": len(dataset["projects"]),
        "total_complaints": len(dataset["complaints"]),
        "total_schemes": len(SCHEMES),
        "national_avg_sentiment": round(
            sum(c["avg_sentiment"] for c in dataset["constituencies"]) / len(dataset["constituencies"]), 1
        ),
        "generated_at": datetime.now().isoformat(),
    }

    return dataset
