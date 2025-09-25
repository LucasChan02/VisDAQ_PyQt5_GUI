# VisDAQ_PyQt5_GUI

## Dependencies 

* Python 3.9
* numpy
* opencv-python
* PyQt5 
* PyQt6-tools 6.4.2.3.3 (Migrating)
* PySerial
* matplotlib

This is a screenshot of how this multithreaded GUI looks. You can control motion of two stepper motors with this software. Two force sensors and one camera are also connected to the PC and this software can be used for data acquisition with multiple threads. Force sensors used are mentioned below.

* [Mark 10 force gauge](https://mark-10.com/products/force-gauges/series-5/)  

    Force gauge is connected to PC with DB9 connector for RS232 serial protocol. Refer to mark10_force_reader.py file, for understanding of getting data from this force gauge. (WIP)
    
* [Forsentek load cell with indicator](https://www.forsentek.com/)  

    Load cell is connected to load cell indicator (both can be bought from the mentioned website). Load cell indicator is connected to PC with DB9 connector for RS232 serial protocol. Refer to forsentek_force_reader.py file, for more understanding. (Not being maintained)

![UI Screenshot](https://github.com/SaumilShah66/PyQt5-GUI-for-force-reading-and-plotting/blob/master/images/parameter.PNG)

As soon as you start the testing, forces will be plotted in blank window. 
