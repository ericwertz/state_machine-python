# state_machine-python
This is a state machine library for building state machines.

# History
It was originally created for MicroPython/RP2040 for the State Machine Lab(s) experiments for the *ME/EE106 Introduction to Mechatronics* course at
San Jose State University.  A (much) less-flexible/configurable implementaion of this library was used in the previous semester.

# The basic structure of (these)state machines
A program implemented as a state machine using this library is comprised of three parts: the main program, one (or theoretically more) *eventer*,
and one or more *eventoids*.  The main program creates an *Eventer*, from which all events are received that cause the state machine transitions.  Event-
generating Eventoids are created (usually) at the start of the main program and registered with the Eventer.  A diagram of how these three pieces are joined
together is shown below:
                                                       +---------->  eventoid #1  (e.g. gpio, alarm, encoder, sensor, etc.)
             register(),next()->             poll()->  |
main_program <-----------------> eventer <-------------+----------> [eventoid #2]
     ^     v                                 <-add()   |        ...
     ^     v                                           +----------> [eventoid #n]
     ^<<<<<< event_process()
     
All of the work to be done in implementing a state-machine-based program is in the state machine design itself, and the code needed to perform the actions
required in all of the transitions from state to state.  Assuming that no custom eventoids need to be created, the only code that needs to be written is in
```event_process()``` (discussed immediately below) and the initializations needed to support ```event_process()``` and the configuration of the required
eventoids.

Eventoids are chosen based on the input event requirements of the system design.  Were you designing a simple flashlight program, you would need only
one eventoid that generates "press" events from the single input button.  If your flashlight is fancier and has the requirement to provide manual dimming,
this could be provided by an analog-reactive eventoid monitoring a potentiometer, a rotary encoder eventoid, or some type of pulse-mapping eventoid using
a second (or even the existing) button.

The main program may subsequently never need to communicate directly with eventoids after creation and registration with the eventer.  In some cases
eventoids may be reconfigurable in-place, for example, changing the period of a recurring timer, but this tends to be the exception rather than the norm.

Because the types of input events are fairly common from system to system but the system's outputs and responses are unbounded, most types of input
behaviors come from a relatively small group of (hopefully) general-purpose and re-usable eventoids. However no support is provided for state-machine
actions (except those of eventoids, like alarm cancellation) or output behaviors.


# How are these three pieces used together?

The main program logically need only contain two parts, a loop that repeatedly calls ```Eventer.next()``` to retrieve the next event (or ```None```
if no event has occurred), and a single function that takes as parameters the current state and the recieved event to process.  Using the convention
in the provided examples, this function is called ```event_process()``` and takes as parameters the current state and the most recently received event,
and returns the value of the state transitioned to in response to processing that event.  At its bare minimum, after everything is initialized, the
remainder of the running program executes *only* a loop similar to the following:
```
state = STATE_START
while True:
  event = eventer.next()
  state = event_process(state, event)
```

Because this basic loop is the same for every program, the eventer has an ```Eventer.loop()``` method that can be called instead of providing
one```Eventer.loop(event_process, STATE_START)``` which replaces it with just this one statement.

Later we will walk-through a full, but bare-bones, example of the obligatory *Blink* program.

# The role of the eventoids
Eventoids are the modules that monitor the state of the conditions for which events are generated at the appropriate time.  A simple eventoid might
only generate rising-edge GPIO events, or after a pre-determined period of time has elapsed.  A complex eventoid could watch for patterns of data combined
from a variety of conditions or inputs.

Some evenoids may have both a polled and an interrupting version providing the same functionality, one of which may make more sense in a
project or MCU than another.

If any eventoids require polling it is performed by the Eventer on just those eventoids, alleviating the main program from these chores.
This requires the eventer to cycle through such eventoids with some application-specific frequency so as to not miss generating events as conditions change.
How this happens can be in one of three ways:
- the main program can explicitly cause this to happen, at least as often is required and/or convenient, by calling ```Eventer.poll()```
- the main program can set an alarm callback to call ```Eventer.poll()``` at the required minimum frequency
- the eventer can poll (possibly in a very tight loop) independently in a separate thread and/or on a separate core as is available on the RP2040.

Eventoids that are fully interrupt-driven do not require polling (by definition) and run autonomously as far as both the main program and the eventer
are concerned.  They typically queue their generated events from their (sometimes virtual) interrupt handlers.

In either a polled or non-polled/interrupt-driven eventoid, when conditions warrant generating an event for consumption, it is passed to the eventer
with ```Eventer.add()```.  The Eventer is the single point of contact by the main program for all event types, making event receipt simple for the main
program.  The eventer keeps the backlog of events in a list for retrieval by the main program by calling ```Eventer.next()```.


