##kentcamerav1.py
##Kent Heckel
##Started 4.13.22
##Recent 10.16.22
##QuadCamV9
import os
import time
import imageio
from PIL import Image
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
from time import sleep
from gpiozero import Button
from signal import pause
import PySimpleGUI as sg
from threading import Thread
from pathlib import Path
import shutil
import os
from pathlib import Path

##google drive needed these
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

##variable for deleting
done = 1

##setup led flash
GPIO.setup(17, GPIO.OUT)
GPIO.setwarnings(False)

##setup button
button = Button(27)

##intro flash - camera is ready
GPIO.output(17, True)
sleep(1)
GPIO.output(17, False)

##start window
layout = [  [sg.Text("QuadCam is on!")]]
                    
window = sg.Window('Quad Cam', layout)

##main where everything happens
def main(done):
    ##setup output folder
    t = time.localtime(time.time())
    currentTime = time.strftime("%m-%d-%Y-%H:%M:%S", t)
    folderPath = "/home/kentheckel/Desktop/Kentcamera/images/%s" % currentTime
    ##name the 2x2 photo
    photoName = "capture_Main"
    ##take the photo and flash the LED when done
    GPIO.output(17, True)
    capture(photoName, currentTime, folderPath)
    GPIO.output(17, False)
    ##crop the image
    crop(photoName, folderPath)
    ##copy files to upload folder and upload
    copyFiles(folderPath)
    upload(done)
    ##below is not used anymore
    #cropAdjust(folderPath)
    #makeGif(folderPath)

## where the photo is taken   
def capture(photoName, currentTime, folderPath):
    
    newpath = folderPath 
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    ##this is the actual cmd that take the photo. it runs a terminal cmd    
    cmd = "libcamera-jpeg -o %s/%s.jpg -n --autofocus -f --quality 100" % (folderPath, photoName)
    os.system(cmd)

##where the cop of the 2x2 happens
def crop(photoName, folderPath):
    originalImage = Image.open("%s/%s.jpg" % (folderPath, photoName))
    width, height = originalImage.size
   
   ##set width and height
    imageWidth = 2328
    imageHeight = 1748

    left = 0
    top = 0
    right = width / 2
    bottom = height / 2
    
    crop1 = originalImage.crop((left, top, right, bottom))
    #crop1Final = crop1.crop((0, 14, imageWidth - 315, imageHeight))
    crop1.save("%s/crop1.jpg" % folderPath)
    
    left = width / 2
    top = 0
    right = width
    bottom = height / 2
    
    crop2 = originalImage.crop((left, top, right, bottom))
    #crop2Final = crop2.crop((315, 0, imageWidth, imageHeight - 14))
    crop2.save("%s/crop2.jpg" % folderPath)
    
    left = 0
    top = height / 2
    right = width / 2
    bottom = height
    
    crop3 = originalImage.crop((left, top, right, bottom))
    #crop3Final = crop3.crop((adjustDistance * 2, 0, width / 2 - adjustDistance, height / 2))
    crop3.save("%s/crop3.jpg" % folderPath)
    
    left = width / 2
    top = height / 2
    right = width
    bottom = height
    
    crop4 = originalImage.crop((left, top, right, bottom))
    #crop4Final = crop4.crop((adjustDistance * 3, 0, width / 2, height / 2))
    crop4.save("%s/crop4.jpg" % folderPath)

##where I used to make the Gif - this is not a good method to making the gif, it must be done manually
# def makeGif(folderPath):
#     images = []
#     images.append(imageio.imread("%s/crop1.jpg" % folderPath))
#     images.append(imageio.imread("%s/crop2.jpg" % folderPath))
#     images.append(imageio.imread("%s/crop3.jpg" % folderPath))
#     images.append(imageio.imread("%s/crop4.jpg" % folderPath))
#     
#     imageio.mimsave("%s/final.gif" % folderPath, images, fps=4)

##what is called when the button is pushed
##say_hello is a thread that runs main() and blink() at the same time
def say_hello(done):
    if __name__ == '__main__':
        print("Running!")
        Thread(target = main, args=(done,)).start()
        Thread(target = blink).start()
    ##flash the led
    GPIO.output(17, True)
    sleep(1)
    GPIO.output(17, False)

##falsh the LED on a 3,2,1 countdown - this relies on timing, its not exaclty when the photo is taken but i tied my best
def blink():
    sleep(4)
    GPIO.output(17, True)
    sleep(0.5)
    GPIO.output(17, False)
    sleep(0.5)
    GPIO.output(17, True)
    sleep(0.5)
    GPIO.output(17, False)
    sleep(0.5)
    GPIO.output(17, True)
    sleep(0.5)
    GPIO.output(17, False)

