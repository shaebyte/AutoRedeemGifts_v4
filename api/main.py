from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from .limiter import limiter
from app.config import ALLOWED_ORIGINS
from .auth import router as auth_router
from .routes.accounts import router as accounts_router
from .routes.gift_codes import router as codes_router
from .routes.redeem_attempts import router as redeem_router

app = FastAPI(title="AutoRedeemGifts API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(accounts_router)
app.include_router(codes_router)
app.include_router(redeem_router)