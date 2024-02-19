import logging
from fastapi import FastAPI
import os, sys
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), '../common/libs/misc')))
import download


logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)



app = FastAPI()



@app.get("/")
async def root():
	return {"message": "Hello World"}



@app.get("/health")
async def health():
	return {"message": "Hello World"}


app.post("/get_file_from_url_into_dir")(download.get_file_from_url_into_dir)


if __name__ == "__main__":
	import uvicorn
	uvicorn.run(app, port=6457)