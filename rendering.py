"""
rendering.py

My humble attempt at creating a graphics engine from scratch
"""
import ctypes
import math
from typing import Union


# load in C code for creating a window and drawing on it
window_lib : ctypes.CDLL = ctypes.CDLL('./dlls/window.dll')
window_lib.create_window.argtypes = [ctypes.POINTER(ctypes.c_char), ctypes.POINTER(ctypes.c_int)]
window_lib.get_hwnd.argtypes = [ctypes.POINTER(ctypes.c_char)]
window_lib.draw_pixel.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
window_lib.fill_rect.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]

# ctype for creating the dimensions of the window
DimensionsArray = ctypes.c_int * 2

class CustomError(Exception):
    """Base class for custom exceptions
    """
    pass


class NoValidHandle(CustomError):
    """Exception raised when a window handle couldn't be found
    """
    pass


class Window:
    """A window created in C that allows for drawing
    """
    def __init__(self, title : str, dimensions : Union[list, tuple]) -> None:
        """Initialize the window

        :param title: The title of the window
        :type title: str
        :param dimensions: The dimensions of the window
        :type dimensions: Union[list, tuple]
        :raises NoValidHandle: If a valid window handle couldn't be found
        """
        # convert the window title to a char array
        name_array = (ctypes.c_char * len(title))(*title.encode('utf-8'))
        window_lib.create_window(name_array, DimensionsArray(dimensions[0], dimensions[1]))
        self.title : str = title
        self.hwnd = window_lib.get_hwnd(name_array)
        if self.hwnd == 0:
            raise NoValidHandle('No valid window handle could be found')

    def draw(self, coord : 'Coordinate', color : 'Color') -> None:
        """Color the pixel at the given coordinate with the given color

        :param coord: The coordinate to be colored
        :type coord: Coordinate
        :param color: The color of the pixel in rgb(a)
        :type color: Color
        """
        window_lib.draw_pixel(self.hwnd, coord.x, coord.y, color.colorref)

    def mainloop(self) -> None:
        """Loop to run the window's message loop in C
        """
        # start the message loop
        window_lib.message_loop()


class Color:
    """A color that is rgba compatible and can be used as a COLORREF object in C
    """
    def __init__(self, color : Union[tuple, list]) -> None:
        """Initialize the color

        :param color: A tuple containing rgb(a) values
        :type color: Union[tuple, list]
        :raises ValueError: If too many arguments are passed in the color parameter
        :raises ValueError: If the rgb(a) values are too large or too small
        """
        # not the right amount of values
        if len(color) != 4 and len(color) != 3:
            raise ValueError('color must be a rgb/rgba color value')
        # values are not in correct range
        if color[0] > 255 or color[0] < 0 or color[1] > 255 or color[1] < 0 or color[2] > 255 or color[2] < 0:
            raise ValueError('r, g, b, and a values must be between 0 and 255')
        # check for alpha value as well
        elif len(color) == 4:
            if color[3] > 255 or color[3] < 0:
                raise ValueError('r, g, b, and a values must be between 0 and 255')
        
        # set values
        if len(color) == 4:
            self.r : int = color[0]
            self.g : int = color[1]
            self.b : int = color[2]
            self.a : int = color[3]
            self.color : Color = color
            self.colorref : ctypes.c_uint32 = self.generate_colorref(self.r, self.g, self.b)
        else:
            self.r : int = color[0]
            self.g : int = color[1]
            self.b : int = color[2]
            self.color : Color = color
            self.colorref : ctypes.c_uint32 = self.generate_colorref(self.r, self.g, self.b)

    @classmethod
    # create the class from a hex code instead
    def from_hex_code(cls, hex_code : str) -> 'Color':
        """Initialize the color from a hex code

        :param hex_code: The color's hex code
        :type hex_code: str
        :raises ValueError: If the length of the hex code doesn't represent a rgb(a) color
        :raises ValueError: If the hex code has incompatible characters
        """
        if len(hex_code) != 8 and len(hex_code) != 6:
            raise ValueError('hex_code must be a rgb/rgba hex code')
        for char in hex_code:
            if char.upper() not in set('0123456789ABCDEF'):
                raise ValueError('Incompatible character(s) in hex_code')
        
        if len(hex_code) == 8:
            r : int = int(hex_code[:2], 16)
            g : int = int(hex_code[2:4], 16)
            b : int = int(hex_code[4:6], 16)
            a : int = int(hex_code[-2:], 16)

            return cls((r, g, b, a))
        else:
            r : int = int(hex_code[:2], 16)
            g : int = int(hex_code[2:4], 16)
            b : int = int(hex_code[-2:], 16)

            return cls((r, g, b))
    
    def generate_colorref(self, r : int, g : int, b : int, a : int = None) -> ctypes.c_uint32:
        """Generate the COLORREF C object for the color

        :param r: The r value of the color
        :type r: int
        :param g: The g value of the color
        :type g: int
        :param b: The b value of the color
        :type b: int
        :param a: The a value of the color, defaults to None
        :type a: int, optional
        :return: A hexadecimal representation of the color
        :rtype: ctypes.c_uint32
        """
        # return an unsigned integer using some bit shifting
        return ctypes.c_uint32((b << 16) | (g << 8) | r)

    def __str__(self) -> str:
        """Converts color to readable format to be printed

        :return: A readable format of the color
        :rtype: str
        """
        return f'Color({self.color})'

