import json
import queue
import logging
from typing import Iterable, Tuple

import pika
from pika import spec

from ..entities import MessageBrokerConfigSchema
from .message_schema import ProcessingResult, ProcessingStatus


class Consumer:
    def __init__(self,
                 config: MessageBrokerConfigSchema,
                 input_queue: queue.Queue,
                 output_queue: queue.Queue):
        credentials = pika.PlainCredentials(
            config.user, config.passwd, erase_on_connect=True)
        self._connection_params = pika.ConnectionParameters(
            host=config.host, port=config.port, 
            credentials=credentials, heartbeat=config.heartbeat)

        self._config = config
        self._connection = None
        self._channel = None
        self._consume_queue = config.input_queue
        self._logger = logging.getLogger("consumer")
        self._input_queue = input_queue
        self._output_queue = output_queue

    def _set_connection(self):
        self._connection = pika.BlockingConnection(
            parameters=self._connection_params)
        self._channel = self._connection.channel()
        self._channel.queue_declare(
            self._consume_queue, durable=self._config.input_durable)

    def _get_message(self) -> Iterable[Tuple[spec.Basic.Deliver, spec.BasicProperties, str]]:
        for method_frame, properties, body in self._channel.consume(self._consume_queue,
                                                                    inactivity_timeout=None,
                                                                    auto_ack=self._config.auto_ack,
                                                                    ):
            yield method_frame, properties, body

    def _process_message(self, method_frame, properties, body) -> ProcessingResult:
        try:
            json_message = json.loads(body)
        except ValueError:
            self._logger.exception("Cannot decode the input json message.")

        self._output_queue.put(json_message, block=True)

        while True:
            try:
                result: ProcessingResult = self._input_queue.get_nowait()
            except queue.Empty:
                self._connection.sleep(self._config.sleep_timeout_in_sec)
            else:
                break

        return result

    def _process_success(self, result: ProcessingResult, method_frame):
        self._logger.info("Successfully process object")
        if not self._config.auto_ack:
            self._channel.basic_ack(method_frame.delivery_tag)

    def _process_fail(self, result, method_frame, requeue: bool):
        self._channel.basic_nack(method_frame.delivery_tag, requeue=requeue)

    def start_consuming(self):
        if self._connection is None:
            self._set_connection()

        try:
            for method_frame, properties, body in self._get_message():
                if method_frame is None:
                    self._logger.info("Wait message")
                    continue

                self._logger.info("Got message")
                result = self._process_message(method_frame, properties, body)

                if result.status == ProcessingStatus.SUCCESS:
                    self._process_success(result, method_frame)
                
                else:
                    self._process_fail(
                        result, method_frame, 
                            requeue = result.status == ProcessingStatus.FAIL_NEED_REQUEUE)
        except Exception:
            self._logger.exception(
                "Unexpected runtime error. Shutdown consumer")
        finally:
            _ = self._channel.cancel()
            self._channel.close()
            self._connection.close()
