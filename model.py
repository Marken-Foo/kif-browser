import os
import re

from enum import Enum

from event import Emitter, ProbDirEvent, ProbStatusEvent, ProbTimeEvent
from kif_parser import KifReader


class ProblemStatus(Enum):
    NONE = 0; CORRECT = 1; WRONG = 2; SKIP = 3


class Problem:
    '''Data class representing one tsume problem.'''
    def __init__(self, filename):
        self.filename = filename
        self.time = None
        self.status = ProblemStatus.NONE
        return


class Model(Emitter):
    # Following MVC principles, this is the data model of the program.
    @staticmethod
    def natural_sort_key(str, _nsre=re.compile(r'(\d+)')):
        return [int(c) if c.isdigit() else c.lower() for c in _nsre.split(str)]
    
    def __init__(self):
        self.problems = []
        self.curr_prob_idx = None
        self.curr_prob = None
        self.directory = None # not currently used meaningfully
        self.reader = KifReader()
        self.solution = ""
        self.observers = [] # Observer pattern, to sync Views to it
    
    def read_problem(self):
        # Read current problem into reader.
        # Try any likely encodings for the KIF files
        encodings = ["cp932", "utf-8"]
        for e in encodings:
            try:
                with open(self.curr_prob.filename, "r", encoding=e) as kif:
                    self.reader.parse_kif(kif)
                    self.solution = "　".join(self.reader.moves)
            except UnicodeDecodeError:
                pass
            else:
                break
        return self.reader
    
    def set_directory(self, directory):
        self.directory = directory
        with os.scandir(directory) as it:
            self.problems = [
                Problem(os.path.join(directory, entry.name))
                for entry in it
                if entry.name.endswith(".kif") or entry.name.endswith(".kifu")
            ]
        self.problems.sort(key=lambda p: Model.natural_sort_key(p.filename))
        self.curr_prob_idx = 0
        self.curr_prob = self.problems[self.curr_prob_idx]
        self.read_problem()
        self._notify_observers(ProbDirEvent(self.problems))
        return
    
    def open_next_file(self):
        if self.curr_prob_idx+1 >= len(self.problems):
            return False
        self.curr_prob = self.problems[self.curr_prob_idx + 1]
        self.curr_prob_idx += 1
        self.read_problem()
        return True
    
    def open_prev_file(self):
        if self.curr_prob_idx-1 < 0:
            return False
        self.curr_prob = self.problems[self.curr_prob_idx - 1]
        self.curr_prob_idx -= 1
        self.read_problem()
        return True
    
    def open_file(self, idx):
        if idx >= len(self.problems) or idx < 0:
            return False
        self.curr_prob = self.problems[idx]
        self.curr_prob_idx = idx
        self.read_problem()
        return True
    
    def set_correct(self):
        if self.curr_prob is not None:
            self.curr_prob.status = ProblemStatus.CORRECT
            self._notify_observers(ProbStatusEvent(self.curr_prob_idx, ProblemStatus.CORRECT))
        return
    
    def set_wrong(self):
        if self.curr_prob is not None:
            self.curr_prob.status = ProblemStatus.WRONG
            self._notify_observers(ProbStatusEvent(self.curr_prob_idx, ProblemStatus.WRONG))
        return
    
    def set_skip(self):
        if self.curr_prob is not None:
            self.curr_prob.status = ProblemStatus.SKIP
            self._notify_observers(ProbStatusEvent(self.curr_prob_idx, ProblemStatus.SKIP))
        return
    
    def set_time(self, time):
        if self.curr_prob is not None:
            self.curr_prob.time = time
            self._notify_observers(ProbTimeEvent(self.curr_prob_idx, time))
        return
