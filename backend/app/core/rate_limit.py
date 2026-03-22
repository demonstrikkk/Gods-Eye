from slowapi import Limiter
from slowapi.util import get_remote_address

# Global API throttling to protect expensive LLM/OSINT paths.
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute", "2000/day"])
