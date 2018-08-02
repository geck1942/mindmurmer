
import wx
from fr0stlib.decorators import *

class InputController(object):
    def __init__(self,engine):
        # main script MMEngine reference.
        self.engine = engine

    def bind_keyboardevents(self, guiframe):
        self.guiframe = guiframe
        self.guiframe.Bind(wx.EVT_KEY_DOWN, self.OnKey)

    def unbind_keyboardevents(self):
        self.guiframe.UnBind(wx.EVT_KEY_DOWN)
        self.guiframe = None

    def OnKey(self, event):
        if self.guiframe is None:
            return 

        key_code = event.GetKeyCode()
        print('WXK keycode: %s' %(key_code))
        # [F8] - START
        if key_code == 347:
            self.engine.start()
            event.Skip()            
        # [F9] OR [F10] - STOP
        elif key_code == 348 or key_code == 349:
            self.engine.stop()
            event.Skip()            
        # [F11] - FORWARD
        elif key_code == 350:
            self.engine.zoom(1.1)
        # [F12] - BACKWARD
        elif key_code == 351:
            self.engine.zoom(0.9)
        # [W] OR [UP_ARROW] - MOVE
        elif key_code == 87 or key_code == 315:
            self.engine.move(0, -1)
        # [A] OR [LEFT_ARROW] - MOVE
        elif key_code == 65 or key_code == 314:
            self.engine.move(-1, 0)
        # [S] OR [DOWN_ARROW] - MOVE
        elif key_code == 83 or key_code == 317:
            self.engine.move(0, +1)
        # [D] OR [RIGHT_ARROW] - MOVE
        elif key_code == 68 or key_code == 316:
            self.engine.move(+1, 0)
        # [Q] - ROTATE LEFT
        elif key_code == 81:
            self.engine.rotate(-15)
        # [E] - ROTATE RIGHT
        elif key_code == 69:
            self.engine.rotate(+15)
        # [Z] - RECENTER
        elif key_code == 100:
            self.engine.recenter()

    @Bind(wx.EVT_MOUSEWHEEL)
    def OnWheel(self, e):
        if e.ControlDown():
            if e.AltDown():
                diff = 1.01
            else:
                diff = 1.1
        elif e.AltDown():
            diff = 1.001
        else:
            diff = 1.1
        # self.engine.flame.scale /= 1.1
        self.engine.flame.scale*= diff**((e.GetWheelRotation() > 0)*2 -1)