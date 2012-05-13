from tornado import gen

from redistest import RedisTestCase, async_test


class PubSubTestCase(RedisTestCase):

    def setUp(self):
        super(PubSubTestCase, self).setUp()
        self._message_count = 0
        self.publisher = self._new_client()

    def tearDown(self):
        try:
            self.publisher.connection.disconnect()
            del self.publisher
        except AttributeError:
            pass
        super(PubSubTestCase, self).tearDown()

    def _expect_messages(self, messages):
        self._expected_messages = messages

    def _handle_message(self, msg):
        self._message_count += 1
        self.assertIn(msg.kind, self._expected_messages)
        expected = self._expected_messages[msg.kind]
        self.assertEqual(msg.channel, expected[0])
        self.assertEqual(msg.body, expected[1])

    @async_test
    @gen.engine
    def test_pub_sub(self):
        self._expect_messages({'subscribe': ('foo', 1),
                               'message': ('foo', 'bar'),
                               'unsubscribe': ('foo', 0)})

        yield gen.Task(self.client.subscribe, 'foo')
        self.client.listen(self._handle_message)
        yield gen.Task(self.publisher.publish, 'foo', 'bar')
        yield gen.Task(self.client.unsubscribe, 'foo')

        self.assertEqual(self._message_count, 3)
        self.stop()

    @async_test
    @gen.engine
    def test_pub_psub(self):
        self._expect_messages({'psubscribe': ('foo.*', 1),
                               'pmessage': ('foo.*', 'bar'),
                               'punsubscribe': ('foo.*', 0),
                               'unsubscribe': ('foo.*', 1)})

        yield gen.Task(self.client.psubscribe, 'foo.*')
        self.client.listen(self._handle_message)
        yield gen.Task(self.publisher.publish, 'foo.1', 'bar')
        yield gen.Task(self.publisher.publish, 'bar.1', 'zar')
        yield gen.Task(self.client.punsubscribe, 'foo.*')

        self.assertEqual(self._message_count, 3)
        self.stop()
