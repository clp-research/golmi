# TODO: update these for socketio

def selftest(): 
	with app.test_client() as c:
		# --- attaching and detaching views --- #
		dummy_view = "127.0.0.1:666"
		rv = c.post("/attach-view", data=json.dumps({"url":dummy_view}))
		assert rv.status == "200 OK" and dummy_view in model.views
		# delete view again or there view be errors in the following tests
		# when the model tries to notify the dummy view
		c.delete("/attach-view", data=json.dumps({"url":dummy_view}))
		assert dummy_view not in model.views

		# --- loading a state --- #
		f = open("resources/state/pento_test2.json", mode="r", encoding="utf-8")
		json_state = f.read()
		f.close()
		rv_state = c.post("/state", data=json_state)
		test_state = json.loads(json_state)

		# --- gripper position --- #
		rv2 = c.get("/gripper")
		gripper = rv2.get_json()
		assert float(gripper["1"]["x"]) == float(test_state["grippers"]["1"]["x"]) and \
			float(gripper["1"]["y"]) == float(test_state["grippers"]["1"]["y"]), "Grippers should be at the same location: {} vs {}".format(gripper["1"], test_state["grippers"]["1"])
		# move gripper once with default step size
		rv_move_gripper = c.post("/gripper/position", data=json.dumps({"id":"1", "dx":3, "dy":0}))
		assert rv_move_gripper.status == "200 OK"
		assert model.get_gripper_coords("1")[0] > gripper["1"]["x"] and \
			model.get_gripper_coords("1")[1] == gripper["1"]["y"]
		# move gripper with custom step size
		rv_move_gripper2 = c.post("/gripper/position", data=json.dumps({"id":"1", "dx":0, "dy":3, "step_size":1, "loop": True}))
		assert rv_move_gripper2.status == "200 OK"
		assert float(model.get_gripper_coords("1")[1]) == float(gripper["1"]["y"] + 3)
		# stop moving the gripper
		rv_stop_gripper = c.delete("/gripper/position", data=json.dumps({"id": "1"}))
		assert rv_stop_gripper.status == "200 OK"

		# --- rotating the gripped object --- #
		rv_rotate = c.post("/gripper/rotate", data=json.dumps({"id": "1", "direction": 1, "step_size": 45, "loop": True}))
		# even if no object is gripped, should return OK
		assert rv_rotate.status == "200 OK"
		rv_stop_rotate = c.delete("/gripper/rotate", data=json.dumps({"id": "1"}))
		assert rv_rotate.status == "200 OK"

		# --- flipping the gripped object --- # 
		# flip once
		rv_flip = c.post("/gripper/flip", data=json.dumps({"id": "1"}))
		assert rv_flip.status == "200 OK"

		# --- gripping --- #
		rv4 = c.get("/gripper/grip")
		# both data structures show no object gripped or same object is gripped
		if "gripped" not in test_state["grippers"]["1"] or test_state["grippers"]["1"]["gripped"] == None:
			assert "1" not in rv4.get_json() or rv4.get_json()["1"] == None or len(rv4.get_json()["1"]) == 0, \
				"test state gripper '1' has no object gripped but model seems to have one: {}".format(rv4.get_json()["1"]) 
		else:
			assert test_state["grippers"]["1"]["gripped"] in rv4.get_json()["1"].keys(), \
				"test state gripper '1' and model gripper '1' do not have the same object gripped: {} vs {}".format(test_state["grippers"]["1"]["gripped"], rv4.get_json()["1"].keys())

		# bad request: missing gripper id
		rv5_bad_request = c.post("/gripper/grip")
		# valid request
		assert rv5_bad_request.status == "400 BAD REQUEST"
		rv5_start_gripping = c.post("/gripper/grip", data=json.dumps({"id":"1"}))
		assert rv5_start_gripping.status == "200 OK"

		# stop gripping
		rv5_stop_gripping = c.delete("/gripper/grip", data=json.dumps({"id":"1"}))
		assert rv5_stop_gripping.status == "200 OK"

		# --- objects --- #
		rv6 = c.get("/objects")
		assert rv6.get_json().keys() == test_state["objs"].keys()

		# --- deleting the state --- #
		rv_reset = c.delete("/state")
		assert rv_reset.status == "200 OK" and len(model.get_object_dict()) == 0