from fastapi import FastAPI, UploadFile, File,HTTPException, status, Header, Depends
import aiofiles
import cv2
import os
from pydantic import BaseModel

dirname = os.path.dirname(__file__)

def get_relative_path(relative_path):
    filename = os.path.join(dirname, relative_path)
    return filename

app = FastAPI()

def get_duration(filename):
    video = cv2.VideoCapture(filename)
    frames = video.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = int(video.get(cv2.CAP_PROP_FPS))
    seconds = int(frames / fps)
    return seconds 

@app.post("/")
async def root(file: UploadFile = File(...)):
    if file.content_type != "video/mp4" and file.content_type != "video/x-matroska":
        raise HTTPException(400, detail="Invalid document type : Accepted mp4, mkv")
    contents = await file.read()
    if(len(contents) > 1073741824): 
        raise HTTPException(400, detail="File size too big !")

    out_file_path = get_relative_path(f'..\\videos\\{file.filename}')

    async with aiofiles.open(out_file_path, 'wb') as out_file:
        await out_file.write(contents)

    duration = get_duration(out_file_path)
    if(duration > (10 *60)):
        os.remove(out_file_path)
        raise HTTPException(400, detail="Video length cannot be more than 10 minutes")

    return {"file_name": file.filename, "content-type" : file.content_type, "file_size" : len(contents)} 

def get_files(dirpath):
    data = os.listdir(dirpath)
    print(data)
    files = []
    for i in data:
        full_path = f"{dirpath}\\{i}" 
        if(os.path.isfile(full_path)):
            files.append(i)
    return files


@app.get("/being-uploaded")
def get_being_uploaded():
    dirpath = get_relative_path("..\\videos")
    return {
        'files': get_files(dirpath)
    }


def validate(size, length, file_type):
    if(size > (1024 * 1024 * 1024)): 
        raise HTTPException(400, detail="File too Large !")
    if(length > (10 * 60)):
        raise HTTPException(400, detail="File length too large")
    if(file_type != 'mp4' and file_type != 'mkv'):
        raise HTTPException(400, detail="Invalid file type")
    return True

class CostRequest(BaseModel):
    size:int
    length:int
    file_type:str

# Length in seconds
# Size in bytes
# Type in string
@app.post('/compute-cost')
def compute_cost(req : CostRequest):
    validate(req.size, req.length, req.file_type)

    charge = 0.0
    
    if(req.size < (500 *1024*1024)):
        # $5
        charge = 5.0
    else:
        # $ 12.5
        charge = 12.5
    
    if(req.length < ((6 * 60) + 18)):
        # $ 12.5
        charge += 12.5
    else:
        # $ 20
        charge += 20 
    
    return {"charge" : charge, "currency" : "USD"}
