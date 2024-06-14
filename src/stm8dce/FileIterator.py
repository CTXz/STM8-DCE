############################################
# Classes
############################################


class FileIterator:
    """
    Class to iterate over lines in a file.

    Attributes:
        path (str): The path of the file.
        index (int): The current line number.
    """

    def __init__(self, file_obj):
        """
        Initializes the FileIterator with the given file object.

        Args:
            file_obj (file): The file object to iterate over.
        """
        self.path = file_obj.name
        self.iterable = file_obj.readlines()
        self.index = 0

    def __iter__(self):
        return self

    def next(self):
        """
        Returns the next line in the file.

        Returns:
            str: The next line in the file.

        Raises:
            StopIteration: If the end of the file is reached.
        """
        if self.index < len(self.iterable):
            ret_line = self.iterable[self.index]
            self.index += 1
            return ret_line
        else:
            raise StopIteration

    def prev(self):
        """
        Moves back one line in the file.

        Returns:
            str: The previous line in the file.

        Raises:
            StopIteration: If the beginning of the file is reached.
        """
        if self.index > 0:
            self.index -= 1
            return self.iterable[self.index]
        else:
            raise StopIteration