class Coordinate:
    """A representation of a coordinate in 2D space
    """
    def __init__(self, x : float, y : float) -> None:
        """Initialize the coordinate

        :param x: The x-coordinate of the coordinate
        :type x: float
        :param y: The y-coordinate of the coordinate
        :type y: float
        :raises ValueError: If x or y isn't positive
        """
        if x < 0 or y < 0:
            raise ValueError('x and y must be positive')
        
        self.x : float = x
        self.y : float = y
    
    def distance(self, other : 'Coordinate') -> float:
        """Find the distance between this coordinate and another coordinate

        :param other: The coordinate to find the distance from
        :type other: Coordinate
        :return: The distance between the two coordinates
        :rtype: float
        """
        return math.sqrt((other.x - self.x) ** 2 + (other.y - self.y) ** 2)

    def __str__(self) -> str:
        """Converts coordinate to readable format to be printed

        :return: A readable format of the coordinate
        :rtype: str
        """
        return f'Coordinate({self.x}, {self.y})'


class Line:
    """A line that can be drawn on a window with antialiasing capabilities
    """
    def __init__(self, master : Window, start : Coordinate, end : Coordinate, color : Color = Color((0, 0, 0)), width : int = 1, antialias : bool = False) -> None:
        """Initialize the line

        :param master: The master window of the line
        :type master: Window
        :param start: The start coordinate of the line
        :type start: Coordinate
        :param end: The end coordinate of the line
        :type end: Coordinate
        :param color: The color of the line, defaults to Color((0, 0, 0))
        :type color: Color, optional
        :param width: The width (in pixels) of the line, defaults to 1
        :type width: int, optional
        :param antialias: Whether or not the line should be antialiased, defaults to False
        :type antialias: bool, optional
        :raises ValueError: If width is not a positive integer
        """
        if width <= 0 or not isinstance(width, int):
            raise ValueError('width must be a positive integer')
        
        self.master : Window = master
        self.start : Coordinate = start
        self.end : Coordinate = end
        self.color : Color = color
        self.width : int = width
        self.radius : int = width // 2
        try:
            self.slope : float = (self.end.y - self.start.y) / (self.end.x - self.start.x)
        except ZeroDivisionError:
            self.slope : float = None

    def display(self) -> None:
        """Draw the line on it's master
        """
        # check to see if the line is vertical or horizontal
        if self.slope != 0 and self.slope is not None:
            # bresenham's line algorithm
            # first find all the coordinates
            dx = abs(self.start.x - self.end.x)
            dy = abs(self.start.y - self.end.y)
            step_x = 1 if self.start.x < self.end.x else -1
            step_y = 1 if self.start.y < self.end.y else -1
            error = dx - dy
            two_error = 2 * error
            coords : list = []
            # no need to check for slope = None because that's already checked for
            x = self.start.x
            y = self.start.y
            while True:
                for offset in range(-self.radius, self.radius + 1):
                    # whichever integer value of y is close is the one we fill in
                    y : int = round(self.slope * (x - self.start.x) + self.start.y)
                    if self.slope > 1:
                        # if line is more vertical thicken in x direction
                        coords.append(Coordinate(x + offset, y))
                    else: 
                        # otherwise thicken in the y direction
                        coords.append(Coordinate(x, y + offset))
                
                if x == self.end.x and y == self.end.y:
                    break

                if two_error > -dy:
                    error -= dy
                    x += step_x

                if two_error < dx:
                    error += dx
                    y += step_y


            # draw all the coordinates
            for coord in coords:
                self.master.draw(coord, self.color)
        # if it is just draw a rectangle instead
        else:
            # vertical
            if self.slope is None:
                #print('vertical')
                window_lib.fill_rect(self.master.hwnd, self.start.x, self.start.y, self.width, self.end.y - self.start.y, self.color.colorref)
            # horizontal
            else:
                #print('horizontal')
                window_lib.fill_rect(self.master.hwnd, self.start.x, self.start.y, self.end.x - self.start.x, self.width, self.color.colorref)


    def __str__(self) -> str:
        """Converts the line to a readable format

        :return: A readable format of the line
        :rtype: str
        """
        return f'Line({self.start}, {self.end})'


