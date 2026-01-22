import firebase_admin
from firebase_admin import credentials, firestore

firebase_admin.initialize_app()

db = firestore.client()

print("Connected to Firestore")
print("Collections:", [c.id for c in db.collections()])
