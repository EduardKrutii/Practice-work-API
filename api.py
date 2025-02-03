from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

fake_db = []

class Appointment(BaseModel):
    id: int
    patient_name: str
    doctor_name: str
    date: datetime
    status: str

class User(BaseModel):
    username: str
    password: str
    role: str

fake_users_db = {
    "admin": {"username": "admin", "password": "admin123", "role": "admin"},
    "user": {"username": "user", "password": "user123", "role": "user"}
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user = fake_users_db.get(username)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

app = FastAPI()

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or form_data.password != user["password"]:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/appointments", response_model=List[Appointment])
def get_appointments(user: dict = Depends(get_current_user)):
    return fake_db

@app.post("/appointments", response_model=Appointment)
def create_appointment(appointment: Appointment, user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    fake_db.append(appointment)
    return appointment

@app.delete("/appointments/{appointment_id}")
def delete_appointment(appointment_id: int, user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    global fake_db
    fake_db = [a for a in fake_db if a.id != appointment_id]
    return {"message": "Appointment deleted"}

@app.patch("/appointments/{appointment_id}", response_model=Appointment)
def update_appointment(appointment_id: int, appointment: Appointment, user: dict = Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    existing_appointment = next((a for a in fake_db if a.id == appointment_id), None)
    if not existing_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    existing_appointment.patient_name = appointment.patient_name
    existing_appointment.doctor_name = appointment.doctor_name
    existing_appointment.date = appointment.date
    existing_appointment.status = appointment.status

    return existing_appointment


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)