##copy the files from the "images" folder to the temporary "upload" folder
def copyFiles(folderPath):
    # defining source and destination
    # paths
    src = folderPath
    trg = '/home/kentheckel/Desktop/Kentcamera/upload'
     
    files=os.listdir(src)

    # iterating over all the files in
    # the source directory
    for fname in files:
         
        # copying the files to the
        # destination directory
        shutil.copy2(os.path.join(src,fname), trg)
        print("copied files")

##upload to google drive using google api, dont ask me how this works
def upload(done):
    ## begin google drive uplaod
    SCOPES = ["https://www.googleapis.com/auth/drive"]

    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    try:
        service = build("drive", "v3", credentials=creds)
        
        response = service.files().list(
            q="name='quadcam' and mimeType='application/vnd.google-apps.folder'",
            spaces='drive'
            ).execute()
        
        if not response['files']:
            file_metadata = {
                "name": "quadcam",
                "mimeType": "application/vnd.google-apps.folder"
                }
            
            file = service.files().create(body=file_metadata, fields="id").execute()
            
            folder_id = file.get('id')
        else:
            folder_id = response['files'][0]['id']
            
        for file in os.listdir('upload'):
            file_metadata = {
                "name": file,
                "parents": [folder_id]
                
                }
            
            media = MediaFileUpload(f"upload/{file}")
            upload_file = service.files().create(body=file_metadata,
                                                 media_body=media,
                                                 fields='id').execute()
            print("Backed up File: " + file)
            
            ##this is to indicate if all the files have been uplaoded
            done = 0
            
            
    except HttpError as e:
        print("Error: " + str(e))
        
    ##delete folder then flash LED to indicate the camera is good to go   
    if done == 0:
        [f.unlink() for f in Path("/home/kentheckel/Desktop/Kentcamera/upload").glob("*") if f.is_file()]
        print("deleted all")
        GPIO.output(17, True)
        sleep(0.5)
        GPIO.output(17, False)
        sleep(0.5)
        GPIO.output(17, True)
        sleep(0.5)
        GPIO.output(17, False)
        
##where the magic happens, if button is pushed run the thread
button.when_pressed = say_hello

##this is for the GUI that opens when the app starts
event, values = window.read()

##old ideas on how to take the photo
# def mouseClick(x, y, button, pressed):
#     print(x,y)
#     mouseListener.stop()
# 
# mouseListener = mouse.Listener(on_click=mouseClick)
# 
# def cropAdjust(folderPath):
#     mouseListener.start()
#     image1 = Image.open("%s/crop1.jpg" % folderPath)
#     image1.show()

##below here is all the functions of libcamera so i dont have to google it everytime

