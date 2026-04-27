#!/usr/bin/env python3
import sys
sys.path.insert(0, '/workspace/ee9a60d3-53a4-4fe3-abd7-e9f3eea949bc/sessions/agent_e418d70e-7f00-41a1-9dd0-21285873c140')

from app.main import app
import uvicorn

if __name__ == "__main__":
    print("Starting CEREBUS Signal Guard on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)