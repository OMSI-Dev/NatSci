"""
Simplified Presentation Controller
Handles PowerPoint/LibreOffice Impress control with programmatic slide navigation.
Uses win32com for Windows COM automation.
"""

import os


class PowerPointShowController:
    """Controller for PowerPoint/LibreOffice Impress presentations."""
    
    def __init__(self, slideshow):
        """
        Initialize the controller.
        
        Args:
            slideshow: Full path to the presentation file (supports .ppt, .pptx, .odp)
        """
        self.slideshow = slideshow
        self.app = None
        self.show = None
        self.presentation = None
        self.launched = False
        self.count = 0
        
        # Determine if using PowerPoint or LibreOffice based on file extension
        ext = os.path.splitext(slideshow)[1].lower()
        self.is_powerpoint = ext in ['.ppt', '.pptx']
        self.is_libreoffice = ext in ['.odp']
    
    def launchpp(self, RunShow=True):
        """
        Launch presentation software and open the presentation.
        Uses Windows COM for programmatic control.
        
        Args:
            RunShow: If True, start the slideshow automatically
        """
        try:
            from win32com.client import Dispatch
            import time
            
            if self.is_powerpoint:
                # Use PowerPoint
                print("  Launching PowerPoint...")
                self.app = Dispatch('Powerpoint.Application')
                self.app.Visible = 1
                
                print(f"  Opening: {self.slideshow}")
                self.show = self.app.Presentations.Open(FileName=self.slideshow)
                
                if RunShow:
                    print("  Starting slideshow...")
                    self.presentation = self.show.SlideShowSettings.Run()
                    self.launched = True
                
                self.count = self.get_slide_total()
                print(f"✓ PowerPoint launched: {self.count} slides")
                
            elif self.is_libreoffice:
                # Use LibreOffice via COM
                print("  Launching LibreOffice Impress...")
                self.app = Dispatch('com.sun.star.ServiceManager')
                desktop = self.app.createInstance('com.sun.star.frame.Desktop')
                
                # Convert to file URL
                file_url = "file:///" + self.slideshow.replace("\\", "/")
                print(f"  Opening: {self.slideshow}")
                
                self.show = desktop.loadComponentFromURL(file_url, "_blank", 0, ())
                
                if RunShow:
                    print("  Starting slideshow...")
                    presentation = self.show.getPresentation()
                    presentation.start()
                    time.sleep(2)
                    self.presentation = presentation
                    self.launched = True
                
                self.count = self.get_slide_total()
                print(f"✓ LibreOffice Impress launched: {self.count} slides")
            
            else:
                raise Exception(f"Unsupported file type: {os.path.splitext(self.slideshow)[1]}")
            
        except Exception as e:
            print(f"Error launching presentation: {e}")
            print(f"File path: {self.slideshow}")
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
            if self.is_powerpoint:
                # PowerPoint navigation
                self.presentation.View.GotoSlide(number)
                print(f"  → Navigated to slide {number}")
            elif self.is_libreoffice:
                # LibreOffice navigation
                controller = self.presentation.getController()
                if controller:
                    controller.gotoSlideIndex(number - 1)  # 0-indexed
                    print(f"  → Navigated to slide {number}")
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
                if self.is_powerpoint:
                    self.count = self.show.Slides.count
                elif self.is_libreoffice:
                    self.count = self.show.getDrawPages().getCount()
            except Exception as e:
                print(f"Error getting slide count: {e}")
                self.count = 0
        return self.count
    
    def close(self):
        """Close presentation and cleanup."""
        if self.app:
            try:
                if self.is_powerpoint:
                    if self.show:
                        self.show.Save()
                    self.app.Quit()
                    print("PowerPoint closed")
                elif self.is_libreoffice:
                    if self.show:
                        self.show.close(True)
                    print("LibreOffice Impress closed")
            except Exception as e:
                print(f"Warning: Error closing presentation: {e}")
            finally:
                self.show = None
                self.app = None
                self.presentation = None
                self.launched = False
