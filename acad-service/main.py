from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
from contextlib import contextmanager

app = FastAPI(title="Product Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'products'),
    'user': os.getenv('DB_USER', 'productuser'),
    'password': os.getenv('DB_PASSWORD', 'productpass')
}

def row_to_dict(row):
    if row is None:
        return None
    return dict(row)

class Mahasiswa(BaseModel):
    nim: str
    nama: str
    jurusan: str
    angkatan: int = Field(ge=0)

# Database connection pool
@contextmanager
def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

@app.on_event("startup")
async def startup_event():
    try:
        with get_db_connection() as conn:
            print("Acad Service: Connected to PostgreSQL")
    except Exception as e:
        print(f"Acad Service: PostgreSQL connection error: {e}")

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "Acad Service is running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/acad/mahasiswa")
async def get_mahasiswas():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM mahasiswa"

            cursor.execute(query)
            rows = cursor.fetchall()

            return [{"nim": row[0], "nama": row[1], "jurusan": row[2], "angkatan": row[3]} for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/api/acad/ips")
async def get_ips(nim:str):
     try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
                        
            query = "select m.nim, m.nama, m.jurusan, krs.nilai, mk.sks  from mahasiswa m join krs on krs.nim = m.nim join mata_kuliah mk ON mk.kode_mk = krs.kode_mk where m.nim = %s"
            
            cursor.execute(query,(nim,))
            rows = cursor.fetchall()

            grade_map = {
                "A": 4.0,
                "B+": 3.5,
                "B": 3.0,
                "B-": 2.75, 
                "C+": 2.5,
                "C": 2.0,
                "D": 1.0,
                "E": 0.0,
            }
            
            total_bobot = 0.0
            total_sks = 0 

            for row in rows:
                nilai = row[3]
                sks=row[4]
                
                if isinstance(nilai, str):
                    nilai = nilai.strip()

                bobot = grade_map[nilai]
                total_bobot += bobot * sks
                total_sks += sks

            ips = round(total_bobot / total_sks, 2)

            return {"nim" : nim, "nama" : row[1], "jurusan" : row[2], "total_sks" : total_sks, "ips" : ips}

     except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))