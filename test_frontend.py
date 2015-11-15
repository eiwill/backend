import frontend
import unittest
import json
import redis

from flexmock import flexmock

class FrontEndTestCase(unittest.TestCase):

    def setUp(self):
        frontend.app.config['TESTING'] = True
        self.app = frontend.app.test_client()

    def tearDown(self):
        pass

    def test_task_put(self):
        flexmock(frontend)\
            .should_call("get_redis")\
            .times(1)

        rv = self.app.put("/task", data=json.dumps(dict(type="message")), headers={"Content-Type":"application/json"})
        data = json.loads(rv.data)
        self.assertEqual(rv.status_code, 200)
        self.check_task_response(data)

    def test_incorrect_content_type(self):
        rv = self.app.put("/task", data=json.dumps(dict(type="message")))
        self.assertEqual(rv.status_code, 406)

    def test_task_get(self):
        rv = self.app.put("/task", data=json.dumps(dict(type="message")), headers={"Content-Type":"application/json"})
        data = json.loads(rv.data)
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get("/task/%s" % data["id"])
        data = json.loads(rv.data)
        self.assertEqual(rv.status_code, 200)

        self.check_task_response(data, "execute_time")

    def test_task_put_bad_json(self):
        rv = self.app.put("/task", data="12345", headers={"Content-Type":"application/json"})
        self.assertEqual(rv.status_code, 400)

    def test_task_get_not_found(self):
        rv = self.app.get("/task/1234")
        self.assertEqual(rv.status_code, 404)

    def check_task_response(self, task, *additional_fields):
        keys = ["id", "time_start", "time_end"]
        keys.extend(additional_fields)
        for key in keys:
            self.assertTrue(key in task)               
        self.assertEqual(task["type"], "message")


if __name__ == '__main__':
    unittest.main()