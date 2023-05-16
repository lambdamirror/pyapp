from utils.logger import logger
from config.settings import *
from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import HTMLResponse

from .service import auth, authorize_redirect

router = APIRouter()

@router.get('/login')
async def get_login(request: Request, client_id: str):
    logger.info('Google Account Login on Gateway')
    result = await authorize_redirect(request, client_id)
    return result


@router.get('/redirect')
async def get_redirect(request: Request):
    return HTMLResponse("""
        <body onload="send()">
        <script>
        function send(){
            var req = new XMLHttpRequest();
            req.onreadystatechange = function() {
                if (req.readyState === 4) {
                    console.log(req.response);
                    if (req.response["result"] === true) {
                        window.localStorage.setItem('jwt', req.response["access_token"]);
                    }
                    location.href = '%s/google-login?token=' + req.response["access_token"];
                }
            }
            req.withCredentials = true;
            req.responseType = 'json';
            req.open("get", "/auth/google/token?"+window.location.search.substr(1), true);
            req.send("");
        }
        </script>
        </body>
    """ % (FRONT_END_URL))


@router.get('/token')
async def get_token(request: Request, background_tasks: BackgroundTasks):
    logger.info('Google Token Authorization on Gateway')
    return await auth(request, background_tasks)
