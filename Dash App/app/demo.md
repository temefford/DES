## What does the app do?

This app allows you to simulate a Teleradiology network in which medical images of various types are created and distributed to the radiologists in the network that are best able to process them. We have defined three tiers of medical image urgencies: 
1 - very urgent 
2 - urgent 
3 - not urgent.
For each of the three types of image, you can define several parameters:

Simulation Duration - This value defines the amount of time that medical images will be created and put into the system for.

Number of Radiologists - How many radiologists are created to process the medical images. Each radiologist has their own queue that hold's the medical images waiting to be analyzed.

Time Between Images - Images will be created at random intervals sampled from a Poisson distribution with mean defined by this interval. A smaller value means images arrive faster and create more burden on the system.

Average Process Time - Each image type will take a certain amount of time (also random sampling around distribution with here-defined mean) once it is seen by a radiologist. This time does not start until the image has been seen by a radiologist. Once a radiologist begins analyzing an image, any other copies of the image in the network are removed from the other radiologists queues.

Target Time - This value defines how much time is allotted for each image type to be processed (since time of creation). If not processed by this time, It is considered a "failed job."

Fraction of specialist radiologists - In addition to an "urgency value", each medical image is given a particular "type" out of 5 and can only be seen by radiologists who can handle that type. At the definition of the radiologists, they are randomly assigned m choose n types of images that they can process. Increasing this fraction gives more radiologists more specialities so they are able to handle a larger fraction of the images.

Cutoff Time - In the case of an overburdened system, the radiologists will be backlogged long after the Simulation Duration. This cutoff ends the simulation at a defined multiple of the Simulation Duration.

## Getting Started with the Demo

Some place-holder values have been inserted so just click "Run Simulation" to get started! Then you can explore tuning the different parameters.





