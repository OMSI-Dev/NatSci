from win32com.client import constants, Dispatch
import time

class PowerPointShowController:
    def  __init__(self,slideshow):
        self.slideshow = slideshow
        self.app = None
        self.show = None
        self.presentation = None
        self.launched = False
        self.count = 0
        
    def launchpp(self,RunShow=True,debug=False):
        """
        launchpp(Runshow:
        launches powerpoint, opens slideshow, and starts the presentation
        Input: slideshow - string of the full path to the desired show
        Output: tuple (success,runslide)
                success - bool of success
                runslide - pointer to an instance of a running show
        """
        self.app = Dispatch('Powerpoint.Application')
        self.app.Visible = 1
        self.show = self.app.Presentations.Open(FileName=self.slideshow)
        if RunShow:
            self.presentation = self.show.SlideShowSettings.Run()
            self.launched = True
        if debug:
            print ("PowerPoint Launched Successfully")
        self.count = self.get_slide_total()
        return (True,None)

    def create_slide(self,title,totalslides):
        if self.launched:
            return (False,None)
        slide = self.show.Slides.Add(totalslides,1)
        time.sleep(1)
        title = title.strip()
        slide.Shapes.Item(1).TextFrame.TextRange.Text=title
        self.show.Save()

    def goto(self,number):
        if self.launched:
            if number <= self.count:
                try:
                    self.presentation.View.GotoSlide(number)
                except:
                    print ("Failed to goto slide")
            else:
                print ("Slide Number is not in range, Check Database")
                self.presentation.View.GotoSlide(1)
            return (True,None)
        return (False,None)

    def get_slide_total(self):
        self.count = self.show.Slides.count
        return self.count

    def close(self):
        if self.app:
            try:
                self.show.Save()
            except:
                print("Warning: Power Point Slide Show could not be saved")
            self.app.Quit()
            self.show = None
            self.app = None


    