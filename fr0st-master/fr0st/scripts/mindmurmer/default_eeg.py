import logging
import time
import numpy
import wx

from fr0stlib import Flame
from fr0stlib.render import save_image
from fr0stlib.pyflam3 import Genome, byref, flam3_interpolate

from utils import get_scriptpath, easing_cubic, easing_sine
from eegsources import *
from rabbit_controller import RabbitController
from sound_controller import MindMurmurSoundScapeController
from input_controller import InputController


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
    def __init__(self, eeg_source, gui, audio_folder):
        print("[>] _INIT")
        self.eeg_source = eeg_source
        self.frame_index = 0
        self.speed = 0.1
        self.channels = 24
        self.sinelength = 300 # frames
        self.gui = gui
        self.maxfps = 20 # target frames per second
        self.states_flames = [ ]
        self.meditation_state = 1

        # init rabbitMQ connection
        self.rabbit = RabbitController('localhost', 5672, 'guest', 'guest', '/')

        # self.audio_controller = MindMurmurSoundScapeController(audio_folder)
        self.input_controller = InputController(self)

        # attach keyboard events.
        self.input_controller.bind_keyboardevents(self.gui.previewframe)
        
        # reference to global or defined herebefore
        self.flame = flame
        # set these 3 to start fractal interpolation
        self.transition_pct = None
        self.transition_from = None
        self.transition_to = None
        # sets the frame at which the user disconnected
        self.disconnected_at = None

    def gui_start(self):
        print("[>] GUI START")
        # ask for input
        self.retreive_params()
        # hide UI
        # self.gui.Hide()
        # show GUI preview Window
        self.gui.previewframe.Show()
        self.gui.previewframe.ShowFullScreen(True)
        self.gui.previewframe.SetWindowStyle(self.gui.previewframe.GetWindowStyle() | wx.BORDER_NONE | wx.CLIP_CHILDREN)
        self.gui.previewframe.SetFocus()
        time.sleep(0.040)
        # fullscreen
        # self.gui.previewframe.ShowFullScreen(True)

        # time.sleep(0.400)
        self.set_state(1, False)
        # start loop

    def idle(self):
        print("[>] IDLE")
        self.frame_index = 0
        self.frame_index_sincestate = 0
        self.keeprendering = True

        while self.keeprendering:
            # fps timer
            t0 = time.clock()
            try:

                # read data
                eegdata = self.eeg_source.read_data()

                # apply transition
                self.apply_transition(duration_sec = 30)

                # no data
                if(eegdata is None or eegdata.is_empty() == True):

                    # do nothing during 5 minutes.
                    if(self.frame_index_sincestate > self.maxfps * 30):
                    # or transition to next state:
                        self.set_state(set_next=True)

                # data recived
                else:
                    print("[ ] USER CONNECTED")
                    # if inactive for more than 30 seconds
                    if(self.frame_index > self.maxfps * 30):
                        # back to state 1
                        self.set_state(1)
                    # stop idling
                    self.keeprendering = False

                # update status bar
                show_status("Frame: %s/%s | IDLING" 
                            %(self.frame_index,
                            self.frame_index_sincestate))

                # render with new values
                self.render()

                # count frame number
                self.frame_index += 1
                self.frame_index_sincestate += 1

                
            except Exception as ex:
                import traceback
                print('[!] error during MMEngine idle loop: ' + str(ex))
                traceback.print_exc()
                self.keeprendering = False
            finally:
                # sleep to keep a decent fps
                delay = t0 + 1./self.maxfps - time.clock()
                if delay > 0. : time.sleep(delay)
                else :  time.sleep(0.01)

        # -- END of loop
        self.start()


    def start(self):

        print("[>] START")
        
        self.frame_index = 0
        self.frame_index_sincestate = 0
        self.keeprendering = True

        while self.keeprendering:
            # fps timer
            t0 = time.clock()
            try:

                # if no flames were designed for transition, 
                if(self.apply_transition() == False):
                
                    # read data
                    eegdata = self.eeg_source.read_data()

                    # data found                
                    if(eegdata is not None and eegdata.is_empty() == False):

                        # [!] new meditation state reached
                        if(self.meditation_state != eegdata.meditation_state \
                            # and if transitionned less than a minute ago
                            and self.frame_index_sincestate > self.maxfps * 30):
                            # [>] set new state
                            self.set_state(eegdata.meditation_state)

                        #TODO get heartbeat
                        heartbeat = 60
                        # send data to RabbitMQ bus
                        self.rabbit.publish_heart(heartbeat)

                        # transform fractal with new values from data
                        self.animate(eegdata)

                        # update status bar
                        show_status("Frame: %s/%s | EEG: %s | MEDITATION STATE: %s" 
                                    %(self.frame_index,
                                    self.frame_index_sincestate, 
                                    eegdata.console_string() if eegdata is not None else "no data",
                                    self.meditation_state ))

                    # no data is found
                    else:
                        # go to idling.
                        self.keeprendering = False
            
                # render with new values
                self.render()

                # count frame number
                self.frame_index += 1
                self.frame_index_sincestate += 1

                
            except Exception as ex:
                import traceback
                print('error during MMEngine loop: ' + str(ex))
                traceback.print_exc()
                self.keeprendering = False
            finally:
                # sleep to keep a decent fps
                delay = t0 + 1./self.maxfps - time.clock()
                if delay > 0. : time.sleep(delay)
                else :  time.sleep(0.01)

        # -- END of loop
        self.idle()
            
    def stop(self):
        print("[>] STOP")
        self.keeprendering = False
           
        # hide GUI preview Window
        self.gui.Show()
        self.gui.previewframe.Hide()
        self.gui.previewframe.ShowFullScreen(False)
        self.gui.previewframe.SetWindowStyle(self.gui.previewframe.GetWindowStyle() & ~wx.STAY_ON_TOP)
        # set gobal variable to visualize final falame
        self.gui.flame = self.flame

    def zoom(self, zoomamount = 1):
        self.flame.scale *= zoomamount

    def set_state(self, newstate = 0, transtition = True, set_prev = False, set_next = False):
        if(set_prev):
            newstate = self.meditation_state - 1 if self.meditation_state > 1 else 5
        elif(set_next):
            newstate = self.meditation_state + 1 if self.meditation_state < 5 else 1
        # else it's a number
        print("[ ] TRANSITION TO STATE %s" %(newstate))

        # save state
        self.meditation_state = newstate
        self.frame_index_sincestate = 0

        # find appropriate flame
        flame_per_state = int(len(self.states_flames) / 5)
        flame_index = (newstate - 1) * flame_per_state \
                    + numpy.random.randint(0, flame_per_state)

        print("[ ] ENTERING STATE %s" %(newstate))
        if(transtition):
            print("[ ] TRANSITION TO FLAME %s" %(self.states_flames[flame_index].name))
            # start transition
            self.transition_pct = 0.0
            self.transition_from = self.flame
            self.transition_to = self.states_flames[flame_index]
        else:
            print("[ ] LOADING FLAME %s" %(self.states_flames[flame_index].name))
            self.flame = self.load_flame(self.states_flames[flame_index])



    def move(self, x = 0, y = 0):
        try:
            move_x =  y * np.sin(self.flame.rotate * np.pi / 180.) \
                    + x * np.cos(self.flame.rotate * np.pi / 180.)
            move_y =  y * np.cos(self.flame.rotate * np.pi / 180.) \
                    + x * np.sin(self.flame.rotate * np.pi / 180.)
            move_x /= self.flame.scale
            move_y /= self.flame.scale
            

            self.flame.center[0] += move_x
            self.flame.center[1] += move_y
        except:
            print("[!] error during flame move")

    def rotate(self, deg_angle = 0):
        try:
            self.flame.rotate += deg_angle
        except:
            print("[!] error during flame rotate")

    def recenter(self):
        self.flame.center = 0, 0
        self.flame.rotate = 0

    # retreive the global fractal color from the current flame's xforms
    def get_flamecolor_rgb(self):
        r,g,b, = 0,0,0
        weight = 0
        # read colors for each xform
        for xf in flame.xform:
            if(xf.weight > 0):
                gradientlocation = int(xf.color * (len(flame.gradient) - 1))
                xcolors = flame.gradient[gradientlocation]
                r = r + xcolors[0] * xf.weight
                g = g + xcolors[1] * xf.weight
                b = b + xcolors[2] * xf.weight
                weight = weight + xf.weight
        if weight == 0:
            return [0,0,0]
        return [int(r / weight), int(g / weight), int(b / weight)]
    
    def retreive_params(self, show_dialog = False):
        flames = get_flames()
        if(show_dialog):
        
            res = dialog("Choose settings.\n\n(Keyframe interval = 0 "
                 "uses the time attribute of each flame instead "
                 "of a fixed interval)",
                 ("MEDITATION STATE 1", flames, 1),
                 ("MEDITATION STATE 2", flames, 2),
                 ("MEDITATION STATE 3", flames, 3),
                 ("MEDITATION STATE 4", flames, 4),
                 ("MEDITATION STATE 5", flames, 5))
            self.states_flames = res
        else:
            # the 1st frame is used to be worked on. not a state
            self.states_flames = flames[1:]

        if len(self.states_flames) < 2:
            raise ValueError("Need to select at least 2 flames")

        for flame in self.states_flames:
            flame.size = 960, 540 
        return

    def apply_transition(self, duration_sec = 10):
        if(self.transition_pct is not None and self.transition_from is not None and self.transition_to is not None):
            # do the transition
                    # apply interpolation transition
            lerp_pct = easing_cubic(self.transition_pct)
            newflame = self.load_flame(self.transition_from, self.transition_to, lerp_pct)
            if(newflame is not None):
                self.flame = newflame

            if(self.transition_pct >= 1):
                # end of transition
                self.transition_pct = None
            else:
                # add 1 / nth to the transition
                self.transition_pct += 1 / float(duration_sec * self.maxfps)
            return True
        else:
            return False


    # lerp is interpolation percentage [0 - 1] between origin and target
    def load_flame(self, flame_origin, flame_target = None, lerp = 0.0):
        loaded_flame = self.flame
        try:
            if(lerp == 0.0 or flame_target is None):
                loaded_flame = flame_origin
            elif(lerp >= 1.0 or flame_origin is None):
                loaded_flame = flame_target
            else:        
                # interpolation:
                from fr0stlib.render import to_string as flame_to_string
                flame_origin.time = 0
                flame_target.time = 1
                flames_lerp = [flame_origin, flame_target]
                flames_str = "<flames>%s</flames>" % "".join(map(flame_to_string, flames_lerp))
                genomes, ngenomes = Genome.from_string(flames_str)           
                targetflame = Genome()
                flam3_interpolate(genomes, ngenomes, lerp, 0, byref(targetflame))
                loaded_flame = Flame(targetflame.to_string())
            
        except Exception as ex:
            import traceback
            print('[!] error during interpolation at %s: %s' %(lerp, str(ex)))
            traceback.print_exc()
            return None

        return loaded_flame
        
    # process new EEGData and animate flame
    def animate(self, eegdata):
        docontinue = True
        if (self.flame.xform is None or len(self.flame.xform) == 0):
            return False
        try:
            #if(self.frame_index % 10 == 2) : print(str(eegdata.waves))
            # FLAME UPDATE (at least 125 frames apart)
            # if(eegdata.blink == 1 and self.frame_index > 125):
                # adjust form weights (from utils)
                #normalize_weights(self.flame)
                
                # move window
                #self.flame.reframe()

                # update colors
                #calculate_colors(self.flame.xform)

            dataindex = 5
            for x in self.flame.xform:
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
                    mov_delta = data * 0.01 * self.speed
                    x.move(mov_delta)

                    # # ZOOM
                    # # calculate zoom amount from data elements
                    # data = eegdata.waves[dataindex % len(eegdata.waves)]
                    # dataindex += 1 # next data from audiodata
                    # # every n frames is a cycle of X back and forth.
                    # data *= np.cos(self.frame_index * (np.pi * 2) / self.sinelength)
                    # zoom_delta = data * 0.01 * self.speed
                    # x.zoom(1 + zoom_delta)

            return True
        except Exception as ex:
            logging.exception(ex)
            print('[!] error during rendering: ' + str(ex))

            # SHOW preview on Fr0st
            return False

    def render(self):
        # animate preview window if renderer is ok and Idling
        if(self.gui.previewframe.rendering == False):
            # run pyflam4 rendering
            self.gui.previewframe.RenderPreview(self.flame)

    

