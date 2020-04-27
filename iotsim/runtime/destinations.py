"""
This module defines where your  assembly can send its data.

Write a destination class to implement your destination.
The class must define three methods:
`__init__(**kwargs)`, `send(message)`, `shutdown()`

Then add your destination to `known_destinations` dictionary.

`known_destinations` is what is imported into `run_assembly` script.
Keys are labels that identify the destinations in script's config.
Values are tuples (destination_class, kwargs_dict).
Script's config can supply additional parameters or override these kwargs.
The destination will be instantiated as
``destination_class(kwargs_dict.update(parameters_from_script_config))``

"""

import sys


class StandardDestination:

    def __init__(self, output):
        output = output.lower()
        if output == 'stdout':
            self.file = sys.stdout
        elif output == 'stderr':
            self.file = sys.stderr
        else:
            raise ValueError("Unrecognized output {!r}".format(output))

    def send(self, message):
        print(message, file=self.file)

    def shutdown(self):
        pass


class KinesisDestination:

    def __init__(self, stream):
        from boto3 import client as boto3_client
        self.kinesis_client = boto3_client('kinesis')
        self.stream = str(stream)
        self.partitiion_key = 'dummy'

    def send(self, message):
        response = self.kinesis_client.put_record(
            StreamName=self.stream,
            Data=message,
            PartitionKey=self.partitiion_key)

    def shutdown(self):
        pass


class PubSubDestination:

    def __init__(self, project_id, topic_name):
        from google.cloud import pubsub_v1
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_name)
        self._sent_counter = 0
        self._published_counter = 0

    def send(self, message):

        def callback(future):
            self._published_counter += 1

        message = message.encode('utf-8')
        self._sent_counter += 1
        message_future = self.publisher.publish(self.topic_path, data=message)
        message_future.add_done_callback(callback)

    def shutdown(self):
        print(
            "Published: {}, lost: {}".format(
                self._published_counter,
                self._sent_counter - self._published_counter),
            file=sys.stderr
        )

known_destinations = {
    'stdout': (StandardDestination, {'output': 'stdout'}),
    'stderr': (StandardDestination, {'output': 'stderr'}),
    'kinesis': (KinesisDestination, {}),
    'pubsub': (PubSubDestination, {}),
}
