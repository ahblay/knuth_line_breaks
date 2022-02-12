import math
import os
from pprint import pprint as pp


# simple class for storing information about potential line break sequences
class Path:
    def __init__(self, breaks=None, score=0, indices=None, adjustments=None):

        # breaks is an array of the current sequence of line breaks
        # current_end stores most recent line break
        if breaks is None:
            self.breaks = []
            self.current_end = ''
        else:
            self.breaks = breaks
            self.current_end = self.breaks[-1]

        # indices is an array of the indices of line breaks in the sample text
        # current_index stores the index of the most recent line break
        if indices is None:
            self.indices = []
            self.current_index = -1
        else:
            self.indices = indices
            self.current_index = self.indices[-1]

        # adjustments is an array that stores the width of the spaces on each line as fractions of an em-dash
        if adjustments is None:
            self.adjustments = []
        else:
            self.adjustments = adjustments

        # length is the number of characters in the word at the end of the most recent line break
        # score is the cumulative score of the sequence of breaks
        self.length = len(self.current_end)
        self.score = score


# function to render LaTeX document with inter-word spacing as determined by calculate_breakpoints
def to_latex(sample, solution):

    # all of the basic code for rendering a LaTeX file
    header = [
        '\documentclass{article}',
        '\\usepackage[margin=1in]{geometry}',
        '\setlength\parindent{0pt}',
        '\\renewcommand{\\familydefault}{\\ttdefault}',
        '\\begin{document}'
        ]
    footer = '\end{document}'

    # a somewhat hacky solution to construct a LaTeX document where each line has the appropriate spacing
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

    # compiles the document
    os.system("pdflatex output.tex")


# main function to calculate optimal line breaks
def calculate_breakpoints(sample, target, candidate_breaks, tolerance):
    last = False

    # iterate through each word (or candidate line break) in text sample
    for word_index, word in enumerate(sample):

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

            # check if this distance is within tolerable range
            feasible = demerits(line, target, tolerance, last)

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

    # find the cheapest solution from the list of possible line breaks
    cheapest = math.inf
    best_solution = None
    for sequence in candidate_breaks:
        if sequence.score < cheapest:
            best_solution = sequence

    # handling for when the tolerance and line length are too low
    if not best_solution:
        raise ValueError("I am returning 'None' because I was "
                         "unable to find a viable solution with this tolerance "
                         "and line length. Increasing the tolerance will result in a solution. "
                         "Be warned of potentially unsightly spaces.")

    # render resulting solution in latex
    to_latex(sample, best_solution)

    return best_solution.breaks, best_solution.indices, best_solution.adjustments


# function to calculate cost of a candidate line break
# we shall measure line width as a function of letter width in monospaced font
def demerits(line, target, tolerance, last):

    space_width = 1
    line_length = 0
    spaces = -1

    # determine length of line
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
    em_dashes = 0.5
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
    # if adj_ratio < -1, then spaces must shrink beyond allowable limit
    if adj_ratio < -1:
        return False, adj_ratio
    # adj_ratio > tolerance, then spaces must stretch beyond tolerable limit
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

    # acceptable cases
    # if we are on the final line, disregard the score and simply use normal 0.5em spacing
    if last or line[-1] == '\n':
        return True, 0, 0.5
    return True, bad, em_dashes


# function to save sample text to array
# attempts to handle forced line breaks (\n characters) but doesn't work
def to_array(sample):
    paragraphs = [paragraph for paragraph in sample.split('\n')]
    words = []
    for paragraph in paragraphs:
        words.extend(paragraph.split())
        words.append('\n')
    words.pop(-1)
    return words

# initializes variables
with open('explanation.txt', 'r') as f:
    sample = to_array(f.read())
initial_active_node = [Path()]
line_width = 80
tolerance = 2

# run
calculate_breakpoints(sample, line_width, initial_active_node, tolerance)





