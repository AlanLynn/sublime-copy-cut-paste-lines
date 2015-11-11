"""A series of tests to verify that the commands work properly

To run the tests:
1. Open the console. (View->Show Console)
2. Paste the line below into the console then press enter.
   window.run_command('ccpl_run_tests')
"""

import sublime, sublime_plugin
import operator
import traceback
import CopyCutAndPasteLines.main


class CcplRunTestsCommand(sublime_plugin.WindowCommand):
    """Run the tests and show them in a new tab."""

    def description(self):
        return "Run CutCopyPasteLines tests"

    def run(self):
        # Open a new buffer to show the test results in.
        view = self.window.new_file()
        view.set_scratch(True)
        view.set_name("Test Results")
        # Need to run a text command to edit the view.
        view.run_command('ccpl_show_test_output')


class CcplShowTestOutputCommand(sublime_plugin.TextCommand):
    """Run the tests and show them in this tab."""

    def description(self):
        return "Run CutCopyPasteLines tests"

    def run(self, edit):
        view = self.view
        tests = get_tests()
        # Run the tests.
        output = ""
        pass_count = 0
        for test in tests:
            test_result = test.run(view, edit)
            # Output Pass/Fail.
            output += ("FAIL", "Pass")[test_result]
            output += " - " + test.name + test.fail_message + "\n"
            pass_count += test_result
        output = "{} of {} tests passed.\n\n".format(pass_count, len(tests)) + output
        # Show the output.
        view.replace(edit, sublime.Region(0, view.size()), "")
        view.insert(edit, 0, output)
        view.sel().clear()


def selections_equal(selection1, selection2):
    """Whether the selections are equivalent"""
    # To do: Merge overlapping regions?
    selection1 = sorted(selection1)
    selection2 = sorted(selection2)
    if len(selection1) != len(selection2):
        return False
    for index in range(0, len(selection1)):
        if selection1[index] != selection2[index]:
            return False
    return True


def cursor(position):
    """Returns a zero-width (cursor) selection at position."""
    return [sublime.Region(position, position)]

def region(start, end):
    """Returns a selection between start and end."""
    return [sublime.Region(start, end)]


class Test:
    """Runs a command and compares the end state to the expected state."""

    UNCHANGED = 'VALUE_UNCHANGED'
    ANY = 'VALUE_ANY'

    def __init__(
            self, name, command, initial_text, initial_selection,
            initial_clipboard='CLIPBOARD', correct_text=UNCHANGED,
            correct_selection=UNCHANGED, correct_clipboard=UNCHANGED):
        """Specifies all information needed to run the test.

        Args:
            initial_*: The initial state before command is run.
            correct_*:The expected state after command is run.
                -Use Test.UNCHANGED to mean that the value remain unchanged.
                -Use Test.ANY to mean that any value is acceptable.
            initial_selection & correct_selection: Array of sublime.Region
        """
        if correct_text == self.UNCHANGED:
            correct_text = initial_text
        if correct_selection == self.UNCHANGED:
            correct_selection = initial_selection
        if correct_clipboard == self.UNCHANGED:
            correct_clipboard = initial_clipboard
        self.name = name
        self.initial_text = initial_text
        self.initial_selection = initial_selection
        self.initial_clipboard = initial_clipboard
        self.command = command
        self.correct_text = correct_text
        self.correct_selection = correct_selection
        self.correct_clipboard = correct_clipboard
        self.fail_message = ""

    def run(self, view, edit):
        """Returns True for pass or False for fail.

        Sets self.fail_message if the test fails.
        """
        # Initial state
        view.replace(edit, sublime.Region(0, view.size()), self.initial_text)
        sublime.set_clipboard(self.initial_clipboard)
        view.sel().clear()
        for selection_region in self.initial_selection:
            view.sel().add(selection_region)
        # Run the command (cut/copy/paste/duplicate).
        try:
            # Call the command directly instead of using view.run_command, so
            # that errors can be caught and displayed.
            class_name = 'Ccpl' + self.command.capitalize() + 'Command'
            command_class = getattr(CopyCutAndPasteLines.main, class_name)
            command_object = command_class(view)
            command_object.run(edit)
        except:
            # Get the traceback message.
            self.fail_message = "\n" + traceback.format_exc()
            # Trim down long file paths.
            self.fail_message = self.fail_message.replace(
                sublime.packages_path(), 'Packages')
            self.fail_message = self.fail_message.replace(
                sublime.installed_packages_path(), 'Installed Packages')
            return False # Fail due to an exception.
        end_text = view.substr(sublime.Region(0, view.size()))
        # Check that the end state matches the correct state.
        pass_selection = self._test_value("selection", self.correct_selection,
                                          list(view.sel()), selections_equal)
        pass_clipboard = self._test_value("clipboard", self.correct_clipboard,
                                          sublime.get_clipboard())
        pass_text = self._test_value("text", self.correct_text, end_text)
        return pass_text and pass_clipboard and pass_selection

    def _test_value(self, name, correct_value, actual_value, equal=operator.eq):
        """Returns whether the value is correct.

        Sets self.fail_message if the value is incorrect."""
        if correct_value == self.ANY:
            # Any value is correct, so the test is guaranteed to pass.
            return True
        if not equal(actual_value, correct_value):
            self.fail_message = (
                "\n"
                "    Incorrect {}\n"
                "    Expected: {!r}\n"
                "    Received: {!r}"
                ).format(name, correct_value, actual_value)
            return False # Fail due to incorrect value.
        return True # Pass.


