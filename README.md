# Maze_Router

<p align= "center" >
<font size ="6">CSCE3304</font>
</p>
<p align= "center" >
<font size ="4"><b>Digital Design II<b></font>
</p>
<p align= "center" >
<font size ="3">Dr. Mohamed Shalan</font>
</p>
<p align= "center" >
<font size ="3">By Youssef Mentawy, Rana Sherif, Ali Elkhouly</font>
</p>

# Aim of the Project

This project focuses on building a maze router for layout synthesis. It is built for efficient routing using Lee's Algorithm.

## Work Divided as follows

Youssef Mentawy:

    Built the maze router, which uses Lee's algorithm
    It is built as a class that has variables which are the dimensions, nets with their pins, obstacles and penalties. Finally with the routing algoirthm. Worked on the drawing and mapping algorithm.

#

Rana Sherif:

    Parser functions, which reads from a file and parses through the text file to get the values ready. Worked on the algorithm of mapping and drawing.

#

Ali Elkhouly:

    Joining the codes together and finalizing the code. Writing the Readme.md and finally writing the test cases. Debugging the code and fixing the priority hierchy.

#

## How to use?

    When you run the code, it prompts you to add the name of the file to test. Just write it and it will produce a text file with the output in the format of a single line per net. After that, it produces a plot to visualize the plotting.

#

## Implementation

The user inputs the name of the file, then the program reads the file and parses it into the class Lee Router using REGEX. We first received the grid size followed by the cost of changing direction and using a via.

As obstacles are first in the file, we give them priority and add them to the grid. Then, we place the pins (we avoid any pin colliding with an obstacle)

We start by plotting the wires with priority based on the number of pins (the less pins, the higher the priority). In case of two equal number of pins in two nets, we then use the Manhattan Distance case. If both are equal, then we use the FCFS approach.

We then use the Lee Routing algorithm to find the shortest path between the pins in the 2D grid. It moves in 4 directions searching for the fastest way to the next pin.

#

## Challenges

#

- Finding bugs and fixing them
- - Finding bugs and things that would break our code was a bit of a challenge.
- - Not to mention, thinking of solutions and fixing them was also difficult.

- Corner Cases
- - Checking every corner case that came to mind and fixing them was a hassle.

- Time Constraint
- - Other courses' demands and projects limited the production with this project.

## Visualization plan

Display the grid as a 2D grid
Obstacles should be highlighted with unique color
show routed paths using lines and arrows and conection for each net
use colors for different features such paths and pins
tools suggested: Matplotlib, library called tinker on python, imshow, scatter
each cell will hold 0,1,2,3 representing empty space, obstacle, path, start/end points of a net
chech obstacle list mark obstacle to 1
initially mark pins to 3 if a path exists change to 2
