## Employee Training Assistant  

This project implements an end-to-end employee training assistant with:  
- Authentication flow  
- RAG queries  
- Reset conversation  
- Parallel user support  

A demo video of the application is attached.

Run the Entire System with Docker (Backend + Frontend)

Both services are fully containerized and orchestrated via **docker-compose**.

## 1. Create a `.env` file  
In the **root directory** (same folder as `docker-compose.yml`) create:

> The repository includes `.env.example` to show which variables are required.  
> Do **NOT** commit `.env` — it contains secrets.

---

## 2. Start the system
docker compose up --build

---

## 3. open UI
Once Docker is running:
Open the UI in your browser:

http://localhost:3000

The frontend automatically connects to the backend container on port 8000.

---

## UI Notes

The chat includes a Send button, and you can also press Enter to send messages.

A Reset button is available to fully clear the conversation and start a new session.

After successful authentication, a “Connected” indicator appears at the bottom of the screen to confirm successful login.

