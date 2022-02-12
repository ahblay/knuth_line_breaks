import math
import os
from pprint import pprint as pp


# simple class for storing information about potential line break sequences
class Path:
    def __init__(self, breaks=None, score=0, indices=None, adjustments=None):

        if breaks is None:
            self.breaks = []
            self.current_end = ''
        else:
            self.breaks = breaks
            self.current_end = self.breaks[-1]

        if indices is None:
            self.indices = []
            self.current_index = -1
        else:
            self.indices = indices
            self.current_index = self.indices[-1]

        if adjustments is None:
            self.adjustments = []
        else:
            self.adjustments = adjustments

        self.length = len(self.current_end)
        self.score = score


# function to render latex document with inter-word spacing as determined by calculate_breakpoints
def to_latex(sample, solution):
    pp(solution.__dict__)

    header = [
        '\documentclass{article}',
        '\\usepackage[margin=1in]{geometry}',
        '\setlength\parindent{0pt}',
        '\\renewcommand{\\familydefault}{\\ttdefault}',
        '\\begin{document}'
        ]
    footer = '\end{document}'

    with open('output.tex', 'w') as f:
        f.writelines('\n'.join(header))
        counter = 0
        solution.adjustments.append(0)
        sample.insert(0, f'\n\n \\fontdimen2\\font={solution.adjustments[counter]}em')
        counter += 1
        for index in solution.indices:
            sample.insert(index + 1 + counter, f'\n\n \\fontdimen2\\font={solution.adjustments[counter]}em')
            counter += 1
        f.writelines(' '.join(sample))
        f.writelines('\n')
        f.writelines(footer)

    os.system("pdflatex output.tex")


# main function to calculate optimal line breaks
def calculate_breakpoints(sample, target, candidate_breaks, tolerance):
    last = False

    # iterate through each word (or candidate line break) in text sample
    for word_index, word in enumerate(sample):

        #target += (1/10)

        # initialize variables for storing information regarding the location and cost of potential line breaks
        best_score = math.inf
        best_break = Path()
        line_adjustment = 0
        updated = False
        if word_index == len(sample) - 1:
            last = True

        # iterate over list of candidate breakpoints
        for n in candidate_breaks:

            # calculate distance from each candidate's most recent line break to the current word
            line = sample[n.current_index + 1: word_index + 1]
            #print(line)

            # check if this distance is within tolerable range

            feasible = demerits(line, target, tolerance, last)
            #print(feasible)

            # if distance is tolerable, consider the cost of adding a line break after current word
            if feasible[0]:
                updated = True
                # update candidate line break if the cost of breaking is minimized
                # store candidate line break information in variables defined above
                if feasible[1] + n.score < best_score:
                    best_break = n
                    best_score = feasible[1] + n.score
                    line_adjustment = feasible[2]

            # if the distance from n to word is too long for a line, remove n from the list of candidate breakpoints
            elif feasible[1] < -1:
                candidate_breaks.remove(n)

        if updated:
            # save sequence of line breaks leading up to best_break
            new_break = Path(best_break.breaks + [word],
                             best_score,
                             best_break.indices + [word_index],
                             best_break.adjustments + [line_adjustment])
            # add node to active_nodes
            candidate_breaks.append(new_break)
            #print(new_break.__dict__)
        #print('\n')

    # find the cheapest solution from the list of possible line breaks
    cheapest = math.inf
    best_solution = None
    for sequence in candidate_breaks:
        if sequence.score < cheapest:
            best_solution = sequence

    # render resulting solution in latex
    to_latex(sample, best_solution)

    return best_solution.breaks, best_solution.indices, best_solution.adjustments


# we shall measure line width as a function of letter width in monospaced font
def demerits(line, target, tolerance, last):

    '''
    penalty = 0
    if line[-1] == '\n':
        penalty = -math.inf
    '''

    space_width = 1
    line_length = 0
    spaces = -1

    for word in line:
        # length of word
        line_length += len(word)
        # length of space
        line_length += space_width

        # account for double-spacing after end of sentence in monospace fonts
        if word[-1] in ['.', '?', '!']:
            line_length += 1

        # counter for spaces in a line
        spaces += 1
    # removes last space
    line_length -= space_width

    # removes extra space if line ends when sentence ends
    if line[-1][-1] in ['.', '?', '!']:
        line_length -= 1

    # the amount we need to adjust the space between words to attain the target width
    adjustment = target - line_length
    #print(f"Adjustment: {adjustment}")

    # allowable stretch and shrink factors of space between words
    stretch = 0.5 * spaces
    shrink = 0.3 * spaces

    # ratio of adjustment necessary
    if adjustment <= 0:
        if shrink == 0:
            adj_ratio = -math.inf
        else:
            # percentage of maximum shrink to apply to each space
            adj_ratio = adjustment / shrink
            # size of space in terms of em-dashes
            # each space is standardized to 0.5em
            em_dashes = (adj_ratio * 0.3 * 0.5) + 0.5
    else:
        if stretch == 0:
            adj_ratio = math.inf
        else:
            # percentage of maximum stretch to apply to each space
            adj_ratio = adjustment / stretch
            em_dashes = (adj_ratio * 0.5 * 0.5) + 0.5

    # unacceptable cases
    if adj_ratio < -1:
        return False, adj_ratio
    if adj_ratio > tolerance:
        return False, adj_ratio

    # score for the badness of a potential line break
    bad = (abs(adj_ratio)**3)*100+0.5

    '''
    # total demerits including considerations for lines with a forced break, and final line
    if last:
        dem = bad**2
    elif penalty < 0:
        dem = bad**2 - penalty**2
    else:
        dem = bad**2 + penalty**2
    '''

    # acceptable
    return True, bad, em_dashes


# saves sample text to array
# attempts to handle forced line breaks (\n characters) but doesn't work
def to_array(sample):
    paragraphs = [paragraph for paragraph in sample.split('\n')]
    words = []
    for paragraph in paragraphs:
        words.extend(paragraph.split())
        words.append('\n')
    words.pop(-1)
    pp(words)
    return words

with open('sample.txt', 'r') as f:
    array = to_array(f.read())
    pp(array)

initial_active_node = [Path()]
result = calculate_breakpoints(array, 40, initial_active_node, 5)
#print(result)
#print(no_numbers)





