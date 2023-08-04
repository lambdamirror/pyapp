import warnings

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from _services.mongo.service import MongoDbClient
from api.app import api_app, shutdown_api, startup_api
from auth.app import auth_app, startup_auth
from config.settings import *
from stream.app import startup_stream, stream_app
from webhooks.app import webhooks_app

# from setup.service import load_dataset


warnings.filterwarnings("ignore")

app = FastAPI()
app.mount('/auth', auth_app)
app.mount('/api', api_app)
app.mount('/ws', stream_app)
app.mount('/webhooks', webhooks_app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.split(" "),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    # await load_dataset()
    await startup_auth()
    await startup_api()
    startup_stream()

@app.on_event("shutdown")
async def shutdown():
    MongoDbClient().disconnect()
    await shutdown_api()

@app.get('/')
async def root():
    return HTMLResponse('<body><a href="/auth/google/login">Log In</a></body>')

@app.get('/token')
async def token(request: Request):
    return HTMLResponse('''
        <script>
        function send(){
            var req = new XMLHttpRequest();
            req.onreadystatechange = function() {
                if (req.readyState === 4) {
                    console.log(req.response);
                    if (req.response["result"] === true) {
                        window.localStorage.setItem('jwt', req.response["access_token"]);
                    }
                }
            }
            req.withCredentials = true;
            req.responseType = 'json';
            req.open("get", "/auth/google/token?"+window.location.search.substr(1), true);
            req.send("");
        }
        </script>
        <button onClick="send()">Get FastAPI JWT Token</button>
        <button onClick='fetch("%s/api/").then(
            (r)=>r.json()).then((msg)=>{console.log(msg)});'>
        Call Unprotected API
        </button>
        <button onClick='fetch("%s/auth/user/profile").then(
            (r)=>r.json()).then((msg)=>{console.log(msg)});'>
        Call Protected API without JWT
        </button>
        <button onClick='fetch("%s/auth/user/profile",{
            headers:{
                "Authorization": "Bearer " + window.localStorage.getItem("jwt")
            },
        }).then((r)=>r.json()).then((msg)=>{console.log(msg)});'>
        Call Protected API wit JWT
        </button>
    ''' % (API_URL, API_URL, API_URL))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=HOST,
        reload=DEBUG_MODE,
        port=PORT,
        # workers=2
    )

