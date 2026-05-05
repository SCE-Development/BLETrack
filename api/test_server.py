from fastapi import FastAPI, HTTPException
import subprocess
import os
app = FastAPI()

@app.get("/")
async def execute_curl():
    """
    Executes the predefined curl command and returns the output.
    """
    try:
        # Run the curl command
        result = subprocess.run(
            ["curl", "-X", "GET", f"{os.getenv('ESP_IP')}/json/devices/"],
            capture_output=True,  # Captures stdout and stderr
            text=True,            # Returns strings instead of bytes
            check=True            # Raises CalledProcessError if the exit code is non-zero
        )
        
        # Return the output of the curl command
        return {
            "status": "success",
            "output": result.stdout.strip()
        }
    
    except subprocess.CalledProcessError as e:
        # Handles errors if the curl command itself fails (e.g., bad URL, connection refused)
        raise HTTPException(
            status_code=500, 
            detail={"error": "Curl command failed", "stderr": e.stderr.strip()}
        )
    except Exception as e:
        # Handles any other unexpected Python errors
        raise HTTPException(
            status_code=500, 
            detail={"error": "An unexpected error occurred", "message": str(e)}
        )