def get_tests():
    """Returns an array of all the tests to run."""
    return [
        Test("Empty buffer copy",
             initial_text='',
             initial_selection=cursor(0),
             command='copy',
             correct_clipboard='\n'
            ),
        Test("Empty buffer cut",
             initial_text='',
             initial_selection=cursor(0),
             command='cut',
             correct_clipboard='\n'
            ),
        Test("Empty buffer paste word",
             initial_text='',
             initial_selection=cursor(0),
             initial_clipboard='clipboard',
             command='paste',
             correct_text='clipboard',
             correct_selection=cursor(9)
            ),
        Test("Empty buffer paste line",
             initial_text='',
             initial_selection=cursor(0),
             initial_clipboard='line 1\n',
             command='paste',
             correct_text='line 1'
            ),
        Test("Empty buffer paste multiline",
             initial_text='',
             initial_selection=cursor(0),
             initial_clipboard='line 1\nline 2\n',
             command='paste',
             correct_text='line 1\nline 2'
            ),
        Test("Empty buffer duplicate",
             initial_text='',
             initial_selection=cursor(0),
             command='duplicate'
            ),
        Test("Null selection copy",
             initial_text='line 1\nline 2',
             initial_selection=[],
             command='copy'
            ),
        Test("Null selection cut",
             initial_text='line 1\nline 2',
             initial_selection=[],
             command='cut'
            ),
        Test("Null selection paste",
             initial_text='line 1\nline 2',
             initial_selection=[],
             command='paste'
            ),
        Test("Null selection duplicate",
             initial_text='line 1\nline 2',
             initial_selection=[],
             command='duplicate'
            ),
        Test("Copy word",
             initial_text='line 1\nline 2',
             initial_selection=region(0, 4),
             command='copy',
             correct_clipboard='line'
            ),
        Test("Cut word",
             initial_text='line 1\nline 2',
             initial_selection=region(0, 4),
             command='cut',
             correct_clipboard='line',
             correct_text=' 1\nline 2',
             correct_selection=cursor(0)
            ),
        Test("Paste word",
             # Pasting a word should move the cursor to the end of the paste.
             initial_text='line 1\nline 2\nline 3',
             initial_selection=cursor(9),
             initial_clipboard='CLIPBOARD',
             command='paste',
             correct_text='line 1\nliCLIPBOARDne 2\nline 3',
             correct_selection=cursor(18)
            ),
        Test("Duplicate word",
             initial_text='line 1\nline 2',
             initial_selection=region(0, 4),
             command='duplicate',
             correct_text='lineline 1\nline 2',
             correct_selection=region(4, 8)
            ),
        Test("Copy line",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=cursor(8),
             command='copy',
             correct_clipboard='line 2\n'
            ),
        Test("Cut line",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=cursor(8),
             command='cut',
             correct_text='line 1\nline 3',
             correct_clipboard='line 2\n'
            ),
        Test("Paste line",
             # Paste in the line below the cursor.
             initial_text='line 1\nline 2\nline 3',
             initial_selection=cursor(8),
             initial_clipboard='line 4\n',
             command='paste',
             correct_text='line 1\nline 2\nline 4\nline 3'
            ),
        Test("Duplicate line",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=cursor(8),
             command='duplicate',
             correct_text='line 1\nline 2\nline 2\nline 3'
            ),
        Test("Copy multiline",
             # Selecting parts of lines should still copy the full lines.
             initial_text='line 1\nline 2\nline 3\nline 4',
             initial_selection=region(8, 16),
             command='copy',
             correct_clipboard='line 2\nline 3\n'
            ),
        Test("Cut multiline",
             # Selecting parts of lines should still cut the full lines.
             initial_text='line 1\nline 2\nline 3\nline 4',
             initial_selection=region(8, 16),
             command='cut',
             correct_clipboard='line 2\nline 3\n',
             correct_text='line 1\nline 4',
             correct_selection=cursor(9)
            ),
        Test("Paste multiline",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=cursor(8),
             initial_clipboard='line 4\nline 5\n',
             command='paste',
             correct_text='line 1\nline 2\nline 4\nline 5\nline 3'
            ),
        Test("Duplicate multiline",
             # Selecting parts of lines should still duplicate the full lines.
             initial_text='line 1\nline 2\nline 3',
             initial_selection=region(8, 16),
             command='duplicate',
             correct_text='line 1\nline 2\nline 3\nline 2\nline 3'
            ),
        Test("Cut long line",
             # Make sure the cursor stays on the first line.
             initial_text='long line 1\nline 2\nline 3',
             initial_selection=cursor(10),
             command='cut',
             correct_text='line 2\nline 3',
             correct_clipboard='long line 1\n',
             correct_selection=cursor(6)
            ),
        Test("Copy blank line",
             initial_text='line 1\n\nline 3',
             initial_selection=cursor(7),
             command='copy',
             correct_clipboard='\n'
            ),
        Test("Cut blank line",
             initial_text='line 1\n\nline 3',
             initial_selection=cursor(7),
             command='cut',
             correct_text='line 1\nline 3',
             correct_clipboard='\n'
            ),
        Test("Duplicate blank line",
             initial_text='line 1\n\nline 3',
             initial_selection=cursor(7),
             command='duplicate',
             correct_text='line 1\n\n\nline 3'
            ),
        Test("Copy first line",
             initial_text='line 1\nline 2',
             initial_selection=cursor(1),
             command='copy',
             correct_clipboard='line 1\n'
            ),
        Test("Cut first line",
             initial_text='line 1\nline 2',
             initial_selection=cursor(1),
             command='cut',
             correct_clipboard='line 1\n',
             correct_text='line 2'
            ),
        Test("Duplicate first line",
             initial_text='line 1\nline 2',
             initial_selection=cursor(1),
             command='duplicate',
             correct_text='line 1\nline 1\nline 2'
            ),
        Test("Copy last line",
             initial_text='line 1\nline 2',
             initial_selection=cursor(8),
             command='copy',
             correct_clipboard='line 2\n',
            ),
        Test("Cut last line",
             initial_text='line 1\nline 2',
             initial_selection=cursor(8),
             command='cut',
             correct_clipboard='line 2\n',
             correct_text='line 1',
             correct_selection=cursor(1)
            ),
        Test("Paste last line",
             initial_text='line 1\nline 2',
             initial_selection=cursor(8),
             initial_clipboard='line 3\n',
             command='paste',
             correct_text='line 1\nline 2\nline 3'
            ),
        Test("Duplicate last line",
             initial_text='line 1\nline 2',
             initial_selection=cursor(8),
             command='duplicate',
             correct_text='line 1\nline 2\nline 2'
            ),
        Test("Paste word on last line",
             initial_text='line 1\nline 2',
             initial_selection=cursor(13),
             initial_clipboard='word',
             command='paste',
             correct_text='line 1\nline 2word',
             correct_selection=cursor(17)
            ),
        Test("Right-to-left selection copy",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=region(9, 1),
             command='copy',
             correct_clipboard='line 1\nline 2\n'
            ),
        Test("Right-to-left selection cut",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=region(9, 1),
             command='cut',
             correct_text='line 3',
             correct_clipboard='line 1\nline 2\n',
             correct_selection=cursor(1)
            ),
        Test("Right-to-left selection paste",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=region(9, 1),
             initial_clipboard='line 4\n',
             command='paste',
             correct_text='line 4\nline 3',
             correct_selection=cursor(1)
            ),
        Test("Right-to-left selection duplicate",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=region(9, 1),
             command='duplicate',
             correct_text='line 1\nline 2\nline 1\nline 2\nline 3'
            ),
        Test("Indented copy",
             initial_text='line 1\n\tline 2\nline 3',
             initial_selection=cursor(8),
             command='copy',
             correct_clipboard='\tline 2\n'
            ),
        Test("Cut with trailing newline 1",
             initial_text='line 1\nline 2\n',
             initial_selection=cursor(8),
             command='cut',
             correct_clipboard='line 2\n',
             correct_text='line 1\n',
             correct_selection=Test.ANY # Don't check - either 1 or 7 is acceptable.
            ),
        Test("Cut with trailing newline 2",
             initial_text='line 1\nline 2\n',
             initial_selection=cursor(14),
             command='cut',
             correct_clipboard='\n',
             correct_text='line 1\nline 2',
             correct_selection=cursor(7)
            ),
        Test("Paste with trailing newline 1",
             initial_text='line 1\nline 2\n',
             initial_selection=cursor(8),
             initial_clipboard='line 3\n',
             command='paste',
             correct_text='line 1\nline 2\nline 3\n'
            ),
        Test("Paste with trailing newline 2",
             initial_text='line 1\nline 2\n',
             initial_selection=cursor(14),
             initial_clipboard='line 3\n',
             command='paste',
             correct_text='line 1\nline 2\n\nline 3'
            ),
        Test("Paste with trailing newline 3",
             initial_text='line 1\nline 2\n',
             initial_selection=cursor(14),
             initial_clipboard='word',
             command='paste',
             correct_text='line 1\nline 2\nword',
             correct_selection=cursor(18)
            ),
        Test("Duplicate with trailing newline 1",
             initial_text='line 1\nline 2\n',
             initial_selection=cursor(8),
             command='duplicate',
             correct_text='line 1\nline 2\nline 2\n'
            ),
        Test("Duplicate with trailing newline 2",
             initial_text='line 1\nline 2\n',
             initial_selection=cursor(14),
             command='duplicate',
             correct_text='line 1\nline 2\n\n'
            ),
        Test("Multiple selection copy 1",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=cursor(1) + cursor(8),
             command='copy',
             correct_clipboard='line 1\nline 2\n'
            ),
        Test("Multiple selection copy 2",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=region(1, 3) + region(8, 9),
             command='copy',
             correct_clipboard='line 1\nline 2\n'
            ),
        Test("Multiple selection cut 1",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=cursor(1) + cursor(8),
             command='cut',
             correct_clipboard='line 1\nline 2\n',
             correct_text='line 3',
             correct_selection=Test.ANY
            ),
        Test("Multiple selection cut 2",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=region(1, 3) + region(8, 9),
             command='cut',
             correct_clipboard='line 1\nline 2\n',
             correct_text='line 3',
             correct_selection=Test.ANY
            ),
        Test("Multiple selection duplicate 1",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=cursor(1) + cursor(8),
             command='duplicate',
             correct_text='line 1\nline 1\nline 2\nline 2\nline 3',
             correct_selection=cursor(1) + cursor(15)
            ),
        Test("Multiple selection duplicate 2",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=region(1, 3) + region(8, 9),
             command='duplicate',
             correct_text='line 1\nline 1\nline 2\nline 2\nline 3',
             correct_selection=region(1, 3) + region(15, 16)
            ),
        Test("Overlapping selections copy 1",
             # Multiple cursors on the same line, but only copy it once.
             initial_text='line 1\nline 2',
             initial_selection=cursor(1) + cursor(3),
             command='copy',
             correct_clipboard='line 1\n'
            ),
        Test("Overlapping selections copy 2",
             # Parts of two selections on line 2. But don't copy it twice.
             initial_text='line 1\nline 2\nline 3\nline 4',
             initial_selection=region(1, 8) + region(12, 15),
             command='copy',
             correct_clipboard='line 1\nline 2\nline 3\n'
            ),
        Test("Overlapping selections cut 1",
             # Multiple cursors on the same line, but only cut it once.
             initial_text='line 1\nline 2',
             initial_selection=cursor(1) + cursor(3),
             command='cut',
             correct_text='line 2',
             correct_clipboard='line 1\n'
            ),
        Test("Overlapping selections cut 2",
             # Parts of two selections on line 2. But don't cut it twice.
             initial_text='line 1\nline 2\nline 3\nline 4',
             initial_selection=region(1, 8) + region(12, 16),
             command='cut',
             correct_text='line 4',
             correct_clipboard='line 1\nline 2\nline 3\n',
             correct_selection=cursor(1) + cursor(2)
            ),
        Test("Overlapping selections paste 1",
             # Multiple cursors on the same line, but only paste below it once.
             initial_text='line 1\nline 2',
             initial_selection=cursor(1) + cursor(3),
             initial_clipboard='line 3\n',
             command='paste',
             correct_text='line 1\nline 3\nline 2'
            ),
        Test("Overlapping selections paste 2",
             # Parts of two selections on line 2. But don't paste twice.
             initial_text='line 1\nline 2\nline 3\nline 4',
             initial_selection=region(1, 8) + region(12, 16),
             initial_clipboard='line 5\n',
             command='paste',
             correct_text='line 5\nline 4',
             correct_selection=cursor(1) + cursor(2)
            ),
        Test("Overlapping selections duplicate 1",
             # Multiple cursors on the same line, but only duplicate it once.
             initial_text='line 1\nline 2',
             initial_selection=cursor(1) + cursor(3),
             command='duplicate',
             correct_text='line 1\nline 1\nline 2'
            ),
        Test("Overlapping selections duplicate 2",
             # Parts of two selections on line 2. But don't duplicate twice.
             initial_text='line 1\nline 2\nline 3\nline 4',
             initial_selection=region(1, 8) + region(12, 15),
             command='duplicate',
             correct_text='line 1\nline 2\nline 3\nline 1\nline 2\nline 3\nline 4'
            ),
        Test("Paste overwrite word",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=region(7, 11),
             initial_clipboard='word',
             command='paste',
             correct_text='line 1\nword 2\nline 3',
             correct_selection=cursor(11)
            ),
        Test("Paste multiple words 1",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=cursor(5) + cursor(12),
             initial_clipboard='word',
             command='paste',
             correct_text='line word1\nline word2\nline 3',
             correct_selection=cursor(9) + cursor(20)
            ),
        Test("Paste multiple words 2",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=region(0, 5) + region(7, 12),
             initial_clipboard='word',
             command='paste',
             correct_text='word1\nword2\nline 3',
             correct_selection=cursor(4) + cursor(10)
            ),
        Test("Paste multiple lines",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=cursor(1) + cursor(16),
             initial_clipboard='clip-line\n',
             command='paste',
             correct_text='line 1\nclip-line\nline 2\nline 3\nclip-line',
             correct_selection=cursor(1) + cursor(26)
            ),
        Test("Paste overwrite lines 1",
             initial_text='line 1\nline 2\nline 3',
             initial_selection=region(8, 17),
             initial_clipboard='line 4\n',
             command='paste',
             correct_text='line 1\nline 4',
             correct_selection=cursor(10)
            ),
        Test("Paste overwrite lines 2",
             initial_text='line 1\nline 2\nlong line 3\nline 4',
             initial_selection=region(8, 24),
             initial_clipboard='clip\n',
             command='paste',
             correct_text='line 1\nclip\nline 4',
             correct_selection=cursor(13)
            ),
        Test("Paste overwrite lines 3",
             initial_text='line 1\nline 2\nline 3\nline 4\nline 5',
             initial_selection=region(1, 9) + region(29, 25),
             initial_clipboard='clipboard\n',
             command='paste',
             correct_text='clipboard\nline 3\nclipboard',
             correct_selection=cursor(2) + cursor(21)
            ),
        Test("Paste over blank first line",
             # Special case: Blank first line should be overwritten instead of
             # pasting below it.
             initial_text='\nline 2',
             initial_selection=cursor(0),
             initial_clipboard='clip-line\n',
             command='paste',
             correct_text='clip-line\nline 2'
            ),
    ]
