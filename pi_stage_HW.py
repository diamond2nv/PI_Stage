from ScopeFoundry import HardwareComponent
from collections import OrderedDict
from ScopeFoundry.helper_funcs import sibling_path
import time
from pipython import GCSDevice, pitools, GCSError, gcserror

from qtpy import QtCore
import threading
from _tracemalloc import stop

default_axes = OrderedDict(
    [(1,'x')])

class PIStage(HardwareComponent):
    
    name = 'pi_stage'
    
    
    def __init__(self, app, debug=False, name=None , axes =default_axes):
        
        self.axes = axes
        
        HardwareComponent.__init__(self, app, debug=debug, name=name)
    
    def setup(self):
        
        #self.settings.New('port', dtype=str, initial='')
        
        
        for ax_num, ax_name in self.axes.items():
            
            self.settings.New("controller", dtype=str, initial="C-863.11", ro=True)
            self.settings.New("stage", dtype=str, initial="M-405.CG", ro=True)
            self.settings.New("initial_ref_mode", dtype=str, choices=[ "None", "FNL", "FPL", "FRF"], initial="None", ro=False)# reference the connected stages
            
            self.settings.New(ax_name + "_position", dtype=float, 
                              unit='mm', si=False, spinbox_decimals=4,
                              ro=True)

            self.settings.New(ax_name + "_target", dtype=float, 
                              unit='mm', si=False, spinbox_decimals=4,
                              ro=False)
            
            self.settings.New(ax_name + '_servo', dtype=bool, ro=False)
            
            self.settings.New(ax_name + "_velocity", dtype=float, vmin=0, vmax=0.6, ro=False,
                              si=False, spinbox_decimals=3, unit='mm/s')
    
            self.settings.New(ax_name + "_on_target", dtype=bool, ro=True)
            
            self.rangemin = self.add_logged_quantity("rangemin", dtype=float, unit='mm', ro=True)
            self.rangemax = self.add_logged_quantity("rangemax", dtype=float, unit='mm', ro=True)
            

            self.add_operation("stop", self.stop)
            self.add_operation("set_home", self.set_home)
            self.add_operation("go_home", self.go_home)
            
    def connect(self):
        
        S = self.settings

        self.gcs = GCSDevice(S.controller.val)        
        self.gcs.ConnectRS232(comport=8, baudrate=38400)
        #self.gcs.ConnectUSB(serialnum='0135500849')
        print(self.gcs.qPOS(self.gcs.axes)['1'])
        if S.initial_ref_mode.val != 'None':
            pitools.startup(self.gcs, stages=S.stage.val, refmode=S.ref_mode.val)
        else:
            pitools.startup(self.gcs, stages=S.stage.val, refmode=None)
            self.gcs.RON(self.gcs.axes, False)
            self.gcs.POS(self.gcs.axes, self.gcs.qPOS(self.gcs.axes)['1'])

        #self.gcs.MVR(self.gcs.axes, 0.1)
        
        #print(self.gcs.IsMoving(self.gcs.axes)['1'])
        
        self.rangemin.hardware_read_func = self.GetRangeMN
        self.rangemax.hardware_read_func = self.GetRangeMX

        self.rangemin.read_from_hardware()
        self.rangemax.read_from_hardware()
       
        
         
       
        
        for ax_num, ax_name in self.axes.items():
            
            lq = S.get_lq(ax_name + "_position")
            lq.connect_to_hardware(
                read_func = lambda n=ax_num: self.gcs.qPOS()[str(n)]
                )
            lq.read_from_hardware()
            
            lq = S.get_lq(ax_name + "_target")
            lq.connect_to_hardware(
                read_func  = lambda n=ax_num: self.gcs.qMOV()[str(n)],
                write_func = lambda new_target, n=ax_num: self.gcs.MOV(n, new_target)
                )
            lq.read_from_hardware()
            
            lq = S.get_lq(ax_name + "_servo")
            lq.connect_to_hardware(
                read_func  = lambda n=ax_num: self.gcs.qSVO()[str(n)],
                write_func = lambda enable, n=ax_num: self.gcs.SVO(n, enable )
                )
            lq.read_from_hardware()
            
            lq = S.get_lq(ax_name + "_on_target")
            lq.connect_to_hardware(
                read_func  = lambda n=ax_num: self.gcs.qONT()[str(n)],
                )
            lq.read_from_hardware()
            
            lq = S.get_lq(ax_name + "_velocity")
            lq.connect_to_hardware(
                read_func  = lambda n=ax_num: self.gcs.qVEL()[str(n)],
                write_func = lambda new_vel, n=ax_num: self.gcs.VEL(n, new_vel )
                )
            lq.read_from_hardware()
            
        
        
        self.update_thread_interrupted = False
        self.update_thread = threading.Thread(target=self.update_thread_run)
        self.update_thread.start()   


        
        
        
        
    def disconnect(self):
        
        if hasattr(self, 'gcs'):
            self.gcs.SVO(self.gcs.axes, False)
        
        self.settings.disconnect_all_from_hardware()
        #if hasattr(self, 'update_timer'):
        #    self.update_timer.stop()
        if hasattr(self, 'update_thread'):
            self.update_thread_interrupted = True
            self.update_thread.join(timeout=1.0)
            del self.update_thread
            
        if hasattr(self, 'gcs'):
            self.gcs.close()
            del self.gcs
        
        
    def GetRangeMN(self):
        return float(list(self.gcs.qTMN().values())[0])
    def GetRangeMX(self):
        return float(list(self.gcs.qTMX().values())[0])
   
        
    def update_thread_run(self):
        while not self.update_thread_interrupted:
            for ax_num, ax_name in self.axes.items():
                self.settings.get_lq(ax_name + "_position").read_from_hardware()
                self.settings.get_lq(ax_name + "_on_target").read_from_hardware()
            time.sleep(0.050)
            
    def stop(self):
        if hasattr(self, 'gcs'):
            self.gcs.STP()   
            
    def set_home(self):
        if hasattr(self, 'gcs'):
            self.gcs.DFH(self.gcs.axes)
            
        
    def go_home(self):
        if hasattr(self, 'gcs'):
            self.gcs.GOH(self.gcs.axes)


  