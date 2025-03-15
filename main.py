# ไฟล์ main.py 
from typing import Union
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import Request, Response, FastAPI, File, UploadFile
import asyncio
import uvicorn
from typing import Dict, List, Any
import random
import time
from ultralytics import YOLO
from yolo_obj import process_yolo
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.task_queue = asyncio.Queue()

task_id = str
results: Dict[task_id, Any] = {}

SERVER_URL = "http://localhost:8000"
# ให้ FastAPI เปิด folder cropped_images ให้เข้าถึงได้ทาง URL
app.mount("/cropped_images", StaticFiles(directory="cropped_images"), name="cropped_images")

# class Item(BaseModel):
#     name: str
#     price: float
#     is_offer: Union[bool, None] = None

class A(BaseModel): # สร้าง BaseModel ของ YOLO
    task_id: str
    image_url: str

class B(BaseModel): # สร้าง BaseModel ของ Virtual Try
    task_id: str
    text: str
    
class response(BaseModel):
    message: str

    
async def yolo(a: A):
    await asyncio.sleep(5)
    return a.task_id, a.text

async def virtual_try(b: B):
    await asyncio.sleep(2)
    return b.task_id, b.text
    
async def task_worker():
    global results
    while True:
        task = await app.task_queue.get()
        try:
            print(f"Processing task...")
            task_id, result = await task()
            print(f"Task completed: {task_id}, result type: {type(result)}")
            results[task_id] = result
            print(f"Result stored in results dict with key: {task_id}")
        except Exception as e:
            print(f"Error processing task: {e}")
        finally:
            app.task_queue.task_done()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(task_worker())
    


# เขียน endpoint รับข้อมูลจาก client(รูป)
# เขียน BaseModel รับข้อมูลจาก client
@app.get("/yolo")
async def yolorequest(a: A):

    # ใส่ task ลงใน queue
    await app.task_queue.put(lambda: process_yolo(a.task_id, a.image_url, SERVER_URL))
    start = time.time()
    
    # เพิ่ม logging เพื่อดูการทำงาน
    print(f"Task {a.task_id} added to queue")
    
    while True:
        # เพิ่ม logging ทุก 5 วินาที
        if int(time.time() - start) % 5 == 0:
            print(f"Waiting for task {a.task_id}, elapsed time: {time.time() - start:.2f}s")
            print(f"Current results keys: {list(results.keys())}")
            
        if time.time() - start > 30:  # เพิ่ม timeout เป็น 30 วินาที
            return {"message": "timeout", "task_id": a.task_id}
            
        if a.task_id in results:
            result = results.pop(a.task_id)
            print(f"Task {a.task_id} completed with result: {result}")
            return {"message": "success", "detections": result}
            
        # เพิ่ม sleep เพื่อลดการใช้ CPU
        await asyncio.sleep(0.2)
        
@app.get("/virtual_try")
async def virtual_tryrequest(b: B):
    
        
        # ใส่ task ลงใน queue
        await app.task_queue.put(lambda: virtual_try(b))
        start = time.time()
        while True:
            # timeout when time over 20 seconds
            if time.time() - start > 20:
                return Response(content="timeout")
            if b.task_id in results:
                result = results.pop(b.task_id)
                print(result)
                return Response(content="success")

