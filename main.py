# server.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sqlite3
from datetime import datetime
import os

app = FastAPI(title="ECO Весна Leaderboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "leaderboard.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            username TEXT NOT NULL,
            score INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


init_db()


class ScoreSubmission(BaseModel):
    user_id: str
    username: str
    score: int


class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    score: int


@app.get("/")
async def root():
    return {"status": "ok", "message": "ECO Весна Leaderboard API"}


@app.post("/submit_score")
async def submit_score(data: ScoreSubmission):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO scores (user_id, username, score, timestamp) VALUES (?, ?, ?, ?)",
            (data.user_id, data.username, data.score, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        return {"status": "ok", "message": f"Score {data.score} saved for {data.username}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT username, MAX(score) as best_score
        FROM scores
        GROUP BY user_id
        ORDER BY best_score DESC
        LIMIT 10
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [
        LeaderboardEntry(rank=i + 1, username=row[0], score=row[1])
        for i, row in enumerate(rows)
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)