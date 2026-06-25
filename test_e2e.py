import asyncio
import httpx
import time
import sys

API_URL = "http://localhost:8000/api/v1"

async def run_test():
    print("--- Starting End-to-End Pipeline Test ---")
    
    async with httpx.AsyncClient() as client:
        # 1. Create an ICP Config first
        icp_data = {
            "name": "Default Test ICP",
            "company_size_min": 10,
            "company_size_max": 1000,
            "target_industries": ["Technology", "Software", "AI"],
            "required_tech_stack": ["React", "Python", "FastAPI"],
            "min_seniority": "Director or above",
            "disqualifiers": ["Agency", "Consulting"],
            "scoring_weights": {"icp_fit": 0.6, "buying_signals": 0.4},
            "criterion_weights": {
                "company_size": 20,
                "industry": 20,
                "tech_stack": 20,
                "seniority": 20,
                "disqualifier_penalty": 20
            },
            "score_threshold": 50,
            "product_description": "Alfaleus AI helps sales teams automate their lead research.",
            "value_proposition": "We save you 20 hours a week by automatically reading news, websites, and LinkedIn."
        }
        resp = await client.post(f"{API_URL}/icp", json=icp_data)
        if resp.status_code == 200:
            print("[SUCCESS] ICP Configuration Set")
        else:
            print(f"[FAIL] Failed to set ICP: {resp.text}")

        # 2. Upload a Lead via Extension Endpoint
        lead_data = {
            "name": "Satya Nadella",
            "title": "CEO",
            "company": "Microsoft",
            "url": "https://www.microsoft.com",
            "linkedin_url": "https://www.linkedin.com/in/satyanadella/"
        }
        resp = await client.post(f"{API_URL}/leads/extension", json=lead_data)
        if resp.status_code != 200:
            print(f"[FAIL] Failed to submit lead: {resp.text}")
            return
            
        lead = resp.json()
        lead_id = lead["id"]
        print(f"[SUCCESS] Lead Submitted. ID: {lead_id}")
        
        # 3. Poll for completion
        print("Waiting for enrichment pipeline to finish...")
        max_retries = 90 # 270 seconds timeout
        for i in range(max_retries):
            resp = await client.get(f"{API_URL}/leads/{lead_id}")
            data = resp.json()
            status = data.get("status")
            print(f"   Status: {status}")
            if status in ["enriched", "failed"]:
                break
            await asyncio.sleep(3)
            
        # 4. Verify data
        print("\n--- Enrichment Results ---")
        resp = await client.get(f"{API_URL}/leads/{lead_id}")
        data = resp.json()
        
        enrichment = data.get("enrichment") or {}
        drafts = data.get("drafts", [])
        sequences = data.get("sequences", [])
        score_history = data.get("score_history", [])
        
        print(f"Company Size: {enrichment.get('company_size')} (Conf: {enrichment.get('company_size_confidence')})")
        print(f"Tech Stack: {enrichment.get('tech_stack')} (Conf: {enrichment.get('tech_stack_confidence')})")
        print(f"Funding: {enrichment.get('funding_status')} (Conf: {enrichment.get('funding_confidence')})")
        print(f"Industry: {enrichment.get('industry')}")
        print(f"Seniority: {enrichment.get('contact_seniority')} (Conf: {enrichment.get('seniority_confidence')})")
        
        print("\n--- Buying Signals ---")
        signals = enrichment.get('buying_signals', [])
        for sig in signals:
            print(f"- {sig.get('signal')} (Strength: {sig.get('strength')})")
            
        print("\n--- Scoring ---")
        print(f"ICP Score: {data.get('icp_score')}")
        print(f"Total Score: {data.get('total_score')}")
        
        print(f"\n--- Drafts ({len(drafts)}) ---")
        for d in drafts:
            print(f"Tone: {d.get('tone')}")
            print(f"Subject: {d.get('subject')}")
        
        print("\n--- CRM Sync ---")
        crm = data.get("crm_sync")
        print(f"Status: {crm.get('status') if crm else 'None'}")
        
        print("\n--- Bonus Features Check ---")
        emails = enrichment.get('email_candidates', [])
        print(f"Email Finder Candidates: {len(emails)}")
        print(f"Score History Snapshot Count: {len(score_history)}")
        print(f"Sequence Steps Count: {len(sequences[0]['steps']) if sequences else 0}")
        
if __name__ == "__main__":
    asyncio.run(run_test())
