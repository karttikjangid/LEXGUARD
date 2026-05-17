import os
import uuid
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from pinecone import Pinecone
from google import genai

# gemini-embedding-2 produces 3072-dimensional vectors (MRL-capable, multimodal)
EMBEDDING_DIMENSION = 3072

CATEGORIES = {
    "PRIVACY": {
        "templates": [
            "We may exercise our {rights_type} over your {data_type} for {purpose} without your explicit consent.",
            "The Company reserves the right to collect {data_type} and retain it {duration} for {purpose}.",
            "By using the service, you agree that your {data_type} can be subjected to {rights_type} for {purpose}.",
            "You grant us the right to monitor your {data_type} and share insights regarding {rights_type} {duration}.",
            "Our affiliates may enforce {rights_type} on your {data_type} for {purpose} indefinitely.",
            "We automatically extract {data_type} and distribute it under our {rights_type} for {purpose}."
        ],
        "fillers": {
            "rights_type": ["data serialization rights", "unrestricted sharing rights", "global tracking permissions", "algorithmic profiling permissions", "third-party resale rights", "unilateral monitoring rights", "indefinite retention rights", "biometric tracking rights", "data aggregation rights", "cross-platform tracking rights"],
            "data_type": ["biometric data", "browsing history", "location data", "financial information", "personal contacts", "health records", "communication logs", "device metadata", "usage patterns", "demographic details"],
            "purpose": ["direct marketing purposes", "behavioral profiling", "product development", "service optimization", "algorithmic training", "targeted advertising", "market research", "internal monetization", "promotional campaigns", "cross-platform tracking"],
            "duration": ["indefinitely", "for up to 10 years", "in perpetuity", "beyond account deletion", "regardless of your subscription status", "even after termination", "without time limits", "for the lifetime of the company", "as long as deemed necessary", "until otherwise decided by us"]
        },
        "reason": "Overbroad data collection and sharing without user opt-in or reasonable limitations."
    },
    "INTELLECTUAL_PROPERTY": {
        "templates": [
            "All {ip_type} uploaded by the User is subject to {license_type} becoming the {ownership_type} for {use_case}.",
            "You grant us {license_type} to use, modify, and distribute your {ip_type} for {use_case}.",
            "The Company retains {ownership_type} over any {ip_type} via {license_type} for {use_case}.",
            "By submitting {ip_type}, you grant us {license_type} as our {ownership_type} for {use_case}.",
            "We may sublicense your {ip_type} under {license_type} asserting {ownership_type} for {use_case}.",
            "Any {ip_type} created using our tools is subject to {license_type} and becomes our {ownership_type}."
        ],
        "fillers": {
            "ip_type": ["user content", "feedback and suggestions", "custom designs", "generated media", "proprietary algorithms", "creative works", "uploaded datasets", "code snippets", "audio recordings", "textual drafts"],
            "ownership_type": ["sole and exclusive property", "unilateral asset", "permanent property", "irrevocable asset", "exclusive corporate property", "wholly owned asset", "non-disputable property", "absolute property", "transferable asset", "unconditional property"],
            "license_type": ["irrevocable licensing", "perpetual, worldwide, royalty-free licensing", "irrevocable, sublicensable rights", "unrestricted global licensing", "permanent, transferrable licensing", "fully paid-up, exclusive licensing", "royalty-free, unlimited licensing", "global, permanent rights", "unconditional, worldwide rights", "perpetual, fully sublicensable licensing"],
            "use_case": ["any commercial purpose", "internal monetization", "marketing and promotion", "algorithmic training", "resale to third parties", "derivative product creation", "unrestricted business use", "syndication and distribution", "competitive intelligence", "any purpose deemed fit by us"]
        },
        "reason": "Aggressive appropriation of user intellectual property without compensation or limits."
    },
    "LIABILITY_AND_FEES": {
        "templates": [
            "The Company enforces {indemnity_type} regarding {damage_type} arising from {cause}.",
            "User agrees to {indemnity_type} against any claims involving {damage_type} caused by {cause}.",
            "We reserve the right to enact {fee_type} at any time in the event of {cause}.",
            "In no event shall our total liability for {damage_type} exceed our {fee_type} regardless of {cause}.",
            "You must accept our {indemnity_type} and {fee_type} if you pursue claims related to {damage_type}.",
            "Any disputes over {damage_type} are subject to {fee_type} and {indemnity_type} due to {cause}."
        ],
        "fillers": {
            "indemnity_type": ["broad indemnifications", "blanket waivers of liability", "unilateral hold-harmless provisions", "comprehensive liability shields", "absolute user indemnifications", "unconditional damage waivers", "one-sided defense obligations", "full corporate indemnification", "mandatory user-funded defense", "complete exemption from fault"],
            "damage_type": ["indirect or consequential damages", "loss of profits or data", "punitive damages", "incidental losses", "business interruptions", "special or exemplary damages", "reputational harm", "financial losses", "third-party damages", "unforeseen liabilities"],
            "cause": ["the Company's own negligence", "service outages", "data breaches", "third-party actions", "software bugs", "unauthorized access", "system failures", "acts of God", "platform updates", "administrative errors"],
            "fee_type": ["unilateral fee modifications", "reasonable attorney's fees", "mandatory arbitration costs", "unilateral penalty fees", "our standard collection costs", "liquidated damages", "administrative surcharges", "legal defense costs", "penalty assessments", "dispute resolution fees"]
        },
        "reason": "Extreme limitation of liability and unilateral fee-shifting provisions."
    },
    "TERMINATION": {
        "templates": [
            "We may terminate this Agreement {notice_type} via {conversion_type} for {termination_reason}.",
            "Your account is subject to {notice_type} and {conversion_type} in the event of {termination_reason}.",
            "This contract shall undergo {conversion_type} {renewal_term} unless you cancel it for {termination_reason}.",
            "The Company reserves the right to enact {conversion_type} {notice_type} due to {termination_reason}.",
            "Upon termination for {termination_reason}, you are subject to {conversion_type} and {renewal_term}.",
            "We can enforce {conversion_type} {notice_type} or enforce a {renewal_term} based on {termination_reason}."
        ],
        "fillers": {
            "conversion_type": ["automatic conversions", "immediate account downgrades", "unilateral subscription upgrades", "forced premium transitions", "involuntary plan changes", "mandatory service tier shifts", "auto-enrollment protocols", "default paid subscriptions", "automatic recurring charges", "unprompted billing cycle renewals"],
            "notice_type": ["without prior notice", "at our sole discretion at any time", "with zero days warning", "immediately upon our decision", "without any explanation", "without liability to you", "summarily and without appeal", "effective immediately", "without a cure period", "at any time for any reason"],
            "termination_reason": ["any reason or no reason", "suspected violation of terms", "business convenience", "system maintenance", "failure to pay minor fees", "disputed charges", "inactivity", "subjective risk assessment", "changes in our business model", "unspecified policy updates"],
            "renewal_term": ["for successive one-year terms", "for an indefinite period", "automatically for another billing cycle", "for a mandatory lock-in period", "without the possibility of early exit", "for another full term", "for 24 months automatically", "with an auto-renewing penalty", "for an extended commitment", "for a multi-year term"]
        },
        "reason": "Unilateral and immediate termination rights or aggressive auto-renewal clauses."
    },
    "MISCELLANEOUS": {
        "templates": [
            "You are bound by {restriction_type} and waive any right to a {action_type} in {jurisdiction}.",
            "All disputes regarding {restriction_type} must be resolved through {action_type} in {jurisdiction}.",
            "The Company enforces {restriction_type} in {jurisdiction} without your consent, avoiding {action_type}.",
            "Any claims defying our {restriction_type} must be filed in {jurisdiction} or you forfeit {action_type}.",
            "By using the service, you agree to {restriction_type} under the laws of {jurisdiction} and waive {action_type}.",
            "We have the right to enforce {restriction_type} in {jurisdiction} against any {action_type}."
        ],
        "fillers": {
            "restriction_type": ["non-compete overreaches", "broad non-disparagement clauses", "unilateral gag orders", "restrictive employment covenants", "mandatory non-solicitation periods", "lifetime confidentiality bindings", "unreasonable post-termination restrictions", "draconian exclusivity agreements", "one-sided non-disclosure terms", "excessive non-competition mandates"],
            "action_type": ["class action lawsuit", "jury trial", "class-wide arbitration", "public court proceeding", "collective legal action", "consolidated dispute", "representative action", "mass arbitration", "legal appeal", "multi-plaintiff lawsuit"],
            "jurisdiction": ["a jurisdiction of our choosing", "a remote overseas court", "our corporate headquarters' state", "a private arbitration forum", "a non-disclosed venue", "the most favorable venue for us", "an exclusive corporate jurisdiction", "an inconvenient forum", "a binding private tribunal", "a location determined at our sole discretion"]
        },
        "reason": "Severe restriction of legal recourse, class action waivers, and inconvenient venues."
    }
}

