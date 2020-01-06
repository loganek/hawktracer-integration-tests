import glob
import json
import logging
import os
import subprocess
import time
import traceback

from enum import Enum
from typing import NamedTuple


logging.basicConfig(filename='logs.txt', level=logging.INFO, filemode='w')

class TestResult(NamedTuple):
    status: str
    name: str
    fail_reason: Exception


class TransportType(Enum):
    TCP = 'tcp'
    FILE = 'file'


class ReferenceAssert:
    def __init__(self, expected, actual):
        self._expected = expected
        self._actual = actual

    def assert_all(self):
        self.compare_event_count()

    def compare_event_count(self):
        actual = ReferenceAssert._event_map_by_type(self._actual)
        expected = ReferenceAssert._event_map_by_type(self._expected)
        if actual != expected:
            raise Exception(f'Event types do not match. actual: {actual}, expected: {expected}')

    @staticmethod
    def _event_map_by_type(events):
        data = {}
        for event in events:
            data[event['meta_klass_name']] = data.get(event['meta_klass_name'], 0) + 1
        return data

class NoReferenceAssert:
    def __init__(self, events):
        self._events = events

    def assert_all(self):
        self.assert_mapping_from_events()
        self.assert_timestamps_should_grow_for_callstack_events()

    def assert_mapping_from_events(self):
        mapping = self._get_mapping_from_mapping_events()
        for event in self._filter_by_types(['HT_CallstackIntEvent']):
            int_value = event['label']['value']
            if int_value not in mapping and 'maps_to' in event['label']:
                raise Exception(f'Unexpected mapping ocurred for event {event}')
            if mapping[int_value] != event['label']['maps_to']:
                raise Exception(f'Mapping does not match for event {event}')

    def assert_timestamps_should_grow_for_callstack_events(self):
        events = self._filter_by_types(['HT_CallstackIntEvent', 'HT_CallstackStringEvent'])
        events = sorted(events, key=lambda x: (x['timestamp']['value'], -x['duration']['value']))

        for i in range(1, len(events)):
            if events[i-1]['id']['value'] > events[i]['id']['value']:
                raise Exception(f'Invalid callstack event order. Previous: {events[i-1]}, next: {events[i]}')

    def _get_mapping_from_mapping_events(self):
        data = {}
        for event in self._filter_by_types(['HT_StringMappingEvent']):
            data[event['identifier']['value']] = event['label']['value']
        return data

    def _filter_by_types(self, event_types):
        return filter(lambda e: e['meta_klass_name'] in event_types, self._events)


class TestRunner:
    FILE_PATH_TEMPLATE = 'output_{}.htdump'
    PORT = '8798'
    CONVERTER_PATH = './bin/hawktracer-converter-rs'

    def __init__(self, test_name: str, test_path: str, transport_type: TransportType):
        self._test_path = test_path
        self._transport_type = transport_type
        self._test_name = test_name
        self._configure_source_params()

    def run(self):
        if self._transport_type == TransportType.FILE:
            self._run_test_executable()
            result = self._finish_converter(self._run_converter())
        else:
            handle = self._run_converter()
            self._run_test_executable()
            result = self._finish_converter(handle)
        return self._debug_result_to_json(result.decode('utf-8'))

    def _debug_result_to_json(self, result: str):
        # remove last character (,) and add '[]' as hawktracer converter
        # doesn't generate exactly valid JSON. This can be fixed in the future
        logging.info('Converting results to JSON')
        return json.loads('[' + result.strip()[:-1] + ']')

    def _run_test_executable(self):
        parameters = [self._test_path] + self._test_params
        logging.info(f'Running test program {self._test_path} with parameters {parameters}')
        cpi = subprocess.run(parameters, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f'Test program finished')
        try:
            cpi.check_returncode()
        except Exception as error:
            logging.error(f'Test program did not complete successfully. Error: {str(error)}')
            raise

    def _finish_converter(self, handle: subprocess.Popen):
        try:
            out, err = handle.communicate(timeout=10)
            logging.info('Converter completed execution')
            logging.debug(f'STDOUT:\n{out}')
            logging.info(f'STDERR:\n{err}')
            return out
        except:
            handle.kill()
            raise

    def _run_converter(self):
        parameters = [self.CONVERTER_PATH, '--stdout', '--format', 'json_debug'] + self._converter_params
        logging.info(f'Starting converter with parameters: {parameters}')
        handle = subprocess.Popen(parameters, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if self._transport_type == TransportType.TCP:
            logging.info('Waiting for the converter to be ready...')
            time.sleep(0.5)
            logging.info('Converter ready, start test program')

        return handle

    def _configure_source_params(self):
        if self._transport_type == TransportType.FILE:
            file_path = self.FILE_PATH_TEMPLATE.format(self._test_name)
            self._test_params = ['--file', file_path]
            self._converter_params = ['-s', file_path]
        elif self._transport_type == TransportType.TCP:
            self._test_params = ['--port', self.PORT]
            self._converter_params = ['-s', f'127.0.0.1:{self.PORT}']
        else:
            raise Exception(f'Invalid transport type: {self._transport_type}')


class TestExecutor:
    def __init__(self):
        self._test_results = {}

    def execute(self, test_path: str, transport_type: TransportType):
        test_name = os.path.basename(test_path)[5:]
        fail_reason = None
        try:
            result = TestRunner(test_name, test_path, transport_type).run()
            ReferenceAssert(self._load_expected_result(test_name), result).assert_all()
            NoReferenceAssert(result).assert_all()
            status = 'pass'
        except Exception as error:
            status = 'fail'
            fail_reason = error
            logging.error(f'Test {test_name} failed. Reason:\n{str(error)}')
            logging.error(traceback.format_exc())

        name = test_name + '.' + transport_type.value
        print(f'Completed {name}: {status}')
        self._test_results[name] = TestResult(status, name, fail_reason)

    def _load_expected_result(self, test_name):
        with open(f'../snapshots/{test_name}.json') as json_file:
            return json.load(json_file)

    def print_report(self):
        print('--------------')
        print(f'Executed {len(self._test_results)} tests')
        pass_count = len(list(filter(lambda x: x[1].status == 'pass', self._test_results.items())))
        print(f'Failed: {len(self._test_results) - pass_count}')
        print(f'Passed: {pass_count}')

def main():
    executor = TestExecutor()

    for test_path in glob.glob('./bin/test_*'):
        executor.execute(test_path, TransportType.FILE)
        executor.execute(test_path, TransportType.TCP)

    executor.print_report()


if __name__ == '__main__':
    main()
