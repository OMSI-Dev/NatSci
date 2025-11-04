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
            print("  Starting LibreOffice with UNO connection...")
            
            import subprocess
            import time
            
            # Start LibreOffice in listening mode for UNO connections
            # This allows us to connect programmatically
            possible_paths = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            ]
            
            libreoffice_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    libreoffice_path = path
                    print(f"  Found LibreOffice at: {path}")
                    break
            
            if not libreoffice_path:
                raise Exception("Could not find LibreOffice installation")
            
            # Start LibreOffice with socket connection enabled
            print("  Starting LibreOffice in server mode...")
            process = subprocess.Popen(
                [libreoffice_path, "--accept=socket,host=localhost,port=2002;urp;StarOffice.ServiceManager", "--norestore", "--nofirststartwizard", "--nologo", "--nolockcheck"],
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            print(f"  ✓ LibreOffice process started (PID: {process.pid})")
            print("  Waiting for LibreOffice to initialize...")
            time.sleep(5)
            
            # Connect via UNO
            print("  Connecting to LibreOffice via UNO...")
            self.local_context = uno.getComponentContext()
            resolver = self.local_context.ServiceManager.createInstanceWithContext(
                "com.sun.star.bridge.UnoUrlResolver", self.local_context
            )
            
            # Connect to the running LibreOffice instance
            ctx = resolver.resolve(
                "uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext"
            )
            self.smgr = ctx.ServiceManager
            self.desktop = self._create_uno_service("com.sun.star.frame.Desktop")
            
            print("  ✓ Connected to LibreOffice via UNO")
            
            # Convert file path to URL format
            if os.path.exists(self.slideshow):
                from urllib.parse import quote
                file_url = "file:///" + self.slideshow.replace("\\", "/")
            else:
                raise Exception(f"Presentation file not found: {self.slideshow}")
            
            # Load the presentation
            print(f"  Loading presentation: {self.slideshow}")
            props = [self._create_property("Hidden", False)]
            self.document = self.desktop.loadComponentFromURL(file_url, "_blank", 0, tuple(props))
            
            if not self.document:
                raise Exception("Failed to load presentation document")
            
            print("  ✓ Presentation loaded")
            
            # Get slide count
            self.count = self.get_slide_total()
            print(f"  Total slides: {self.count}")
            
            # Start presentation if requested
            if RunShow:
                print("  Starting slideshow...")
                self.presentation = self.document.getPresentation()
                self.presentation.start()
                time.sleep(2)
                print("  ✓ Slideshow started")
            
            self.launched = True
            print(f"\n✓ LibreOffice Impress launched successfully with UNO control!")
            
        except Exception as e:
            print(f"Error launching LibreOffice Impress: {e}")
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
        
        # Basic validation
        if number < 1:
            print(f"Warning: Invalid slide number {number}. Must be >= 1.")
            return
        
        # Validate against known slide count if available
        if self.count > 0 and number > self.count:
            print(f"Warning: Slide {number} exceeds total slides ({self.count}). Clamping to {self.count}.")
            number = self.count
        
        try:
            if not self.document:
                print(f"Error: No document loaded. Cannot navigate to slide {number}")
                return
            
            # Convert to 0-indexed for UNO API
            slide_index = number - 1
            
            # Get the draw pages (slides)
            draw_pages = self.document.getDrawPages()
            
            if slide_index >= draw_pages.getCount():
                print(f"Warning: Slide {number} (index {slide_index}) exceeds available slides ({draw_pages.getCount()})")
                return
            
            # Get the target slide
            target_slide = draw_pages.getByIndex(slide_index)
            
            # Navigate using presentation controller
            if self.presentation:
                # Get the presentation controller (slideshow view)
                controller = self.presentation.getController()
                if controller:
                    # Use gotoSlideIndex if available
                    if hasattr(controller, 'gotoSlideIndex'):
                        controller.gotoSlideIndex(slide_index)
                        print(f"  → Navigated to slide {number}")
                    else:
                        # Fallback: use gotoBookmark or other method
                        controller.gotoFirstSlide()
                        for _ in range(slide_index):
                            controller.gotoNextSlide()
                        print(f"  → Navigated to slide {number} (via iteration)")
                else:
                    print(f"Warning: No presentation controller available")
            else:
                # Not in slideshow mode - just set the current page in edit view
                view_controller = self.document.getCurrentController()
                if view_controller:
                    view_controller.setCurrentPage(target_slide)
                    print(f"  → Set current page to slide {number} (edit mode)")
                        
        except Exception as e:
            print(f"Error navigating to slide {number}: {e}")
            import traceback
            traceback.print_exc()
    
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
