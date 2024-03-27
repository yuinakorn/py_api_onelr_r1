from fastapi import FastAPI

from routers import pregs_router, infants_router, dashboard_router, progress_router, auth_router

from fastapi.middleware.cors import CORSMiddleware

# app = FastAPI(docs_url=None, redoc_url=None)
app = FastAPI(docs_url="/api-docs", redoc_url=None)

# Allow requests from all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    print("Server startup event")


@app.on_event("shutdown")
async def shutdown_event():
    print("Server shutdown event")


app.include_router(auth_router.router)
app.include_router(pregs_router.router)
app.include_router(infants_router.router)
app.include_router(progress_router.router)
app.include_router(dashboard_router.router)