# RUN
print('[$] - BEGIN SCRIPT -')
audio_folder = get_scriptpath() + "/mindmurmer/sounds_controllers/sound_controller_demo_files/soundscape_controller_demo_files"
# 1 - Dummy DATA
# eeg = EEGDummy()
eeg = EEGFromRabbitMQ('localhost', 5672, 'guest', 'guest', '/')
# audio = get_audio_source(get_scriptpath() + '/mindmurmur/audio/midnightstar_crop.wav')
# eeg = EEGFromAudio(audio)
# 2 - DATA from json file
# eeg = EEGFromJSONFile(get_scriptpath() + '/mindmurmur/data/Muse-B1C1_2018-06-11--07-48-41_1528717729867.json') # extra small
# eeg = EEGFromJSONFile(get_scriptpath() + '/mindmurmer/data/Muse-B1C1_2018-06-10--18-35-09_1528670624296.json') # medium
# eeg = EEGFromJSONFile(get_scriptpath() + '/mindmurmer/data/Muse-B1C1_2018-07-16--07-24-35_1531745297756.json') # large (16 july)
#eeg = EEGFromJSONFile(get_scriptpath() + '/mindmurmer/data/Muse-B1C1_2018-07-17--07-00-11_1531868655676.json') # large (17 july)

#_self is some hidden hack from fr0st that refers to the gui MainWindow
engine = MMEngine(eeg, _self, audio_folder)

engine.gui_start()
engine.idle()
print('[x] - END SCRIPT -')