class Rect:
    """A rectangle that can be drawn on a window with antialiasing capabilities
    """
    def __init__(self, master: Window, top_left_corner : Coordinate, width : int, height : int, border_color : Color = Color((0, 0, 0)), borderwidth : int = 1, antialiasing : bool = False, fill : bool = False, fill_color : Color = Color((0, 0, 0))) -> None:
        """Initialize the rectangle

        :param master: The master window of the rectangle
        :type master: Window
        :param top_left_corner: The top left corner of the rectangle
        :type top_left_corner: Coordinate
        :param width: The width of the rectangle
        :type width: int
        :param height: The height of the rectangle
        :type height: int
        :param border_color: The border color of the rectangle, defaults to Color((0, 0, 0))
        :type border_color: Color, optional
        :param borderwidth: The width of the rectangles border, defaults to 1
        :type borderwidth: int, optional
        :param antialiasing: Whether or not the rectangle's edges should be antialiased, defaults to False
        :type antialiasing: bool, optional
        :param fill: Whether or not the rectangle is filled, defaults to False
        :type fill: bool, optional
        :param fill_color: Fill color of the rectangle, defaults to Color((0, 0, 0))
        :type fill_color: Color, optional
        :raises ValueError: If width is not a positive integer
        :raises ValueError: If height is not a positive integer
        :raises ValueError: If borderwidth is not a positive integer
        """
        if width <= 0 or not isinstance(width, int):
            raise ValueError('width must be a postiive integer')
        
        if height <= 0 or not isinstance(height, int):
            raise ValueError('height must be a positive integer')
        
        if borderwidth <= 0 or not isinstance(borderwidth, int):
            raise ValueError('borderwidth must be a positive integer')
        
        self.master : Window = master
        self.width : int = width
        self.height : int = height
        self.border_color : Color = border_color
        self.borderwidth : int = borderwidth
        self.antialiasing : bool = antialiasing
        self.fill : bool = fill
        self.fill_color : Color = fill_color

        # define 4 vertices
        self.top_left : Coordinate = top_left_corner
        self.top_right : Coordinate = Coordinate(top_left_corner.x + width, top_left_corner.y)
        self.bottom_left : Coordinate = Coordinate(top_left_corner.x, top_left_corner.y + height)
        self.bottom_right : Coordinate = Coordinate(top_left_corner.x + width, top_left_corner.y + height)

        # define 4 edges
        self.top_edge : Line = Line(self.master, self.top_left, self.top_right, self.border_color, self.borderwidth, self.antialiasing)
        self.bottom_edge : Line = Line(self.master, self.bottom_left, self.bottom_right, self.border_color, self.borderwidth, self.antialiasing)
        self.left_edge : Line = Line(self.master, self.top_left, self.bottom_left, self.border_color, self.borderwidth, self.antialiasing)
        self.right_edge : Line = Line(self.master, self.top_right, self.bottom_right, self.border_color, self.borderwidth, self.antialiasing)

    def display(self) -> None:
        """Display the rectangle on its master window
        """
        # draw edges
        self.top_edge.display()
        self.bottom_edge.display()
        self.left_edge.display()
        self.right_edge.display()

        # fill in bottom right corner
        window_lib.fill_rect(self.master.hwnd, self.bottom_right.x, self.bottom_right.y, self.borderwidth, self.borderwidth, self.border_color.colorref)

        # fill if needed
        if self.fill:
            window_lib.fill_rect(self.master.hwnd, self.top_left.x + self.borderwidth, self.top_left.y + self.borderwidth, self.width - self.borderwidth, self.height - self.borderwidth, self.fill_color.colorref)

    def change_fill(self) -> None:
        self.fill = not self.fill

    def __str__(self) -> str:
        """Converts the rectangle to a readable format

        :return: A readable format of the rectangle
        :rtype: str
        """
        return f'Rect({self.top_left}, {self.width}, {self.height})'