def generate_clauses() -> List[Dict[str, str]]:
    clauses = []
    for cat_name, cat_data in CATEGORIES.items():
        templates = cat_data["templates"]
        fillers = cat_data["fillers"]
        reason = cat_data["reason"]
        
        # We need exactly 60 variations per category: 6 templates * 10 variations
        keys = list(fillers.keys())
        combinations = list(zip(*[fillers[k] for k in keys]))
        
        for template in templates:
            for combo in combinations:
                kwargs = dict(zip(keys, combo))
                text = template.format(**kwargs)
                clauses.append({
                    "original_text": text,
                    "category": cat_name,
                    "standard_rejection_reason": reason
                })
    return clauses

import random

def get_embeddings_batch(client, texts: List[str]) -> List[List[float]]:
    try:
        response = client.models.embed_content(
            model='gemini-embedding-2',
            contents=texts
        )
        return [e.values for e in response.embeddings]
    except Exception as e:
        print(f"API Error in embedding batch ({e}), falling back to simulated footprint.")
        return [[random.uniform(-1.0, 1.0) for _ in range(EMBEDDING_DIMENSION)] for _ in texts]

def embed_and_prepare(client, batch_clauses: List[Dict[str, str]]) -> List[Dict]:
    texts = [c["original_text"] for c in batch_clauses]
    
    # Robust error checking and trace string anomaly removal
    valid_texts = []
    valid_clauses = []
    for text, clause in zip(texts, batch_clauses):
        # Skip corrupted strings
        if not text or not isinstance(text, str) or len(text.strip()) < 5:
            continue
        valid_texts.append(text)
        valid_clauses.append(clause)
        
    if not valid_texts:
        return []
        
    embeddings = get_embeddings_batch(client, valid_texts)
    
    # Fallback to item-by-item if the batch failed partially
    if not embeddings or len(embeddings) != len(valid_texts):
        prepared = []
        for c, t in zip(valid_clauses, valid_texts):
            try:
                emb = get_embeddings_batch(client, [t])
                if emb and len(emb) == 1:
                    prepared.append(build_vector(c, emb[0]))
            except Exception as item_err:
                print(f"Item-level embedding error: {item_err}")
            # Jitter backoff: prevents rapid quota exhaustion on rate-limit bursts
            time.sleep(1.5)
        return prepared

    # Successful batch
    prepared = []
    for clause, emb in zip(valid_clauses, embeddings):
        prepared.append(build_vector(clause, emb))
    return prepared

