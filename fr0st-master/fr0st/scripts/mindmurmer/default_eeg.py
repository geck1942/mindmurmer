import logging
import time

from fr0stlib import Flame
from fr0stlib.render import save_image
from fr0st.scripts.mindmurmer.sound_controller import MindMurmurAudioController

from utils import get_scriptpath
from eegsources import *

# For running the script as stand alone and not through the fractal app
if 'flame' not in locals() and 'flame' not in globals():
	print "generating random flame"
	flame = Flame()
	flame.add_xform()


if 'large_preview' not in locals() and 'preview' not in globals():
	def DoNothing():
		pass

	large_preview = DoNothing
	preview = DoNothing


class MMEngine:
    def __init__(self, eeg_source, gui, audio_folder, heartbeat_folder):
        self.eeg_source = eeg_source
        self.audio_controller = MindMurmurAudioController(audio_folder, heartbeat_folder)
        self.frame_index = 0
        self.speed = 1
        self.channels = 24
        self.sinelength = 300 # frames
        self.gui = gui
        self.fps = 25 # target frames per second

    def start(self):
        play = True
        while play:
            t0 = time.clock()
            play = self.render()
            # animate wireframe window
            #preview()
            #self.gui.image.RenderPreview()

            # animate preview window
            self.gui.previewframe.RenderPreview()

            # count frame number
            show_status("render frame: %s" %(self.frame_index))
            self.frame_index += 1
            
            # sleep to keep a decent fps
            delay = t0 + 1./self.fps - time.clock()
            if delay > 0 : time.sleep(delay)

    def render(self):
        docontinue = True
        if (flame.xform is None or len(flame.xform) == 0):
            return False
        try:
            # get eeg data as [] from ext. source
            eegdata = self.eeg_source.read_data()
            #if(self.frame_index % 10 == 2) : print(str(eegdata.waves))
            # FLAME UPDATE (at least 125 frames apart)
            if(eegdata.blink == 1 and self.frame_index > 125):
                self.NewFlame()
                self.frame_index = 0
                print("BLINK: new flames generated")
                # adjust form weights (from utils)
                #normalize_weights(flame)
                
                # move window
                #flame.reframe()

                # update colors
                #calculate_colors(flame.xform)
                print("BLINK: mix track")
                self.audio_controller.mix_track(0)

            dataindex = 0
            for x in flame.xform:
                if(x.animate and eegdata is not None):
                    # ROTATION
                    # calculate rotation amount from data elements
                    data = eegdata.waves[dataindex % len(eegdata.waves)]
                    dataindex += 1 # next data from audiodata
                    x.rotate(data * 1.5 * self.speed)

                    # MOVEMENT
                    # calculate move amount from data elements
                    data = eegdata.waves[dataindex % len(eegdata.waves)]
                    dataindex += 1 # next data from audiodata
                    # every n frames is a cycle of X back and forth.
                    data *= np.sin(self.frame_index * (np.pi * 2) / self.sinelength)
                    mov_delta = data * 0.02 * self.speed

            return True
        except Exception as ex:
            logging.exception(ex)
            print('error during rendering: ' + str(ex))

            # SHOW preview on Fr0st
            return False

    # Generate a whole new Flame
    def NewFlame(self):
        # if(not flame.final is None):
        #     flame.final.delete()
        # l = len(flame.xform)
        # # cannot remove form #0
        # for i in range(l-1):
        #     flame.xform[-1].delete()
        
        # flame.xform[-1].delete()
        #flame.xform =[]
        
        # based on julia lines:
        # Form 1: BASE
        if(len(flame.xform) == 0):
            x1 = flame.add_xform()
        else:
            x1 = flame.xform[0]
        # x1.coefs = [1, 0,    # x
        #             0, 1,    # y
        #             ran(-0.2, 0.2), ran(-0.2, 0.2) ]    # o around 0
        x1.weight = 0.25
        x1.color = random.random() # [0 : 1]
        x1.color_speed = 0.9
        x1.noise = 0.0 + random.random() * 0.4 # [0.0 : 0.4]
        x1.blur = 0.0 + random.random() * 0.1 # [0.0 : 0.1]
        x1.animate = 1
        x1.rotate(random.random() * 360)

        # Form 2: JULIA TRANSFORM
        if(len(flame.xform) <= 1):
            x2 = flame.add_xform()
        else:
            x2 = flame.xform[1]
        # x2.coefs = [0.5, 0,    # x
        #             0, 0.5,    # y
        #             ran(-0.5, 0.5), ran(-0.5, 0.5) ]    # o
        x2.weight = 0.5
        # x2.color = random.random() # [0 : 1]
        x2.color_speed = 0.5
        x2.julian = 0.7 + random.random() * 0.3 # [0.7 : 1]
        x2.animate = 1
        x2.rotate(random.random() * 360)

        # Form 3: LINE
        if(len(flame.xform) <= 2):
            x3 = flame.add_xform()
        else:
            x3 = flame.xform[2]
        # x3.coefs = [ran(1, 3), 0,    # x
        #             0, 0,    # y
        #             ran(-1.0, 1.0), ran(-1.0, 1.0) ]    # o
        x3.weight = 0.25
        # x3.color = random.random() # [0 : 1]
        x3.color_speed = 0.5
        x3.cross = 0.5 + random.random() * 1.5 # [0.5 : 2]
        x3.julian = 0.2 + random.random() * 0.8 # [0.2 : 1]
        x3.animate = 1
        x3.rotate(random.random() * 360)

        # Form 4: FLOWERS
        if(len(flame.xform) > 3):
            x4 = flame.xform[3]
            # x4.coefs = [0.5, 0,    # x
            #             0, 0.5,    # y
            #             ran(-0.5, 0.5), ran(-0.5, 0.5) ]    # o                    
            x4.weight = 0.25
            # x4.color = random.random() # [0 : 1]
            x4.color_speed = 0.9
            x4.julian = 0.9 + random.random() * 0.1 # [0.9 : 1]
            x4.animate = 1
            x4.rotate(random.random() * 360)

        # Form 5: FINAL
        if(not flame.final is None):
            x5 = flame.final
            # x5.coefs = [1, 0,    # x
            #             0, 1,    # y
            #             ran(-0.5, 0.5), ran(-0.5, 0.5) ]    # o around 0
            # x5.color = 0.0
            x5.color_speed = 0.0
            x5.spherical = 0.1 + random.random() * 0.9 # [0.1 : 1]
            x5.julia = 0.1 + random.random() * 0.4 # [0.1 : 0.5]
            x5.linear = 0.0
            x5.rotate(random.random() * 360)

# RUN
audio_folder = get_scriptpath() + "/mindmurmer/sound_controller_demo_tracks"
heartbeat_folder = get_scriptpath() + "/mindmurmer/sound_controller_heartbeats"
# 1 - Dummy DATA
#eeg = EEGDummy()
# audio = get_audio_source(get_scriptpath() + '/mindmurmur/audio/midnightstar_crop.wav')
# eeg = EEGFromAudio(audio)
# 2 - DATA from json file
#eeg = EEGFromJSONFile(get_scriptpath() + '/mindmurmur/data/Muse-B1C1_2018-06-11--07-48-41_1528717729867.json') # extra small
eeg = EEGFromJSONFile(get_scriptpath() + '/mindmurmer/data/Muse-B1C1_2018-06-10--18-35-09_1528670624296.json') # medium

#_self is some hidden hack from fr0st that refers to the gui MainWindow
engine = MMEngine(eeg, _self, audio_folder, heartbeat_folder)

engine.start()