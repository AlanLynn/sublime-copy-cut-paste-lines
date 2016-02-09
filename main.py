"""Replacements for clipboard commands that prefer to operate on full lines of code.

Replaces: Copy, Cut, Paste, and Duplicate Lines
Note: For selections within a single line, commands work as normal, operating
      only on the selection and not on the full line.
"""

import sublime, sublime_plugin


class ExpandedRegion(sublime.Region):
    """Adds original_regions - the regions that were expanded into this."""
    def __init__(self, region, original_region=None):
        self.a = region.a
        self.b = region.b
        self.xpos = region.xpos
        self.original_regions = []
        if original_region != None:
            self.original_regions.append(original_region)


def get_expanded_selection(view):
    """Returns the selection expanded to full lines.

    Returns a list of ExpandedRegion.
    """
    if len(view.sel()) == 0:
        # Null selection
        return []
    expanded_selection = []
    previous_expanded_region_end = -1
    # Expand all regions to the full lines containing them.
    for region in view.sel():
        expanded_region = ExpandedRegion(view.full_line(region), region)
        if expanded_region.begin() < previous_expanded_region_end:
            # Merge overlapping selections.
            new_region = expanded_selection[-1].cover(expanded_region)
            # Don't use new_region directly or we'll lose original_regions.
            expanded_selection[-1].a = new_region.a
            expanded_selection[-1].b = new_region.b
            # Append another original region.
            expanded_selection[-1].original_regions.append(region)
        else:
            expanded_selection.append(expanded_region)
        previous_expanded_region_end = expanded_region.end()
    return expanded_selection


def copy_selection_lines(selection, view):
    """Copies the selection to the clipboard.

    The selection is assumed to be full lines.
    """
    if len(selection) == 0:
        return
    clipboard_string = ''
    for region in selection:
        clipboard_string += view.substr(region)
    # If missing, add a trailing \n, because these are line selections.
    if clipboard_string == '' or clipboard_string[-1] != '\n':
        clipboard_string += '\n'
    sublime.set_clipboard(clipboard_string)


def is_selection_within_a_line(view):
    """Returns true if the selection is within single line, but not zero-width."""
    selection = view.sel()
    if len(selection) == 0:
        # Null selection
        return False
    # selection_coverage will be the region that covers all selections.
    selection_coverage = selection[0]
    all_cursors = True # Whether the selections consists entirely of cursors
    for region in selection:
        # Expand selection_coverage to include this region.
        selection_coverage = selection_coverage.cover(region)
        all_cursors = all_cursors and region.empty()
    selection_within_one_line = (len(view.lines(selection_coverage)) == 1)
    return selection_within_one_line and not all_cursors


def is_single_cursor_selection(view):
    """Returns true if the selection is only a single cursor."""
    selection = view.sel()
    return len(selection) == 1 and selection[0].empty()


def get_point(view, row, column):
    """Returns the point that corresponds to (row, column).

    Same as view.text_point(row, column) except if column goes past the end
    of the line, it returns the end of the line instead.
    """
    row_start = view.text_point(row, 0)
    line_length = len(view.line(row_start))
    return row_start + min(column, line_length)


def append_text(view, edit, string):
    """Appends text to the end of the buffer.

    If there is a cursor is at the end of the buffer, it will be left at its
    original point instead of being moved to the new end of the buffer.
    """
    old_end_region = sublime.Region(view.size(), view.size())
    view.insert(edit, view.size(), string)
    new_end_region = sublime.Region(view.size(), view.size())
    if view.sel().contains(new_end_region):
        view.sel().subtract(new_end_region)
        view.sel().add(old_end_region)


def insert_without_moving_cursor(view, edit, point, string):
    """If inserting at the end of the buffer, does not move any cursors there."""
    if point == view.size():
        append_text(view, edit, string)
    else:
        view.insert(edit, point, string)


class CcplCopyCommand(sublime_plugin.TextCommand):
    """Copies all lines containing a selection.

    Exception: Does a normal copy for a selection within a single line.
    Behavior:
    -Lines put into the clipboard will always end in \n.
    -Lines containing multiple selections are only copied once.
    """

    def description(self):
        return "Copy Lines"

    def run(self, edit):
        view = self.view

        # Do a regular copy if the selection is within a single line.
        if is_selection_within_a_line(view):
            view.run_command('copy')
            return

        expanded_selection = get_expanded_selection(view)
        copy_selection_lines(expanded_selection, view)


