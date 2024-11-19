import os
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import numpy as np
import cv2
from picamera2 import Picamera2, Preview
import time
from skimage import morphology
from libcamera import controls
import tkinter as tk
from tkinter import Label, Button
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
#valores estaticos
threshold=128  #50
light_color="#E1DEE3"
def rooteador(frame):
    # toma de fotografia y binarizado
    img=Image.fromarray(frame)
    img=img.convert('L')
    width,height=img.size
    print(f"width:{width}, height:{height}")
    binarized=np.array(img.point(lambda p: 1 if p > threshold else 0, mode ='1')).astype(np.uint8)
    smoothed = cv2.GaussianBlur(binarized,(5,5),0)
    #se hace el calculo de la sumatoria
    row_sums = np.sum(smoothed,axis=1)
    window_size=5
    row_sums = np.convolve(row_sums, np.ones(window_size)/window_size,mode='same')
    max_img=np.argmax(row_sums)
    print(max_img)
    row_sums=row_sums[(max_img+300):]
    smoothed=smoothed[(max_img+300):,:]
    img=img.crop((0,max_img+300,width,height))
    # calculo de la derivada
    row_sums_derivative = np.abs(np.diff(row_sums)[2:])
    window_size=10
    row_sums_derivative=np.convolve(row_sums_derivative, np.ones(window_size)/window_size,mode='same')
    min_val=np.min(row_sums_derivative)
    max_val=np.max(row_sums_derivative)
    row_sums_derivative=(row_sums_derivative-min_val)/(max_val-min_val)
 
    # se cuentan los cambios de color
    color_changes=np.sum(np.diff(smoothed,axis=1) !=0,axis=1)
 
    # corte de la imagen
    MaxICC=np.argmax(color_changes)
    AboveI=np.where(row_sums_derivative>0.5)[0]
    if len(AboveI)>0:
        CI=AboveI[np.argmin(np.abs(AboveI-MaxICC))]
        print(f"indice mas cercano: {CI}")
    else:
        print("no hay, no ecsiste")
 
    if CI is not None:
        Fimg=smoothed[CI:,:]
        skeleton=morphology.skeletonize(Fimg)
        LH=img.crop((0,CI,width,height))
        return np.array(LH)
        fig,ax=plt.subplots(figsize=(width/500,(height-CI)/500),dpi=100)
        ax.imshow(np.array(LH))
        ax.imshow(skeleton,cmap='Reds',alpha=0.6)
        ax.axis('off')
        fig.canvas.draw()
        rooted=np.frombuffer(fig.canvas.tostring_rgb(),dtype=np.uint8)
    else:
        print("N0")
        rooted = None
 
    return rooted
 
 
 
 
 
 
 
root=tk.Tk()
root.title("interfaz epika")
root.attributes('-fullscreen',True)
root.geometry("1024x600")
root.bind("<Escape>",lambda e: root.attributes("-fullscreen",False))
root.grid_columnconfigure(0,weight=1)
root.grid_columnconfigure(1,weight=1)
 
picam=Picamera2()
picam.configure(picam.create_preview_configuration())
picam.start()
picam.set_controls({"AfMode":controls.AfModeEnum.Continuous})
time.sleep(1.5)
 
video_label=Label(root)
video_label.grid(row=0,column=0,padx=10,pady=10, sticky="nsew")
gray_label=Label(root)
gray_label.grid(row=0,column=1,padx=10,pady=10, sticky="nsew")
 
def update_frame():
    if root.winfo_width()>10:
        frame=picam.capture_array()
        if frame is not None:
            img=Image.fromarray(frame)
            new_width=root.winfo_width()//2-20
            img.thumbnail((new_width,new_width*img.height//img.width),Image.LANCZOS)
 
            imgtk=ImageTk.PhotoImage(image=img)
            video_label.imgtk=imgtk
            video_label.configure(image=imgtk)
    root.after(20,update_frame)
 
def take_photo():
    picam.stop()
    picam.configure(picam.create_still_configuration())
    picam.start()
    frame = picam.capture_array()
    picam.stop()
    picam.configure(picam.create_preview_configuration())
    picam.start()
    if frame is not None:
        raices=rooteador(frame)
        img=Image.fromarray(raices)
        gray_width=root.winfo_width()//2-20
        img.thumbnail((gray_width, gray_width * img.height//img.width),Image.LANCZOS)
 
        imgtk_gray=ImageTk.PhotoImage(image=img)
        gray_label.imgtk=imgtk_gray
        gray_label.configure(image=imgtk_gray)
 
capture_button= Button(root,text="puchale",command=take_photo)
capture_button.grid(row=1,column=0,columnspan=2,pady=20)
 
update_frame()
root.mainloop()
 
picam.stop()
