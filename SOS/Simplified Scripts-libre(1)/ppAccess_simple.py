"""
Simplified LibreOffice Impress Controller
Handles LibreOffice Impress application control and slide navigation.
"""

import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.uno import RuntimeException
import os


class PowerPointShowController:
    """Controller for LibreOffice Impress presentations."""
    
    def __init__(self, slideshow):
        """
        Initialize the controller.
        
        Args:
            slideshow: Full path to the presentation file (supports .ppt, .pptx, .odp)
        """
        self.slideshow = slideshow
        self.local_context = None
        self.smgr = None
        self.desktop = None
        self.document = None
        self.presentation = None
        self.controller = None
        self.launched = False
        self.count = 0
    
    def _create_uno_service(self, service_name):
        """Helper to create UNO services."""
        return self.smgr.createInstanceWithContext(service_name, self.local_context)
    
    def _create_property(self, name, value):
        """Helper to create PropertyValue objects."""
        prop = PropertyValue()
        prop.Name = name
        prop.Value = value
        return prop
    
    def launchpp(self, RunShow=True):
        """
        Launch LibreOffice Impress and open the presentation.
        
        Args:
            RunShow: If True, start the slideshow automatically
        """
        try:
            print("  Starting LibreOffice...")
            
            import subprocess
            import time
            
            # Launch LibreOffice directly with the presentation file
            print("  Launching LibreOffice Impress with presentation...")
            
            # Try multiple possible LibreOffice paths
            possible_paths = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
                r"C:\Program Files\LibreOffice\program\simpress.exe",
            ]
            
            libreoffice_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    libreoffice_path = path
                    print(f"  Found LibreOffice at: {path}")
                    break
            
            if not libreoffice_path:
                raise Exception("Could not find LibreOffice installation")
            
            # Start LibreOffice Impress with the presentation
            if RunShow:
                # Start in presentation mode - use soffice.exe with impress and show
                process = subprocess.Popen(
                    [libreoffice_path, "--impress", "--show", self.slideshow],
                    creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                )
            else:
                # Just open the file
                process = subprocess.Popen(
                    [libreoffice_path, "--impress", self.slideshow],
                    creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
                )
            
            print(f"  ✓ LibreOffice process started (PID: {process.pid})")
            print("  Note: Running in standalone mode (limited programmatic control)")
            
            # Wait for it to start
            time.sleep(3)
            
            # Skip UNO connection for now - it hangs on this system
            print("  Skipping programmatic control (running standalone)")
            self.launched = True
            self.count = 0
            
            print(f"\nLibreOffice Impress launched successfully!")
            print("Running in standalone mode (manual control only)")
            print("The presentation should now be visible on your screen.")
            
        except Exception as e:
            print(f"Error launching LibreOffice Impress: {e}")
            print(f"File path: {self.slideshow}")
            print("Make sure LibreOffice is installed and the file path is correct.")
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
            print("Warning: Slideshow not launched")
            return
        
        if number < 1 or number > self.count:
            print(f"Warning: Slide {number} out of range (1-{self.count}). Going to slide 1.")
            number = 1
        
        try:
            # Convert to 0-indexed for UNO API
            slide_index = number - 1
            
            # Get the draw pages (slides)
            draw_pages = self.document.getDrawPages()
            
            if slide_index < draw_pages.getCount():
                # Get the target slide
                target_slide = draw_pages.getByIndex(slide_index)
                
                # Navigate using presentation controller
                if self.presentation:
                    # Get presentation controller
                    pres_controller = self.document.getCurrentController()
                    if hasattr(pres_controller, 'gotoSlideIndex'):
                        pres_controller.gotoSlideIndex(slide_index)
                    else:
                        # Alternative: set current page
                        pres_controller.setCurrentPage(target_slide)
                        
        except Exception as e:
            print(f"Error navigating to slide {number}: {e}")
    
    def get_slide_total(self):
        """
        Get the total number of slides in the presentation.
        
        Returns:
            int: Total slide count
        """
        if self.document:
            try:
                draw_pages = self.document.getDrawPages()
                self.count = draw_pages.getCount()
            except Exception as e:
                print(f"Error getting slide count: {e}")
                self.count = 0
        return self.count
    
    def close(self):
        """Close LibreOffice Impress and cleanup."""
        if self.document:
            try:
                # Stop presentation if running
                if self.presentation and self.launched:
                    try:
                        self.presentation.end()
                    except:
                        pass
                
                # Close the document
                self.document.close(True)
                print("LibreOffice Impress closed")
            except Exception as e:
                print(f"Warning: Error closing LibreOffice Impress: {e}")
            finally:
                self.document = None
                self.presentation = None
                self.controller = None
                self.desktop = None
                self.smgr = None
                self.local_context = None
                self.launched = False
