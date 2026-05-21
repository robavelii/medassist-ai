import asyncio
import json
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY_SECRET", "")
BASE_URL = "http://localhost:7000/api/v1"

HEADERS = {"Content-Type": "application/json", "X-API-Key": API_KEY}


async def test_emergency_triage():
    print("--- Testing Emergency Triage ---")
    payload = {
        "vitals": {
            "systolic_bp": "150",
            "diastolic_bp": "95",
            "pulse_rate": "110",
            "respiratory_rate": "22",
            "temperature": "38.5",
            "spo2": "94",
            "weight": "80",
            "height": "175",
        },
        "patient_info": {
            "patient_id": "test-patient-002",
            "gender": "male",
            "age": 55,
            "patient_location": "London, UK",
        },
        "chief_complaint": "Severe chest pain radiating to the jaw, shortness of breath, sweating.",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/clinical/emergency-triage",
            headers=HEADERS,
            json=payload,
            timeout=60.0,
        )

        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(response.text)


async def test_diagnosis():
    print("\n--- Testing Diagnosis ---")
    payload = {
        "vitals": {
            "systolic_bp": "120",
            "diastolic_bp": "80",
            "pulse_rate": "72",
            "respiratory_rate": "16",
            "temperature": "37.0",
        },
        "patient_info": {
            "patient_id": "test-patient-003",
            "gender": "female",
            "age": 30,
        },
        "chief_complaint": "Frequent urination, increased thirst, and unexplained weight loss over the past month.",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/clinical/diagnosis",
            headers=HEADERS,
            json=payload,
            timeout=60.0,
        )

        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(response.text)


async def main():
    if not API_KEY:
        print("Error: API_KEY_SECRET not found in .env")
        return

    print(f"Using API Key: {API_KEY[:5]}...{API_KEY[-5:]}")
    await test_emergency_triage()
    await test_diagnosis()


if __name__ == "__main__":
    asyncio.run(main())
