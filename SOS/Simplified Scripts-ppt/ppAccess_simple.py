"""
Simplified PowerPoint Controller
Handles PowerPoint application control and slide navigation.
"""

from win32com.client import Dispatch


class PowerPointShowController:
    """Controller for PowerPoint presentations."""
    
    def __init__(self, slideshow):
        """
        Initialize the controller.
        
        Args:
            slideshow: Full path to the PowerPoint file
        """
        self.slideshow = slideshow
        self.app = None
        self.show = None
        self.presentation = None
        self.launched = False
        self.count = 0
    
    def launchpp(self, RunShow=True):
        """
        Launch PowerPoint and open the presentation.
        
        Args:
            RunShow: If True, start the slideshow automatically
        """
        try:
            # Create PowerPoint Application object
            self.app = Dispatch('Powerpoint.Application')
            self.app.Visible = 1
            
            # Open the presentation
            self.show = self.app.Presentations.Open(FileName=self.slideshow)
            
            # Start slideshow if requested
            if RunShow:
                self.presentation = self.show.SlideShowSettings.Run()
                self.launched = True
            
            # Get total slide count
            self.count = self.get_slide_total()
            
            print(f"PowerPoint launched: {self.count} slides")
            
        except Exception as e:
            print(f"Error launching PowerPoint: {e}")
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
            self.presentation.View.GotoSlide(number)
        except Exception as e:
            print(f"Error navigating to slide {number}: {e}")
    
    def get_slide_total(self):
        """
        Get the total number of slides in the presentation.
        
        Returns:
            int: Total slide count
        """
        if self.show:
            self.count = self.show.Slides.count
        return self.count
    
    def close(self):
        """Close PowerPoint and cleanup."""
        if self.app:
            try:
                if self.show:
                    self.show.Save()
                self.app.Quit()
                print("PowerPoint closed")
            except Exception as e:
                print(f"Warning: Error closing PowerPoint: {e}")
            finally:
                self.show = None
                self.app = None
                self.presentation = None
                self.launched = False
