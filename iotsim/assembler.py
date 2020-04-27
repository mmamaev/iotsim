import iotsim.readers as readers
import iotsim.networks as networks
import iotsim.constructors as contructors

import yaml


_inventory = dict(

    assembly=dict(
        Flatline=contructors.Flatline,
        Seasaw=contructors.Seesaw,
        Pulser=contructors.Pulser,
        SimpleActuator=contructors.SimpleActuator,
    ),

    reader=dict(
        PassThrough=readers.PassthroughReader,
        EveryNth=readers.EveryNthReader,
        OnChange=readers.OnChangeReader,
    ),

    network = dict(
        Ideal = networks.IdealNetwork,
        Normal = networks.NormalNetwork,
    ),
)

def inventory(component, component_type):
    try:
        component_inventory = _inventory[component]
    except KeyError:
        raise ValueError("Illegal assembly component: {}".format(component))
    try:
        component_class = component_inventory[component_type]
    except KeyError:
        raise  ValueError("{} type `{}` is not listed in the inventory".
                          format(component, component_type))
    return component_class


def from_config(config):
    try:
        config.items()
    except AttributeError:
        with open(str(config), 'r') as f:
            config = yaml.load(f, Loader=yaml.SafeLoader)

    return _from_config(config)

def _from_config(config):

    try:
        config.items()
    except:
        raise TypeError("Consfis must be a disctionary. Got {}".format(type(config)))
    if not 'assembly' in config:
        raise KeyError("Config is missing mandatory key 'assembly'")
    if not 'type' in config['assembly']:
        raise KeyError("Assembly definition is missing mandatory key 'type'")

    constructor = inventory('assembly', config['assembly']['type'])
    assembly_params = config['assembly'].get('parameters', dict())
    assembly_template = constructor(**assembly_params)

    readers_definitions = config.get('readers', list())
    readers = dict()
    for reader_definition in readers_definitions:
        try:
            reader_type = reader_definition.pop('type')
        except KeyError:
            raise KeyError("Reader definition is missing mandatory key 'type'")
        try:
            reader_label = reader_definition.pop('label')
        except KeyError:
            raise KeyError("Reader definition is missing mandatory key 'label'")
        reader_parameters = reader_definition.get('parameters', dict())
        reader_class = inventory('reader', reader_type)
        readers[reader_label] = reader_class(**reader_parameters)

    assembly_readers = config['assembly'].get('readers', dict())
    for signal_name, reader_label in assembly_readers.items():
        try:
            reader =  readers[reader_label]
        except KeyError:
            raise KeyError("Undefined reader label '{}' in aseembly definition".
                           format(reader_label))
        if signal_name == 'default':
            assembly_template.attach_reader(reader)
        else:
            assembly_template.attach_reader(reader, signal_name)

    networks_definitions = config.get('networks', list())
    networks = dict()
    for network_definition in networks_definitions:
        try:
            network_type = network_definition.pop('type')
        except KeyError:
            raise KeyError("network definition is missing mandatory key 'type'")
        try:
            network_label = network_definition.pop('label')
        except KeyError:
            raise KeyError("network definition is missing mandatory key 'label'")
        network_parameters = network_definition.get('parameters', dict())
        network_class = inventory('network', network_type)
        networks[network_label] = network_class(**network_parameters)

    assembly_networks = config['assembly'].get('networks', dict())
    for signal_name, network_label in assembly_networks.items():
        try:
            network =  networks[network_label]
        except KeyError:
            raise KeyError("Undefined network label '{}' in aseembly definition".
                           format(network_label))
        if signal_name == 'default':
            assembly_template.attach_network(network)
        else:
            assembly_template.attach_network(network, signal_name)

    assembly = assembly_template()
    return assembly
