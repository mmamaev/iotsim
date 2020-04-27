

# iotsim - Simulator of (I)IoT telemetry

---------------------------------------

**iotsim** simulates telemetry data as they would arrive from some system's sensors and control devices.

## Contents of the repo

### Libraries

- **iotsim** - main package; use it do generate data
- **iotsim.runtime** - utils and helpers for simulation running

### Scripts

- **show_assembly_data.ipynb** - jupyter notebook that collects and shows data from a simulator.

- **run_assembly.py** - runs a simulator in the real time.


## Data Model

*Assembly* is a collection of (possibly interdependent) signals.
Each *signal* represents a measured feature (such as temperature or pressure) or a system's control as they unfold in time.

The time is modeled as a succession of ticks. Assembly provides a runner; every call on the runner advances the time by one tick.
Assembly's parameter `tick` specifies the duration of one tick in seconds (default 1). This is used if you need to generate timestamps or run the assembly in the real time.

On every tick each signal produces two kinds of output:

- *truth* is the true signal's value at this moment of time.
- *reading* is the signal's value as it is seen when delivered to an external observer.

The rationale behind *reading* is that, in real life, we are never able to observe a signal directly and immediately.
There may be inaccurate and noisy sensors that sample the signal at some intervals. The output from the sensors is likely to be transmitted through a network that adds a delay and even loses some data due to congestion and outages.

In **iotsim** assembly, *reader* and *network* are the components used to transform ground the truth into readings. Each signal may be assigned its own *reader* and *network*.

*Reader* transforms the *truth*'s value.
For example, **EveryNth** reader emits the output only every n-th tick by taking the *truth* at that tick and adding some noise to it; at the other ticks the signal is not observable with this reader.
**OnChange** reader emits the output only when the true value changes (and optionally every n-th tick after the last change); it can also add noise.

*Network* determines when the output produced by the *reader* is delivered to the observer. For example, **Normal** network drops some percentage of *reader*'s outputs and adds a variable delay to the arrival time of those that survive.

By default, a signal is assigned **PassThrough** reader and **Ideal** network. This arrangement represent a perfect world where the true value is observable at every tick, immediately and without distortions.


Usage
============

The package comes with a number of pre-cooked assemblies, such as:

- **Flatline** - produces one signal with a constant true value.

- **SimpleActuator** - produces two signals: `control` and `sensor`. `Control` pulses between 0 and 1. When `control` is on (==1), `sensor`'s value rises linearly; when `control` is off (==0), `sensor`'s value drops linearly until it reaches the initial level and then stays there.

Their parameters are read from **assembly.yml** file (see examples in the file).

Use notebook **show_assembly_data.ipynb** to collect and plot data from an assembly. Data is collected as fast as the computer runs (tick's duration is not respected).

To carry out the simulation in real time, run

``python run_assembly.py -t 20 assembly.yml``


In the default configuration of the script, both *readings* and *truths* are printed to the standard output in JSON format, *truths* - at their tick time, *readings* -  at their arrival time. The special `meta` key shows what is printed.

The ``-t`` command line argument specifies the number of ticks to run; omit it or use ``-t 0`` to run the script indefinitely.


## Disclaimer

This is unreleased ongoing development. There is low test coverage and almost no docs.


## License

`BSD 3 Clause <LICENSE.txt>`_
