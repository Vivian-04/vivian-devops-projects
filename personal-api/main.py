from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Create the API application
app = FastAPI()

# Endpoint 1: GET /
@app.get("/")
async def root():
    """
    Root endpoint - tells reviewer API is running
    
    Returns:
        JSON: {"message": "API is running"}
    """
    return JSONResponse(
        status_code=200,
        content={"message": "API is running"},
        media_type="application/json"
    )


# Endpoint 2: GET /health
@app.get("/health")
async def health():
    """
    Health check endpoint - for monitoring
    
    Returns:
        JSON: {"message": "healthy"}
    """
    return JSONResponse(
        status_code=200,
        content={"message": "healthy"},
        media_type="application/json"
    )


# Endpoint 3: GET /me
@app.get("/me")
async def me():
    """
    Personal info endpoint - your details
    
    Returns:
        JSON: {"name": "...", "email": "...", "github": "..."}
    """
    return JSONResponse(
        status_code=200,
        content={
            "name": "Vivian Nduka",
            "email": "ifechukwudenduka@gmail.com",
            "github": "https://github.com/Vivian-04"
        },
        media_type="application/json"
    )


if __name__ == "__main__":
    import uvicorn
    # Run on port 8000 (local development)
    uvicorn.run(app, host="0.0.0.0", port=8000)
