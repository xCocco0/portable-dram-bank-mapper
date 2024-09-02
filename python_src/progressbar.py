
import time

class ProgressBar:

    __markers = ["/","-","\\","|"]

    def __init__(self, iterations, update_delay, width = 60):
        self.iterations = iterations
        self.i = 0

        self.marker_index = 0
        self.i_digits = len(str(iterations))
        self.width = width

        self.delay = update_delay
        self.start_t = time.time()
        self.end_t = None
        self.last_t = self.start_t

        self.progress()

    
    def progress(self, text = ""):

        text_count = f"[{self.i:{self.i_digits}d}/{self.iterations}]"
        text_marker = f" {self.__markers[self.marker_index]}"
        end = "\r"
            
        self.marker_index += 1
        self.marker_index %= len(self.__markers)
    
        if self.i == self.iterations:
            self.end_t = time.time()

        if self.i >= self.iterations:
            text_timing = f"Completed: {self.end_t - self.start_t:.0f}s"
            end = "\n"
        else:
            self.i += 1

            if self.i == 0:
                text_timing = ""
            else:

                elapsed_t = time.time() - self.start_t
                remaining_t = (elapsed_t/self.i)*(self.iterations-self.i)

                text_timing = f"Elapsed: {elapsed_t:.0f}s, Remaining: {remaining_t:.0f}s"

            if time.time() - self.last_t <= self.delay:
                return

        text_leftpart = text_count + "  " + text_timing
        if text != "": text_leftpart += "  " + text
        text_rightpart = "  " + text_marker + " "

        print(f"{text_leftpart:{self.width-len(text_rightpart)}s}", end = "")
        print(text_rightpart, end = end)

        self.last_t = time.time()
        
        
