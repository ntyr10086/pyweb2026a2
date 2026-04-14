import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc = {
  "name": "張煊佩",
  "mail": "12345@pu.edu.tw",
  "lab": 115
}

doc_ref = db.collection("靜宜資管").document("Hsuan")
doc_ref.set(doc)
