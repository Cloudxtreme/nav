from unittest import TestCase

from nav.models import manage
from nav.tests.cases import DjangoTransactionTestCase
from nav.bulkimport import *
from nav.bulkparse import *

class TestGenericBulkImport(TestCase):
    def test_is_generator(self):
        importer = BulkImporter(None)
        self.assertTrue(hasattr(importer, 'next'))
        self.assertTrue(callable(getattr(importer, 'next')))
        self.assertTrue(iter(importer) == importer)


class TestNetboxImporter(DjangoTransactionTestCase):
    def test_simple_import_yields_netbox_and_device_model(self):
        data = 'myroom:10.0.90.252:myorg:SW:public:MOOSE123::'
        parser = NetboxBulkParser(data)
        importer = NetboxImporter(parser)
        line_num, objects = importer.next()

        self.assertTrue(isinstance(objects, list), repr(objects))
        self.assertTrue(len(objects) == 2, repr(objects))
        self.assertTrue(isinstance(objects[0], manage.Device), objects[0])
        self.assertTrue(isinstance(objects[1], manage.Netbox), objects[0])

    def test_simple_import_yields_objects_with_proper_values(self):
        data = 'myroom:10.0.90.252:myorg:SW:public:MOOSE123::'
        parser = NetboxBulkParser(data)
        importer = NetboxImporter(parser)
        line_num, objects = importer.next()

        (device, netbox) = objects
        self.assertTrue(netbox.device is device)
        self.assertEquals(device.serial, 'MOOSE123')
        self.assertEquals(netbox.ip, '10.0.90.252')
        self.assertEquals(netbox.room_id, 'myroom')
        self.assertEquals(netbox.organization_id, 'myorg')
        self.assertEquals(netbox.category_id, 'SW')
        self.assertEquals(netbox.read_only, 'public')

    def test_invalid_room_gives_error(self):
        data = 'invalid:10.0.90.252:myorg:SW:public:MOOSE123::'
        parser = NetboxBulkParser(data)
        importer = NetboxImporter(parser)
        line_num, objects = importer.next()
        self.assertTrue(isinstance(objects, DoesNotExist))

    def test_netbox_function_is_set(self):
        data = 'myroom:10.0.90.252:myorg:SW:public:MOOSE123::does things:'
        parser = NetboxBulkParser(data)
        importer = NetboxImporter(parser)
        line_num, objects = importer.next()

        types = dict((type(c), c) for c in objects)
        self.assertTrue(manage.NetboxInfo in types, types)

    def test_get_netboxinfo_from_function(self):
        importer = NetboxImporter(None)
        netbox = manage.Netbox()
        netboxinfo = importer._get_netboxinfo_from_function(netbox, 'hella')
        self.assertTrue(isinstance(netboxinfo, manage.NetboxInfo))
        self.assertTrue(netboxinfo.key is None)
        self.assertEquals(netboxinfo.variable, 'function')
        self.assertEquals(netboxinfo.value, 'hella')

    def test_netbox_groups_are_set(self):
        data = 'myroom:10.0.90.10:myorg:SRV::MOOSE123::fileserver:WEB:UNIX:MAIL'
        parser = NetboxBulkParser(data)
        importer = NetboxImporter(parser)
        line_num, objects = importer.next()

        netboxgroups = [o for o in objects
                        if isinstance(o, manage.NetboxCategory)]
        self.assertTrue(len(netboxgroups) > 0, objects)

    def test_get_groups_from_group(self):
        importer = NetboxImporter(None)
        netbox = manage.Netbox()
        netbox.category = manage.Category.objects.get(id='SRV')

        netboxgroups = ['LDAP', 'UNIX']
        ncategories = importer._get_groups_from_group(netbox, netboxgroups)
        self.assertTrue(len(ncategories) == 2)

        for netboxgroup, ncategory in zip(netboxgroups, ncategories):
            self.assertTrue(isinstance(ncategory, manage.NetboxCategory),
                            ncategory)
            self.assertEquals(ncategory.category_id, netboxgroup)

    def test_duplicate_locations_should_give_error(self):
        netbox = manage.Netbox(
            sysname='10.1.0.1', ip='10.1.0.1',
            device=manage.Device.objects.get_or_create(serial='MOOSE42')[0],
            room=manage.Room.objects.get(id='myroom'),
            category=manage.Category.objects.get(id='SRV'),
            organization=manage.Organization.objects.get(id='myorg'),
            snmp_version=1)
        netbox.save()

        data = 'myroom:10.1.0.1:myorg:SRV::MOOSE42::fileserver:WEB:UNIX:MAIL'
        parser = NetboxBulkParser(data)
        importer = NetboxImporter(parser)
        line_num, objects = importer.next()

        self.assertTrue(isinstance(objects, AlreadyExists))

    def test_created_objects_can_be_saved(self):
        data = 'myroom:10.0.90.10:myorg:SRV::MOOSE123::fileserver:WEB:UNIX:MAIL'
        parser = NetboxBulkParser(data)
        importer = NetboxImporter(parser)
        line_num, objects = importer.next()

        for obj in objects:
            reset_object_foreignkeys(obj)
            print repr(obj)
            obj.save()

class TestLocationImporter(DjangoTransactionTestCase):
    def test_import(self):
        data = "somewhere:Over the rainbow"
        parser = LocationBulkParser(data)
        importer = LocationImporter(parser)
        line_num, objects = importer.next()

        self.assertTrue(len(objects) == 1, repr(objects))
        self.assertTrue(isinstance(objects[0], manage.Location))
        self.assertEquals(objects[0].id, 'somewhere')

    def test_imported_objects_can_be_saved(self):
        data = "somewhere:Over the rainbow"
        parser = LocationBulkParser(data)
        importer = LocationImporter(parser)
        line_num, objects = importer.next()

        for obj in objects:
            reset_object_foreignkeys(obj)
            print repr(obj)
            obj.save()

    def test_duplicate_locations_should_give_error(self):
        l = manage.Location.objects.get_or_create(
            id='somewhere', description='original somewhere')

        data = "somewhere:Over the rainbow"
        parser = LocationBulkParser(data)
        importer = LocationImporter(parser)
        line_num, objects = importer.next()

        self.assertTrue(isinstance(objects, AlreadyExists))

class TestPrefixImporter(DjangoTransactionTestCase):
    def setUp(self):
        org, created = Organization.objects.get_or_create(id='uninett')
        org.save()

        usage, created = Usage.objects.get_or_create(id='employee')
        usage.save()

    def test_import(self):
        data = "10.0.1.0/24:lan:uninett:here-there:employee:Employee LAN:20"
        parser = PrefixBulkParser(data)
        importer = PrefixImporter(parser)
        line_num, objects = importer.next()

        if isinstance(objects, Exception):
            raise objects
        self.assertEquals(len(objects), 2)
        self.assertTrue(isinstance(objects[0], Vlan))
        self.assertTrue(isinstance(objects[1], Prefix))
