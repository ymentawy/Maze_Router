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
    It is built as a class that has variables which are the dimensions, nets with their pins, obstacles and penalties. Finally with the routing algoirthm.

#

Rana Sherif:

    Parser functions, which reads from a file and parses through the text file to get the values ready.

#

Ali Elkhouly:

    Joining the codes together and finalizing the code. Writing the Readme.md and finally writing the test cases.

#

## Test Cases

brief description of each test case.

### Test 1

Test case given in the handout example to make sure we can run the basics.

#

### Test 2

Landing some obstacles in the fastest route in net 1 to check if it goes around it correctly or not.

#

### Test 3

Adding an obstacle in the place of a pin to check if it's gonna ignore it or not. As two things cannot exist at the same place. It just makes the pin inaccessible since obstacles are loaded first (AKA we cannot put a pin there)

#

### Test 4

Not putting any obstacles to check if it would break the code, also checking if it would go the correct route by adding a cell at the same coordinates but different metal layer.
