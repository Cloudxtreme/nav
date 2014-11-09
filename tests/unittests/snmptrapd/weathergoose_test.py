from unittest import TestCase
from mock import patch, Mock

from nav.snmptrapd.handlers import weathergoose as wg

class WeatherGooseMockedDb(TestCase):
    def setUp(self):
        self.getConnection = patch('nav.snmptrapd.handlers.weathergoose'
                                   '.getConnection')
        self.getConnection.start()

    def tearDown(self):
        self.getConnection.stop()

class WeatherGoose1ClassTest(WeatherGooseMockedDb):
    def test_should_not_handle_a_weathergoose2_trap(self):
        self.assertFalse(
            wg.WeatherGoose1.can_handle('.1.3.6.1.4.1.17373.3.32767.0.10205'))

    def test_should_handle_a_weathergoose1_trap(self):
        self.assertTrue(
            wg.WeatherGoose1.can_handle('.1.3.6.1.4.1.17373.0.10205'))

    def test_should_map_oid_to_correct_trigger(self):
        self.assertEqual(
            wg.WeatherGoose1.map_oid_to_trigger('.1.3.6.1.4.1.17373.0.10205'),
            'cmClimateTempCTRAP')

    def test_init_should_raise_on_invalid_oid(self):
        trap = Mock(snmpTrapOID = '5')
        self.assertRaises(Exception, wg.WeatherGoose1, trap, None, None, None)

class WeatherGoose1TrapTest(WeatherGooseMockedDb):
    def setUp(self):
        super(WeatherGoose1TrapTest, self).setUp()
        trap = Mock(snmpTrapOID = '.1.3.6.1.4.1.17373.0.10205')
        TRIP_TYPE_HIGH = 2
        self.goosename = 'cleese'
        self.temperature = 32
        trap.varbinds = {'.1.3.6.1.4.1.17373.2.1.6': TRIP_TYPE_HIGH,
                         '.1.3.6.1.4.1.17373.2.2.1.3.1': self.goosename,
                         '.1.3.6.1.4.1.17373.2.2.1.5.1': self.temperature}
        self.trap = trap

        import nav.event
        class Event(dict):
            def post(self):
                pass

        self.event = patch('nav.event.Event', side_effect=Event)
        self.event.start()

    def tearDown(self):
        super(WeatherGoose1TrapTest, self).tearDown()
        self.event.stop()

    def test_init_should_parse_trap_without_error(self):
        self.assertTrue(wg.WeatherGoose1(self.trap, None, None, None))

    def test_should_find_correct_alert_type(self):
        goose = wg.WeatherGoose1(self.trap, None, None, None)
        self.assertEquals(goose._get_alert_type(), 'cmClimateTempCTRAP')

    def test_should_find_correct_goosename(self):
        goose = wg.WeatherGoose1(self.trap, None, None, None)
        self.assertEquals(goose.goosename, self.goosename)

    def test_should_find_climate_values(self):
        goose = wg.WeatherGoose1(self.trap, None, None, None)
        self.assertEquals(goose.climatevalue, self.temperature)

    def test_should_find_triptype_high(self):
        goose = wg.WeatherGoose1(self.trap, None, None, None)
        self.assertEquals(goose.triptype, 'High')

    def test_event_event_post(self):
        goose = wg.WeatherGoose1(self.trap, None, None, None)
        self.assertTrue(goose.post_event())

class WeatherGoose2Test(WeatherGooseMockedDb):
    def test_should_not_handle_a_weathergoose1_trap(self):
        self.assertFalse(
            wg.WeatherGoose2.can_handle('.1.3.6.1.4.1.17373.0.10205'))

    def test_should_handle_a_weathergoose2_trap(self):
        self.assertTrue(
            wg.WeatherGoose2.can_handle('.1.3.6.1.4.1.17373.3.32767.0.10205'))

    def test_should_map_oid_to_correct_trigger(self):
        self.assertEqual(
            wg.WeatherGoose2.map_oid_to_trigger(
                '.1.3.6.1.4.1.17373.3.32767.0.10205'),
            'cmClimateTempCNOTIFY')

    def test_should_find_correct_alert_type(self):
        trap = Mock('trap')
        trap.snmpTrapOID = '.1.3.6.1.4.1.17373.3.32767.0.10205'
        TRIP_TYPE_HIGH = 2
        trap.varbinds = {'.1.3.6.1.4.1.17373.3.1.6.0': TRIP_TYPE_HIGH}
        goose = wg.WeatherGoose2(trap, None, None, None)
        self.assertEquals(goose._get_alert_type(), 'cmClimateTempCTRAP')