class CcplCutCommand(sublime_plugin.TextCommand):
    """Cuts all lines containing a selection.

    Exception: Does a normal cut for a selection within a single line.

    Behavior:
    -Clipboard is set the same as in CcplCopy.
    -Cursors are left in their original positions if possible. This may result
     in multiple cursors within a line.
    """

    def description(self):
        return "Cut Lines"

    def run(self, edit):
        view = self.view

        # Do a regular cut if the selection is within a single line.
        if is_selection_within_a_line(view):
            view.run_command('cut')
            return

        # Add a trailing newline to make things easier. It will be removed later.
        append_text(view, edit, '\n')

        # 1. Copy the lines.
        expanded_selection = get_expanded_selection(view)
        copy_selection_lines(expanded_selection, view)

        # 2. Erase the lines.
        # Work backwards to avoid altering other selections.
        for erase_region in reversed(expanded_selection):
            # Clear the old selections.
            view.sel().subtract(erase_region)
            # Add cursors back in.
            # The target row is the row below the selection.
            target_row = view.rowcol(erase_region.end())[0]
            # If there is no line below, use the line above instead.
            if erase_region.end() == view.size():
                target_row = view.rowcol(erase_region.begin())[0] - 1
            for selection_region in erase_region.original_regions:
                # The target column is the column of the selection's cursor.
                target_column = view.rowcol(selection_region.b)[1]
                new_cursor_point = get_point(view, target_row, target_column)
                view.sel().add(sublime.Region(new_cursor_point, new_cursor_point))
            # Erase the cut region.
            view.erase(edit, erase_region)

        # Remove the extra newline that was added earlier.
        view.erase(edit, sublime.Region(view.size() - 1, view.size()))


class CcplPasteCommand(sublime_plugin.TextCommand):
    """Overwrites any lines containing a selection with the clipboard.

    Exception: Does a normal paste if the clipboard does not contain lines of text.
    Behavior:
    -Lines containing a selection are overwritten with the clipboard.
    -Cursor-only selections have the clipboard pasted below them.
    -Paste is done once for each selection.
    """

    def description(self):
        return "Paste Lines"

    def run(self, edit):
        view = self.view
        selection = view.sel()
        clipboard = sublime.get_clipboard()

        # Do a regular paste if the clipboard doesn't contain lines of text.
        if not '\n' in clipboard:
            view.run_command('paste')
            return

        # Add a trailing newline to make things easier. It will be removed later.
        append_text(view, edit, '\n')

        expanded_selection = get_expanded_selection(view)
        # Work backwords to avoid messing up other lines.
        for lines_region in reversed(expanded_selection):
            # Don't overwrite if there are only cursors on this line.
            overwrite = False
            for region in lines_region.original_regions:
                if not region.empty():
                    overwrite = True
                if region.a == 0 and view.substr(sublime.Region(0, 1)) == '\n':
                    # Also overwrite if on a blank first line.
                    overwrite = True
            if overwrite:
                # Remove the selection so it isn't left behind.
                selection.subtract(lines_region)
                # Calculate where to put the remaining cursors.
                new_cursor_points = []
                # The target row is the starting row of the selection.
                target_row = view.rowcol(lines_region.begin())[0]
                for selection_region in lines_region.original_regions:
                    # The target column is the column the selection's cursor is in.
                    target_column = view.rowcol(selection_region.b)[1]
                    new_cursor_point = get_point(view, target_row, target_column)
                    new_cursor_points.append(new_cursor_point)
                # Overwrite with the clipboard.
                view.replace(edit, lines_region, clipboard)
                # Put the remaining cursors back in.
                for new_cursor_point in new_cursor_points:
                    view.sel().add(sublime.Region(new_cursor_point, new_cursor_point))
            else:
                paste_position = lines_region.end()
                insert_without_moving_cursor(view, edit, paste_position, clipboard)

        # Remove the extra newline that was added earlier.
        view.erase(edit, sublime.Region(view.size() - 1, view.size()))


class CcplDuplicateCommand(sublime_plugin.TextCommand):
    """Duplicates all lines containing a selection.

    Exception: Does a normal duplicate for a selection within a single line.
    Behavior:
    -A line with multiple selections is only duplicated once. Otherwise, each
     selection is duplicated independently.
    -Duplicated text is placed below the original.
    """

    def description(self):
        return "Duplicate Lines"

    def run(self, edit):
        view = self.view
        if view.size() == 0:
            return

        # Do a regular duplicate if the selection is within a single line.
        if is_selection_within_a_line(view):
            # Note: The command is named duplicate_line, but it can duplicate
            # text within a line as well.
            view.run_command('duplicate_line')
            return

        # Add a trailing newline to make things easier. It will be removed later.
        append_text(view, edit, '\n')

        expanded_selection = get_expanded_selection(view)
        # Work backwards to avoid altering other selections.
        for region in reversed(expanded_selection):
            text = view.substr(region)
            view.insert(edit, region.end(), text)

        # Remove the extra newline that was added earlier.
        view.erase(edit, sublime.Region(view.size() - 1, view.size()))


