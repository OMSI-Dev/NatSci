"""
Presentation Controller for LibreOffice Impress
Provides slide navigation and control for .odp presentations.
"""

import os
import time
import subprocess


class PowerPointShowController:
    """Controller for LibreOffice Impress presentations."""
    
    def __init__(self, slideshow):
        """
        Initialize the controller.
        
        Args:
            slideshow: Full path to the .odp presentation file
        """
        self.slideshow = slideshow
        self.app = None
        self.show = None
        self.presentation = None
        self.launched = False
        self.count = 0
        
        # Verify file extension
        ext = os.path.splitext(slideshow)[1].lower()
        if ext != '.odp':
            raise ValueError(f"Only .odp files supported. Got: {ext}")
    
    def launchpp(self, RunShow=True):
        """
        Launch LibreOffice Impress and open the presentation.
        Uses Windows COM for programmatic control.
        
        Args:
            RunShow: If True, start the slideshow automatically
        """
        try:
            from win32com.client import Dispatch
            
            # Launch LibreOffice with --norestore parameter to disable crash recovery
            file_url = "file:///" + self.slideshow.replace("\\", "/")
            
            # Find LibreOffice installation path
            libreoffice_paths = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
            ]
            
            soffice_path = None
            for path in libreoffice_paths:
                if os.path.exists(path):
                    soffice_path = path
                    break
            
            if not soffice_path:
                print("Warning: Could not find LibreOffice installation, attempting COM connection only")
            else:
                # Start LibreOffice process with --norestore flag AND the file to open
                subprocess.Popen([
                    soffice_path,
                    "--norestore",
                    "--nologo",
                    self.slideshow
                ])
                
                # Wait for LibreOffice to initialize
                time.sleep(3)
            
            # Connect via COM
            self.app = Dispatch('com.sun.star.ServiceManager')
            desktop = self.app.createInstance('com.sun.star.frame.Desktop')
            
            # Open the presentation
            self.show = desktop.loadComponentFromURL(file_url, "_blank", 0, ())
            
            if RunShow:
                presentation = self.show.getPresentation()
                presentation.start()
                time.sleep(2)
                self.presentation = presentation
                self.launched = True
            
            self.count = self.get_slide_total()
            # print(f"[Success] LibreOffice Impress launched: {self.count} slides")
        
        except Exception as e:
            print(f"Error launching LibreOffice: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def goto(self, number):
        """
        Navigate to a specific slide number.
        
        Args:
            number: Slide number to navigate to (1-indexed)
        """
        if not self.launched:
            print("Warning: Presentation not launched, cannot navigate")
            return
        
        if number < 1 or number > self.count:
            print(f"Warning: Slide number {number} out of range (1-{self.count})")
            number = max(1, min(number, self.count))
        
        try:
            controller = self.presentation.getController()
            if controller:
                controller.gotoSlideIndex(number - 1)  # 0-indexed
            else:
                print("Warning: Could not get controller for slide navigation")
        except Exception as e:
            print(f"Error navigating to slide {number}: {e}")
    
    def get_slide_total(self):
        """
        Get the total number of slides in the presentation.
        
        Returns:
            int: Total slide count
        """
        if self.show:
            try:
                self.count = self.show.getDrawPages().getCount()
            except Exception as e:
                print(f"Error getting slide count: {e}")
                self.count = 0
        return self.count
    
    def close(self):
        """Close presentation and cleanup."""
        if self.app:
            try:
                if self.show:
                    self.show.close(True)
            except Exception as e:
                print(f"Error closing presentation: {e}")
            finally:
                self.show = None
                self.app = None
                self.presentation = None
                self.launched = False
