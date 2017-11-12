import unittest
import datetime
import os.path
from SI507project5_code import CACHE_DICTION
from SI507project5_code import *


# test cache... a new request, put cache, not new request
# event brite start session, session and token not null
# make a request return
# write data

class Proj5Test(unittest.TestCase):
    def setUp(self):
        self.event_brite_finder = EventBriteFinder()

        baseurl = "https://www.eventbriteapi.com/v3"
        self.endpt1 = baseurl + "/events/search/"
        date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=60)
        self.params1 = {
            "start_date.range_end": date.isoformat()
        }

        self.endpt2 = baseurl+"/organizers/{}/".format('10652048014')


    def testSessionSetup(self):
        self.assertFalse(self.event_brite_finder.session is None, "Session is None")
        self.assertFalse(self.event_brite_finder.token is None, "Session is None")

    def testCache(self):
        clear_cache()
        unique_ident = "start_date.range_end-2018-01-10T00:00:00"
        result = get_from_cache(unique_ident)
        print(result, "cache result")
        self.assertEqual(result, None, "Already in Cache where it shouldn't be")
        resp = "testCache resp"
        set_in_cache(unique_ident, resp)
        result = get_from_cache(unique_ident)
        self.assertTrue('testCache' in result, "Resp data not in Cache")

    def testRequest1(self):
        resp = self.event_brite_finder.make_request(self.endpt1, self.params1)
        self.assertTrue('events' in resp['resp'], "resp does not have events")

    def testRequest2(self):
        resp = self.event_brite_finder.make_request(self.endpt2)
        self.assertTrue('id' in resp['resp'], "resp does not have org id")

    def testWriteCsv(self):
        header2 = ["Org ID", "Name", "Twitter", "Facebook"]
        data2_list = [["1234", "CodeMash", "TwitterTest", "FacebookTest"]]
        self.event_brite_finder.write_data_to_csv("Organization_Info.csv", data2_list, header2)
        self.assertTrue(os.path.isfile("Organization_Info.csv"), "File not created")
        with open("Organization_Info.csv", 'r') as file:
            data = file.readlines()
            header = data[0]
            info = data[1]
            self.assertEqual(header, "Org ID,Name,Twitter,Facebook\n", "header mismatch")
            self.assertEqual(info, "1234,CodeMash,TwitterTest,FacebookTest\n", "data mismatch")

    def tearDown(self):
        pass



if __name__ == "__main__":
    unittest.main(verbosity=2)
