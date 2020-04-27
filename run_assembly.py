import argparse, sys, json, yaml

import pandas as pd
import asyncio

from iotsim.utils import to_iterable
from iotsim.runtime.destinations import known_destinations
from iotsim.assembler import from_config


if __name__ != '__main__':
    sys.exit("This program must be run as a standalone script")

parser = argparse.ArgumentParser(description='Assembly runner')
parser.add_argument('assembly_config_filename',
                    help="Name of YAML config file for the assembly.")
parser.add_argument('-c', '--config', metavar='runner_config_filename',
                    help='Name of YAML config file for the runner.')
parser.add_argument('-t', '--ticks', metavar='ticks', type=int,
                    help='Number of time ticks to go, int >=0. '
                         'Zero means infinite run.')
parser.add_argument('-p', '--pace', metavar='pace', type=float,
                    help="Factor to speed up (>1) or slow down (<1) the assembly.")
parser.add_argument('-b', '--start-time', metavar='start_time',
                    help="Start time for the run. The default is 'now'.")
parser.add_argument('-d', '--start-delta', metavar='start_delta',
                    help="Seconds added to the local machine's time to compensate "
                          "clock skew at destination. May be negative. The default is 0.")

defaults=dict(
    ticks=0,
    message_format='json',
    start_time='now',
    start_delta=2,
    pace=1,
    routing={'reading': ['stdout'], 'truth': ['stdout']},
    destinations=dict(),
)

def get_param_value(param):
    global defaults, args, config
    if hasattr(args, param) and getattr(args, param) is not None:
        return getattr(args, param)
    else:
        return config.get(param, defaults.get(param, None))

### Parse config file and command line arguments

args = parser.parse_args()

config = dict()
if args.config is not None:
    with open(str(args.config), 'r') as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)
# else:
#     config=dict(timing=dict(),
#                 signals=[],
#                 destinations=dict(),
#                 routing=defaults['routing'])

assembly_name = get_param_value('name')
message_format = get_param_value('message_format')
ticks = get_param_value('ticks')
if ticks == 0:
    ticks = None
tick_counter = ticks
pace = get_param_value('pace')

start_time = get_param_value('start_time')
start_delta = get_param_value('start_delta')
start_time = pd.Timestamp(start_time) + pd.Timedelta(start_delta, unit='s')

signal_label = 'signal'
value_label = 'value'
event_time_label = 'event_time'
arrival_time_label = 'arrival_time'
meta_label = 'meta'

#### Create an assembly

assembly = from_config(args.assembly_config_filename)
if assembly_name is None:
    assembly_name = 'assembly' if assembly.name is None else assembly.name
tick_duration = pd.Timedelta(assembly.tick, unit='s')
assembly_runner = assembly.launch()

### Set up destinations

active_destinations = dict()
destination_routing = dict(reading=[], truth=[])
configured_routing = get_param_value('routing')
configured_destinations = get_param_value('destinations')
for dataview in destination_routing.keys():
    routing = to_iterable(configured_routing[dataview])
    for destination in routing:
        if destination not in active_destinations:
            if destination in configured_destinations:
                cls, kwargs = known_destinations[
                    configured_destinations[destination]['type']]
            else:
                cls, kwargs = known_destinations[destination]
            try:
                additional_params = configured_destinations[destination]['parameters']
            except KeyError:
                pass
            else:
                kwargs.update(additional_params)
            handler = cls(**kwargs)
            active_destinations[destination] = handler
        else:
            handler = active_destinations[destination]
        destination_routing[dataview].append(handler)

### Define the real-time flow of the messages

# assembly_snapshot.readings -> list [ named_tuple (signal_name, value, arrived=True, arrival_delay)]
# assembly_snapshot.all_readings -> include lost readings (arrived==False)
#
# example:
# assembly_snapshot.readings[0].value
#
# aseembly_state.truths -> list [ named_tuple (signal_name, value)]
#
# assembly_snapshot.signal(signal_name) -> named_tuple (truth, reading)
#     truth: named_tuple (signal_name, value)
#     reading: None or named_tuple (signal_name, value, arrived, arrival_delay)
#
# example:
# assembly_snapshot.signal('control').reading.value

async def deliver_datapoint(datapoint, dataview, delivery_time, event_time,
                            arrival_time=None):

    message_data = {
        meta_label: "{}:{}".format(assembly_name, dataview),
        signal_label: datapoint.signal_name,
        value_label: datapoint.value,
        event_time_label: str(event_time),
    }
    if dataview == 'reading':
        message_data[arrival_time_label] = str(arrival_time)

    message = json.dumps(message_data)
    wait_until_delivery =  (delivery_time - pd.Timestamp('now')).total_seconds()
    await asyncio.sleep(wait_until_delivery)
    if wait_until_delivery < 0:
        raise RuntimeError("System fell behind assembly's schedule")

    for destination_handler in destination_routing[dataview]:
        destination_handler.send(message)


async def main():

    global tick_counter
    latest_delivery_time = pd.Timestamp('now')
    event_time=start_time
    for asm_snapshot in assembly_runner:
        next_tick_at = pd.Timestamp('now') + pd.Timedelta(tick_duration / pace, unit='s')
        event_time = event_time + tick_duration

        for reading in asm_snapshot.readings:
            if reading.value is None or not reading.arrived:
                continue
            arrival_time = event_time + pd.Timedelta(reading.arrival_delay, unit='s')
            delivery_time = next_tick_at + pd.Timedelta(reading.arrival_delay / pace, unit='s')
            asyncio.ensure_future(deliver_datapoint(
                reading, 'reading', delivery_time, event_time, arrival_time))
            if delivery_time > latest_delivery_time:
                latest_delivery_time = delivery_time

        for truth in asm_snapshot.truths:
            asyncio.ensure_future(deliver_datapoint(
                truth, 'truth', next_tick_at, event_time))
            if next_tick_at > latest_delivery_time:
                latest_delivery_time = next_tick_at


        if not tick_counter is None:
            if tick_counter == 0:
                break
            tick_counter -= 1

        wait_until_next_tick = (next_tick_at - pd.Timestamp('now')).total_seconds()
        await asyncio.sleep(wait_until_next_tick)
        if wait_until_next_tick < 0:
            raise RuntimeError("Pace is too fast. System fell behind.")

    await asyncio.sleep(
        (latest_delivery_time - pd.Timestamp('now')).total_seconds() + 1
    )

    if not tick_counter is None and tick_counter > 0:
        sys.exit("Assembly ran out after {} ticks whish is less than required {}".
                 format(ticks - tick_counter, ticks))

### Run

loop = asyncio.get_event_loop()
task = loop.create_task(main())
loop.run_until_complete(task)