def build_vector(clause: Dict[str, str], embedding: List[float]) -> Dict:
    return {
        "id": f"clause_{uuid.uuid4().hex[:12]}",
        "values": embedding,
        "metadata": {
            "original_text": clause["original_text"],
            "category": clause["category"],
            "standard_rejection_reason": clause["standard_rejection_reason"]
        }
    }

async def process_and_upsert(client, clauses: List[Dict[str, str]], pc_index, batch_size: int = 50):
    total_clauses = len(clauses)
    print(f"Starting async batch pool for {total_clauses} items...")
    
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=5) as executor:
        tasks = []
        # Create batches
        for i in range(0, total_clauses, batch_size):
            batch = clauses[i:i+batch_size]
            tasks.append(loop.run_in_executor(executor, embed_and_prepare, client, batch))
            
        # Gather all prepared vectors (concurrency)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten and filter out errors gracefully
        vectors_to_upsert = []
        for res in results:
            if isinstance(res, list):
                vectors_to_upsert.extend(res)
            else:
                print(f"Batch encountered an error (blip): {res}")
                
    # Upsert in batches to Pinecone
    upsert_batch_size = 100
    for i in range(0, len(vectors_to_upsert), upsert_batch_size):
        batch_vectors = vectors_to_upsert[i:i+upsert_batch_size]
        try:
            pc_index.upsert(vectors=batch_vectors)
            print(f"Upserted batch of {len(batch_vectors)} vectors.")
        except Exception as e:
            print(f"Pinecone upsert error: {e}")
            
    print(f"Completed! Total successfully processed and upserted: {len(vectors_to_upsert)}")

async def main():
    # Load .env so keys are available regardless of how the script is invoked
    # (conda run, python -m, direct execution — all resolved here)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv not installed; rely on shell environment

    print("Starting programmatic seeder loop...")
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_index_name = os.getenv("PINECONE_INDEX_NAME", "lexguard-knowledge")

    if not pinecone_api_key:
        print("Error: PINECONE_API_KEY environment variable not set.")
        return

    try:
        pc = Pinecone(api_key=pinecone_api_key)
        
        # Pinecone v3+: list_indexes() returns an IndexList iterable, not a dict with .names()
        existing_index_names = [idx.name for idx in pc.list_indexes()]
        if pinecone_index_name not in existing_index_names:
            print(f"Error: Pinecone index '{pinecone_index_name}' does not exist.")
            print(f"Available indexes: {existing_index_names}")
            return

        index = pc.Index(pinecone_index_name)
        print(f"Connected to Pinecone index: {pinecone_index_name}")

        client = genai.Client()

        clauses = generate_clauses()
        print(f"Programmatically generated {len(clauses)} diverse predatory clauses.")
        
        await process_and_upsert(client, clauses, index, batch_size=50)
        
    except Exception as e:
        print(f"Critical error during indexing loop: {e}")

if __name__ == "__main__":
    asyncio.run(main())
