from app.auth.jwt_handler import (
    create_access_token,
    verify_access_token,
)

token = create_access_token(
    {"sub": "nishant"}
)

print("Token:\n", token)

payload = verify_access_token(token)

print("\nDecoded Payload:")
print(payload)