#  -h [ --help ] [=arg(=1)] (=0)         Print this help message
#   --version [=arg(=1)] (=0)             Displays the build version number
#   --list-cameras [=arg(=1)] (=0)        Lists the available cameras attached to the system.
#   --camera arg (=0)                     Chooses the camera to use. To list the available indexes, use the 
#                                         --list-cameras option.
#   -v [ --verbose ] [=arg(=1)] (=0)      Output extra debug and diagnostics
#   -c [ --config ] [=arg(=config.txt)]   Read the options from a file. If no filename is specified, default to 
#                                         config.txt. In case of duplicate options, the ones provided on the command line
#                                         will be used. Note that the config file must only contain the long form 
#                                         options.
#   --info-text arg (=#%frame (%fps fps) exp %exp ag %ag dg %dg)
#                                         Sets the information string on the titlebar. Available values:
#                                         %frame (frame number)
#                                         %fps (framerate)
#                                         %exp (shutter speed)
#                                         %ag (analogue gain)
#                                         %dg (digital gain)
#                                         %rg (red colour gain)
#                                         %bg (blue colour gain)
#                                         %focus (focus FoM value)
#                                         %aelock (AE locked status)
#   --width arg (=0)                      Set the output image width (0 = use default value)
#   --height arg (=0)                     Set the output image height (0 = use default value)
#   -t [ --timeout ] arg (=5000)          Time (in ms) for which program runs
#   -o [ --output ] arg                   Set the output file name
#   --post-process-file arg               Set the file name for configuring the post-processing
#   --rawfull [=arg(=1)] (=0)             Force use of full resolution raw frames
#   -n [ --nopreview ] [=arg(=1)] (=0)    Do not show a preview window
#   -p [ --preview ] arg (=0,0,0,0)       Set the preview window dimensions, given as x,y,width,height e.g. 0,0,640,480
#   -f [ --fullscreen ] [=arg(=1)] (=0)   Use a fullscreen preview window
#   --qt-preview [=arg(=1)] (=0)          Use Qt-based preview window (WARNING: causes heavy CPU load, fullscreen not 
#                                         supported)
#   --hflip [=arg(=1)] (=0)               Request a horizontal flip transform
#   --vflip [=arg(=1)] (=0)               Request a vertical flip transform
#   --rotation arg (=0)                   Request an image rotation, 0 or 180
#   --roi arg (=0,0,0,0)                  Set region of interest (digital zoom) e.g. 0.25,0.25,0.5,0.5
#   --shutter arg (=0)                    Set a fixed shutter speed
#   --analoggain arg (=0)                 Set a fixed gain value (synonym for 'gain' option)
#   --gain arg                            Set a fixed gain value
#   --metering arg (=centre)              Set the metering mode (centre, spot, average, custom)
#   --exposure arg (=normal)              Set the exposure mode (normal, sport)
#   --ev arg (=0)                         Set the EV exposure compensation, where 0 = no change
#   --awb arg (=auto)                     Set the AWB mode (auto, incandescent, tungsten, fluorescent, indoor, daylight, 
#                                         cloudy, custom)
#   --awbgains arg (=0,0)                 Set explict red and blue gains (disable the automatic AWB algorithm)
#   --flush [=arg(=1)] (=0)               Flush output data as soon as possible
#   --wrap arg (=0)                       When writing multiple output files, reset the counter when it reaches this 
#                                         number
#   --brightness arg (=0)                 Adjust the brightness of the output images, in the range -1.0 to 1.0
#   --contrast arg (=1)                   Adjust the contrast of the output image, where 1.0 = normal contrast
#   --saturation arg (=1)                 Adjust the colour saturation of the output, where 1.0 = normal and 0.0 = 
#                                         greyscale
#   --sharpness arg (=1)                  Adjust the sharpness of the output image, where 1.0 = normal sharpening
#   --framerate arg (=30)                 Set the fixed framerate for preview and video modes
#   --denoise arg (=auto)                 Sets the Denoise operating mode: auto, off, cdn_off, cdn_fast, cdn_hq
#   --viewfinder-width arg (=0)           Width of viewfinder frames from the camera (distinct from the preview window 
#                                         size
#   --viewfinder-height arg (=0)          Height of viewfinder frames from the camera (distinct from the preview window 
#                                         size)
#   --tuning-file arg (=-)                Name of camera tuning file to use, omit this option for libcamera default 
#                                         behaviour
#   --lores-width arg (=0)                Width of low resolution frames (use 0 to omit low resolution stream
#   --lores-height arg (=0)               Height of low resolution frames (use 0 to omit low resolution stream
#   --mode arg                            Camera mode as W:H:bit-depth:packing, where packing is P (packed) or U 
#                                         (unpacked)
#   --viewfinder-mode arg                 Camera mode for preview as W:H:bit-depth:packing, where packing is P (packed) 
#                                         or U (unpacked)
#   --autofocus [=arg(=1)] (=0)           Flush output data as soon as possible
#   -q [ --quality ] arg (=93)            Set the JPEG quality parameter
#   -x [ --exif ] arg                     Add these extra EXIF tags to the output file
#   --timelapse arg (=0)                  Time interval (in ms) between timelapse captures
#   --framestart arg (=0)                 Initial frame counter value for timelapse captures
#   --datetime [=arg(=1)] (=0)            Use date format for output file names
#   --timestamp [=arg(=1)] (=0)           Use system timestamps for output file names
#   --restart arg (=0)                    Set JPEG restart interval
#   -k [ --keypress ] [=arg(=1)] (=0)     Perform capture when ENTER pressed
#   -s [ --signal ] [=arg(=1)] (=0)       Perform capture when signal received
#   --thumb arg (=320:240:70)             Set thumbnail parameters as width:height:quality, or none
#   -e [ --encoding ] arg (=jpg)          Set the desired output encoding, either jpg, png, rgb, bmp or yuv420
#   -r [ --raw ] [=arg(=1)] (=0)          Also save raw file in DNG format
#   --latest arg                          Create a symbolic link with this name to most recent saved file
#   --immediate [=arg(=1)] (=0)           Perform first capture immediately, with no preview phase
# 
# 
