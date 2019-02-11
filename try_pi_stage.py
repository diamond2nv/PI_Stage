from ScopeFoundry import BaseMicroscopeApp

class TryPIStage(BaseMicroscopeApp):

    # this is the name of the microscope that ScopeFoundry uses 
    # when storing data
    name = 'try_pi_stage'
    
    # You must define a setup function that adds all the 
    #capablities of the microscope and sets default settings
    def setup(self):
        
        #Add App wide settings
        
        #Add hardware components
        from pi_stage_HW_test import PIStage
        self.add_hardware(PIStage(self))
        
        
        # Connect to custom gui
        # load side panel UI
        # show ui
        self.ui.show()
        self.ui.activateWindow()


if __name__ == '__main__':
    
    import sys
    app = TryPIStage(sys.argv)
    sys.exit(app.exec_())